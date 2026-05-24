# 命令模式（Command Pattern）教程

## 一、最原始的写法

假设你在写一个 Todo 应用，要支持撤销（undo）：把添加的 Todo 删掉，把完成的状态改回去……

```python
class TodoList:
    def __init__(self):
        self.todos = []
        self._history = []  # 手动记操作历史

    def add_todo(self, title):
        todo = Todo(title)
        self.todos.append(todo)
        self._history.append(("add", todo))  # 手动记

    def undo(self):
        action, data = self._history.pop()
        if action == "add":
            self.todos.remove(data)
```

问题很明显：`undo` 和业务逻辑混在一起，每加一个新操作就要手动管理历史记录。

---

## 二、命令模式（标准写法）

把"操作"封装成对象：

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): pass
    @abstractmethod
    def undo(self): pass

@dataclass
class AddTodoCommand(Command):
    todo_list: TodoList
    title: str
    _todo: Todo = None

    def execute(self):
        self._todo = Todo(self.title)
        self.todo_list.todos.append(self._todo)

    def undo(self):
        self.todo_list.todos.remove(self._todo)
```

用命令对象来操作：

```python
cmd = AddTodoCommand(todo_list, "学 Python")
cmd.execute()
history.append(cmd)   # 存命令对象

# 撤销
history.pop().undo()
```

好处：execute/undo 配对，各自管好自己的状态。  
坏处：每个操作都要写一个类，太啰嗦了。

---

## 三、函数式版本——用闭包代替类

```python
def make_add_command(todo_list, title):
    todo = None
    def execute():
        nonlocal todo
        todo = Todo(title)
        todo_list.todos.append(todo)
    def undo():
        todo_list.todos.remove(todo)
    return execute, undo
```

比类省了几行，但还是手动配对的。

---

## 四、装饰器版本——自动推导 undo

核心观察：**undo 方法签名和原方法一样**。

如果 `add_todo(self, title)` 的 undo 是 `add_todo_undo(self, title)`，那我们能不能自动把两者配对？

这就是 `Command` 类做的事。

### 4.1 最简单的起步

```python
from functools import wraps

class SimpleCommand:
    def __init__(self, cls):
        self.cls = cls
        self.undo_stack = []
        self._wrap(cls)

    def _wrap(self, cls):
        for name in dir(cls):
            if name.startswith("_"):
                continue
            attr = getattr(cls, name)
            if callable(attr):
                setattr(cls, name, self._make_wrapper(attr, name))

    def _make_wrapper(self, func, name):
        @wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0]
            # 找对应的 undo 方法
            undo = getattr(instance, f"{name}_undo", None)
            if undo:
                self.undo_stack.append(lambda: undo(*args[1:], **kwargs))
            return func(*args, **kwargs)
        return wrapper
```

这个版本能用了，但所有实例共享一个 `undo_stack`——`list1.add("A")` 和 `list2.add("B")` 混在一起。

### 4.2 实例级隔离

解决思路：**每创建一个实例就拷贝一份 Command**。

```python
def __call__(self, *args, **kwargs):
    instance = self.cls(*args, **kwargs)
    new_cmd = copy(self)
    new_cmd.undo_stack = []
    instance._command = new_cmd   # 注入实例
    return instance
```

这样每个实例有自己的撤销栈。

`_make_wrapper` 里改成从 `instance._command` 取栈：

```python
cmd = getattr(instance, "_command", None)
if cmd and undo:
    cmd.undo_stack.append(lambda: undo(...))
```

### 4.3 异常时自动回滚

如果操作链中间炸了，已经成功的操作应该自动撤销。

```python
try:
    result = func(*args, **kwargs)
except Exception:
    # 逆序执行所有已记录的 undo
    for u in reversed(cmd.undo_stack):
        u()
    raise

```

但如果 `func` 内部调用了另一个被包装的方法（嵌套），`undo_stack` 会混入子调用的 undo——子调用明明成功了，回滚时难道也把它撤销掉？

### 4.4 全量回滚代替快照

如果操作链中间炸了，已经成功的操作应该自动撤销。

```python
try:
    result = func(*args, **kwargs)
except Exception:
    for u in reversed(cmd.undo_stack):  # 回滚整个栈
        u()
    raise
```

不需要快照。因为每个实例有独立的撤销栈，方法内部的嵌套调用会正常入栈，失败时逆序回滚全部即可。前提是 undo 方法实现了幂等（见第五章）。

> **注意**：如果被包装的方法内部调用了**其他实例**的被包装方法，且后者抛出异常，跨实例的回滚会变得非常复杂（涉及多个撤销栈的协调）。本文的实现暂不处理这种场景。

### 4.5 完整版的补充细节

`command.py` 比上面的骨架多了几个要点：

| 要点                  | 说明                                                                        |
| --------------------- | --------------------------------------------------------------------------- |
| `undo` 不存在时不记录 | `if not undo_method: return func(...)` — 没有 undo 的方法不参与事务         |
| `lambda` 默认参数捕获 | `lambda um=..., ba=...: um(*ba)` — 防止闭包陷阱                             |
| `wraps` 的正确用法    | 不要单独写 `wraps(func)` 再 `def wrapper`，应该 `@wraps(func)` 装饰 wrapper |
| `_command` 回退到类   | `getattr(self.cls, "_command", None)` — 防御性编程                          |
| 不用快照              | 每个实例有独立的撤销栈，失败时直接回滚整个栈即可                            |

### 4.6 使用方式

```python
@Command          # 或者 TodoList = Command(TodoList)
class TodoList:
    def create_todo(self, title, content):
        ...

    def create_todo_undo(self, title, content):
        ...       # 签名和原方法一致

TodoListCmd = Command(TodoList)
todo_list = TodoListCmd()   # 创建实例，自动注入独立 Command
```

### 4.7 另一种思路：方法返回撤销函数（dispose 模式）

装饰器方案虽然方便，但有一个无法回避的代价：**调用方不感知 undo 的存在**。所有 magic 都藏在 `instance._command` 里，出问题了调用方也不知情。

另一种思路更直白——让每个方法直接返回自己的撤销函数：

```python
class Order:
    def add_item(self, item):
        self.items.append(item)
        return lambda: self.items.remove(item)  # ← "怎么撤销我"

    def charge(self, amount):
        self.balance -= amount
        return lambda: setattr(self, 'balance', self.balance + amount)
```

调用方自己维护撤销栈：

```python
disposers = []

disposers.append(order.add_item(coffee))
disposers.append(order.charge(100))

# 想撤销？自己逆序执行
for fn in reversed(disposers):
    fn()
```

| 对比         | 装饰器方案          | dispose 模式       |
| ------------ | ------------------- | ------------------ |
| 撤销定义位置 | 单独的 `_undo` 方法 | 和原方法在一起     |
| 调用方负担   | 无感，异常自动回滚  | 手动维护 disposers |
| 事务边界     | 框架不确定          | 调用方完全掌控     |
| 复杂度       | 框架层复杂          | 每处调用多几行     |

dispose 模式本质上是把 Command 内部的那个 `command_list` 推到外面去了。没有谁绝对好——装饰器省事但隐式，dispose 显式但啰嗦。选哪个取决于你的项目想要「少写代码」还是「少出意外」。

---

## 五、undo 方法的编写要点

### 5.1 幂等性

回滚时可能面对"操作没完全执行"的状态，undo 方法必须**多次执行和一次执行效果相同**：

```python
# ❌ 非幂等
def create_todo_undo(self, title, content):
    self.todos.pop()  # 假设最后一个就是要删的

# ✅ 幂等
def create_todo_undo(self, title, content):
    for todo in reversed(self.todos):
        if todo.title == title and todo.content == content:
            self.todos.remove(todo)
            return
```

### 5.2 保存撤销所需的状态

```python
def update_todo(self, todo_id, content):
    todo = self._find(todo_id)
    self._old_content = todo.content  # ← 存到实例上
    todo.content = content

def update_todo_undo(self, todo_id, content):
    todo = self._find(todo_id)
    if todo:
        todo.content = getattr(self, "_old_content", content)
```

### 5.3 没有 undo 的方法不参与

```python
def display_all_todo(self):    # 没有 _undo 方法
    ...                         # 不会被记录，也不参与回滚
```

---

## 六、事务补偿的难度阶梯

undo 虽然写起来简单，但在真实系统中随着场景复杂度上升，实现难度会急剧增加：

| 级别 | 场景     | 示例                        | 解决方案                            | 复杂度     |
| ---- | -------- | --------------------------- | ----------------------------------- | ---------- |
| 1    | 幂等操作 | `if item in list: remove()` | 删 100 遍也没事                     | ⭐         |
| 2    | 数字加减 | `score += 10`               | 乐观锁 / 版本号                     | ⭐⭐       |
| 3    | 级联反应 | 订单 → 库存 → 优惠券 → 积分 | 区分可补偿/不可逆，不可逆放最后     | ⭐⭐⭐     |
| 4    | 跨服务   | 微服务 A → B → C            | Saga 编排 + 消息队列 + 重试         | ⭐⭐⭐⭐   |
| 5    | 异步操作 | 发邮件后炸了怎么撤回        | 两阶段：预占 → 执行，接受部分不可逆 | ⭐⭐⭐⭐⭐ |

本文实现的装饰器方案主要覆盖**级别 1~2**，对于级别 3 以上的场景，建议参考 Saga 模式、工作单元（Unit of Work）和分布式事务相关的内容。

---

## 附：完整实现

```python
from typing import TypeVar, ParamSpec, Callable, Any, Generic
from copy import copy
from functools import wraps

T = TypeVar("T")
P = ParamSpec("P")


class Command(Generic[T]):
    def __init__(self, cls: type[T]):
        self.cls = cls
        self.command_list: list[Callable[[], None]] = []
        self._wrapper_method(cls)

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        """创建实例，注入独立的 Command 副本（实例间撤销栈隔离）"""
        instance = self.cls(*args, **kwargs)
        new_command = copy(self)
        new_command.command_list = []
        instance._command = new_command
        return instance

    def _wrapper_method(self, cls: type[T]) -> None:
        """将类的公开方法替换为包装版本"""
        for name in dir(cls):
            if name.startswith("_"):
                continue
            attr = getattr(cls, name)
            if not callable(attr):
                continue
            setattr(cls, name, self._push(attr, name))

    def _push(self, func: Callable[P, Any], name: str) -> Callable[P, Any]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            instance = args[0] if args else self
            undo_method = getattr(instance, f"{name}_undo", None) or getattr(
                self.cls, f"{name}_undo", None
            )
            command_obj = getattr(instance, "_command", None) or getattr(
                self.cls, "_command", None
            )

            if not undo_method or not command_obj:
                return func(*args, **kwargs)

            bound_args = args[1:]
            command_obj.command_list.append(
                lambda um=undo_method, ba=bound_args, kw=kwargs: um(*ba, **kw)
            )

            try:
                return func(*args, **kwargs)
            except Exception:
                for undo_func in reversed(command_obj.command_list):
                    undo_func()
                raise

        return wrapper
```

---

## 七、一个尴尬的问题：undo 栈永远在涨

看到这里你可能会发现一个尴尬的事实：**撤销栈只增不减**。

```python
todo_list = TodoListCommand()
todo_list.create_todo("A", "内容A")  # command_list = [undo_A]
todo_list.create_todo("B", "内容B")  # command_list = [undo_A, undo_B]
todo_list.create_todo("C", "内容C")  # command_list = [undo_A, undo_B, undo_C]
```

### 7.1 问题在哪

**正常操作完，栈还在。** 就算所有操作都成功了，那些 undo lambda 依然挂在 `command_list` 里。万一用户不小心删了 `todo_list` 变量又重新创建了一个 `TodoListCommand()`，旧的栈倒是没了——但这是靠 Python GC，不是靠设计。

**回滚之后栈也在。** 异常触发回滚后，`command_list` 里的 undo 被**执行了但没有被清除**。如果再继续操作，新的 undo 会追加在后面：

```python
todo_list = TodoListCommand()
todo_list.create_todo("A", "内容A")
try:
    todo_list.done_todo(999)  # 💥 不存在，触发回滚
except ValueError:
    pass

# 此时 command_list = [undo_A] ← undo_A 已经被执行了，但还在栈里
# 如果再炸一次，undo_A 会被再次执行！
```

这和不释放内存的 `del` 没什么区别——句柄没了但痕迹还在。

### 7.2 理想方案：上下文管理器

根本问题在于**事务边界不清晰**。用户不知道什么算"一组操作"、什么时候该清栈。更好的设计是用上下文管理器让用户显式声明：

```python
with TodoListCommand() as todo_list:
    todo_list.create_todo("A", "内容A")
    todo_list.create_todo("B", "内容B")
    todo_list.done_todo(1)
# 正常退出 → 提交事务，清空撤销栈

with TodoListCommand() as todo_list:
    todo_list.create_todo("A", "内容A")
    todo_list.update_todo(999, "不存在")  # 💥
# 异常退出 → 自动回滚，清空撤销栈
```

或者更显式的 commit/rollback：

```python
tx = TodoListCommand()
todo_list = tx.__enter__()
todo_list.create_todo("A", "内容A")
tx.commit()   # ✅ 确认这组操作，清栈
todo_list.create_todo("B", "内容B")
tx.rollback() # 🔄 回滚 B，清栈
```

### 7.3 为什么当前版本没做

因为一旦引入 commit，问题就变成了 **「撤销栈应该什么时候清」**——而这个决策依赖业务场景：

- 如果每个方法是一个独立事务 → 每调用一次就清一次（那就和没有 undo 一样了）
- 如果一组方法是一个事务 → 需要在调用方显式标记边界
- 如果整个实例生命周期是一个事务 → 实例销毁时才清

当前版本选择了最简单的「实例级别隔离」，把边界的决定权留给了调用方。代价就是用户需要自己记得**在合适的时机清空 command_list**。这确实算不上一个「能用」的框架——更像一个演示事务补偿原理的教学玩具。

### 7.4 所以这个实现到底能不能用

说实话……搞了半天发现还是不太能用 😇

- 玩具项目、脚本、Demo：完全够用，写起来比手动 undo 舒服多了
- 生产环境单体应用：建议配合上下文管理器封装一层再上
- 微服务/分布式场景：别想了，上 Saga 吧

如果你真的想在项目里用，可以基于这个思路自己做两个改造：

1. 加上 `commit()` / `rollback()` 方法，让用户显式控制事务边界
2. 把 `command_list` 改成 `weakref.WeakSet` 或者限制最大长度，防止内存泄漏

---

## 八、不足与方向

- **不支持 `__slots__`**：`instance._command = ...` 对 slots 类会抛异常
- **不支持跨实例事务**：每个实例的撤销栈独立，无法编排 order 和 payment 的联合回滚
- **回滚粒度粗**：方法内部分失败无法精确还原，依赖 undo 方法的幂等性来保证安全
- **跨实例调用异常**：如果一个被包装方法内部调用了其他实例的被包装方法且抛出异常，当前实现无法协调多个撤销栈的回滚
