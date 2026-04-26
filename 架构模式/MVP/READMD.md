# 📐 MVP模式实战：从MVC到MVP——用接口隔离和事件总线重构待办系统

## 📖 什么是MVP？

MVP是MVC的**演化版**。它把MVC中的Controller换成了**Presenter**，核心变化只有一步：

> **View不再被动等待Controller调用，而是通过协议告诉Presenter“用户做了什么”，Presenter再通过协议更新View。**

| MVC | MVP | 核心变化 |
|-----|-----|---------|
| Controller持有View，主动调用View | **View持有Presenter**，用户输入传递给Presenter | **调用方向反转** |
| View和Model不直接通信 | **View和Model完全不通信**，所有通信都通过Presenter | **更严格的隔离** |


## 🎯 为什么要从MVC升级到MVP？

你在MVC中可能遇到过一个痛点：Controller太“忙”了——它要同时处理用户输入、调用Service、更新View，三者搅在一起。当你想换一种View（比如从控制台换成网页），Controller和View都要改。

MVP通过**接口隔离**解决了这个问题。它把View拆成多个独立的**协议**，Presenter只依赖这些协议，不依赖具体的View实现。

**更进一步**：当Service层需要通知多个组件（如日志、缓存刷新、界面更新）时，MVC的Controller会变得越来越臃肿。MVP引入了**事件总线**——Service只负责发出事件，不关心谁在听；订阅者各自处理自己关心的部分，完全解耦。


## 🔥 接口隔离：Protocol怎么用？

Python的`typing.Protocol`让你能定义“合同”——它不看类继承了什么，只看类**有没有合同要求的方法签名**。

```python
from typing import Protocol

class SingleTodoDisplayer(Protocol):
    """合同1：只需要显示单条待办的调用方"""
    @staticmethod
    def display_one_todo(title: str) -> None: ...

class MultiTodoDisplayer(Protocol):
    """合同2：只需要显示全部待办的调用方"""
    @staticmethod
    def display_todo_with_condition(condition) -> None: ...
```

你的`View`类不需要显式继承这些协议。只要它的方法签名与协议要求完全一致，Python的类型检查器就会自动认为它满足了协议。

```python
class View:
    """View实现了两个协议，但它自己并不知道"""
    @staticmethod
    def display_one_todo(title: str):
        print(_get_one_todo(title))

    @staticmethod
    def display_todo_with_condition(condition):
        print(...)
```

**为什么这么设计？** 未来你想换成网页版View，只需要写一个新的类满足同样的协议即可。Presenter完全不用改。如果你想加一个“语音播报View”，它只需要实现`SingleTodoDisplayer`协议，不需要被迫实现`MultiTodoDisplayer`的所有方法——这就是**接口隔离原则**。


## 🔔 事件总线：Service怎么通知多个组件？

### 是什么？

一个全局的广播站。任何函数都可以订阅自己感兴趣的事件，任何函数都可以发出事件。

### 有什么用？

让Service层（业务逻辑）和Logger（日志记录）、View（界面刷新）完全解耦。Service只负责发出事件，不关心谁在听；Logger和View各自订阅自己关心的事件，不关心事件是谁发出的。

### 关键代码

```python
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = defaultdict(list)

    def on(self, event: str, callback):
        """订阅事件"""
        self._subscribers[event].append(callback)

    def emit(self, event: str, *args, **kwargs):
        """发出事件——通知所有订阅者"""
        for callback in self._subscribers[event]:
            callback(*args, **kwargs)

# 全局单例
event_bus = EventBus()
```

### 怎么用？

**第1步：订阅**（程序启动时做一次）
```python
# Logger订阅事件
event_bus.on("todo_added", lambda title, _: print(f"[日志] 添加：{title}"))
event_bus.on("todo_deleted", lambda title: print(f"[日志] 删除：{title}"))
```

**第2步：触发**（Service操作完成时自动发出）
```python
class Service:
    @staticmethod
    def add_todo(title: str, content: str = ""):
        # ... 业务逻辑 ...
        event_bus.emit("todo_added", title, content)  # ← 发出事件

    @staticmethod
    def delete_todo(title: str):
        # ... 业务逻辑 ...
        event_bus.emit("todo_deleted", title)  # ← 发出事件
```

**你不需要手动触发任何东西。** Service操作完成后自动发出事件，EventBus自动通知订阅者，订阅者自动响应。

### 和观察者模式的关系

事件总线是**观察者模式的现代化版本**。GoF的经典观察者模式需要Subject维护观察者列表，而事件总线的Subject只负责发出事件，不关心谁在听——耦合度更低、更灵活。


## 📋 MVC vs MVP：调用方向对比

| MVC | MVP |
|-----|-----|
| Controller调用`view.display_one_todo()` | Presenter调用`single_displayer.display_one_todo()`，通过协议 |
| Controller知道View的具体类型 | Presenter只知道协议，不知道View的类型 |
| View被动等待Controller调用 | View通过协议定义“我需要什么”，Presenter通过协议提供服务 |
| Controller需要同时处理日志、缓存、界面更新 | Service发出事件，Logger/View各自订阅，互不干扰 |


## 📁 文件结构

```
MVP模式/
├── todo_mvp.py          # 完整MVP+事件总线+协议代码
└── README.md            # 本文件
```


## 🙋‍♂️ 关于作者

- **塑梦** / sumeng
- 新媒体技术专业（对，不是计算机专业）
- GitHub：[pythonic-design-patterns](https://github.com/SumengQAQ/pythonic-design-patterns)
