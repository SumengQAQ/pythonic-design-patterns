## 📚 目录

- [📖 什么是原型模式？](#-什么是原型模式)
- [🐍 Python 自带的“复印机”](#-python-自带的复印机)
- [🆚 浅拷贝 vs 深拷贝](#-浅拷贝-vs-深拷贝)
- [🔧 什么时候要自己写 `__copy__` / `__deepcopy__`？](#-什么时候要自己写-__copy____deepcopy__)
- [🤔 `__deepcopy__` 中的 `memo` 是个什么东西？](#-__deepcopy__-中的-memo-是个什么东西)
- [🏭 原型管理器](#-原型管理器)
- [🏆 什么时候用原型模式？](#-什么时候用原型模式)
- [📝 总结](#-总结)

---

## 📖 什么是原型模式？

**原型模式**就是通过 `copy.copy()`、`copy.deepcopy()` 或自定义类的 `clone` 方法，从而获得一个**一模一样**的实例。

当**创建对象消耗的资源很大**，或**创建对象耗时很长**时，**复制比新建更划算**。

> ⚠️ **注意**：这里“一模一样”指的是**字面值**，而非引用。具体的引用关系会因为浅拷贝/深拷贝的实现策略有所不同。

好吧，这可能是 GoF 中最简单的一个模式之一了……

---

## 🐍 Python 自带的“复印机”

```python
import copy

# 浅拷贝：只复制外层，内部对象共享
new_obj = copy.copy(obj)

# 深拷贝：递归复制所有嵌套对象
new_obj = copy.deepcopy(obj)
```

---

## 🆚 浅拷贝 vs 深拷贝

```python
class Team:
    def __init__(self, name, members):
        self.name = name
        self.members = members  # 列表是可变对象

original = Team("原团队", ["张三", "李四"])

# 浅拷贝
shallow = copy.copy(original)
shallow.members.append("王五")
print(original.members)  # ['张三', '李四', '王五']  ← 原对象也被改了！

# 深拷贝
deep = copy.deepcopy(original)
deep.members.append("赵六")
print(original.members)  # ['张三', '李四', '王五']  ← 原对象不受影响
```

**结论：** 浅拷贝只复制“外层”，内部的可变对象是**共享**的；深拷贝会**递归复制**所有嵌套对象。

事实上，我们可以通过重写类中的 `__copy__` 与 `__deepcopy__`，来自定义 `copy.copy()` 与 `copy.deepcopy()` 时的行为。

---

## 🔧 什么时候要自己写 `__copy__` / `__deepcopy__`？

Python 的 `deepcopy` 不是万能的。以下情况需要**手动控制复制逻辑**：

| 场景           | 问题                          | 解决方案                       |
| -------------- | ----------------------------- | ------------------------------ |
| **文件句柄**   | 不能复制                      | 克隆时重新打开文件             |
| **数据库连接** | 不能复制                      | 克隆时创建新连接，或共享原连接 |
| **单例对象**   | 只能有一个实例                | 克隆时返回同一个实例           |
| **循环引用**   | `deepcopy` 能处理，但可能很慢 | 手动打破循环                   |
| **大对象**     | `deepcopy` 递归太慢           | 只复制需要的字段               |

### 📋 示例：处理不可复制的数据库连接

```python
import copy

class Connection:
    """模拟数据库连接（不可复制）"""
    def __init__(self, db_name):
        self.db_name = db_name
        print(f"建立连接: {db_name}")

    def __copy__(self):
        """浅拷贝时：创建新连接"""
        return Connection(self.db_name)

    def __deepcopy__(self, memo):
        """深拷贝时：也创建新连接"""
        return Connection(self.db_name)


class Config:
    def __init__(self, db_name):
        self.conn = Connection(db_name)
        self.settings = {"theme": "dark", "lang": "zh"}

    def __copy__(self):
        """浅拷贝：settings 浅复制，conn 通过 Connection.__copy__ 处理"""
        new = type(self)(self.conn.db_name)  # 复用原 db_name
        new.settings = self.settings.copy()
        return new

    def __deepcopy__(self, memo):
        """深拷贝：settings 深复制，conn 通过 Connection.__deepcopy__ 处理"""
        new = type(self)(self.conn.db_name)
        new.settings = copy.deepcopy(self.settings, memo)
        return new
```

---

## 🤔 `__deepcopy__` 中的 `memo` 是个什么东西？

`memo` 是一个**字典**，用于记录**已经被复制过的对象**，从而**避免循环引用导致的死循环**。

> 📌 **举例**：假设有一个循环链表，节点 A 指向节点 B，节点 B 指向节点 A。`deepcopy` 在复制 A 时，会把 A 记录到 `memo` 里；当复制到 B 时，发现 A 已经复制过了，就不会再递归复制 A，而是直接引用。

```python
def __deepcopy__(self, memo):
    if id(self) in memo:
        return memo[id(self)]   # 已经复制过了，直接返回
    # ... 复制逻辑 ...
    memo[id(self)] = new_obj    # 记录已复制
    return new_obj
```

---

## 🏭 原型管理器

当有多种原型时，可以用**字典**统一管理：

```python
import copy
from typing import Any
from dataclasses import dataclass, field


@dataclass(slots=True)
class PrototypeManager:
    _prototype_dict: dict = field(default_factory=dict)

    def register(self, prototype_name: str, prototype: Any) -> None:
        """注册原型"""
        self._prototype_dict[prototype_name] = prototype

    def clone(self, prototype_name: str, **kwargs):
        """克隆并微调"""
        obj = copy.deepcopy(self._prototype_dict[prototype_name])
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj


@dataclass(slots=True)
class Enemy:
    name: str
    health: int
    attack: int

    def __str__(self):
        return f'name: {self.name}, health: {self.health}, attack: {self.attack}'


def main():
    manager = PrototypeManager()
    manager.register('goblin', Enemy('哥布林', 50, 10))
    manager.register('dragon', Enemy('龙', 500, 80))

    # 克隆并微调
    boss = manager.clone("dragon", health=800)
    print(boss)


if __name__ == '__main__':
    main()
```

**运行结果：**

```
name: 龙, health: 800, attack: 80
```

---

## 🏆 什么时候用原型模式？

| 场景                               | 用原型 | 不用               |
| ---------------------------------- | ------ | ------------------ |
| 对象创建成本高（数据库、IO、网络） | ✅     | ❌                 |
| 需要大量相似对象                   | ✅     | ❌                 |
| 对象有复杂嵌套结构                 | ✅     | ⚠️ 可用 `deepcopy` |
| 简单对象（几个 `int`/`str`）       | ❌     | ✅ 直接 `new`      |

---

## 📝 总结

| 概念                        | 说明                         |
| --------------------------- | ---------------------------- |
| **原型模式**                | 用复制代替 `new`             |
| **浅拷贝**                  | 只复制外层，内部共享         |
| **深拷贝**                  | 递归复制所有嵌套对象         |
| `__copy__` / `__deepcopy__` | 控制自定义类的复制行为       |
| **原型管理器**              | 管理多个原型，支持克隆后微调 |

---

## 📂 文件结构

```
原型模式/
├── shallow_vs_deep.py      # 浅拷贝 vs 深拷贝示例
├── custom_copy.py          # 自定义 __copy__ / __deepcopy__
├── prototype_manager.py    # 原型管理器
└── task.md               # 本文件
```
