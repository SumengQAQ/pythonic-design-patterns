# 📐 MVP模式实战：从MVC到MVP——用接口隔离重构待办系统

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


## 🔥 接口隔离：Protocol怎么用？

Python的`typing.Protocol`让你能定义“合同”——它不看类继承了什么，只看类**有没有合同要求的方法签名**。

```python
from typing import Protocol

class SingleTodoDisplayer(Protocol):
    """合同1：只需要显示单条待办的调用方"""
    def display_one_todo(self, title: str) -> None: ...

class MultiTodoDisplayer(Protocol):
    """合同2：只需要显示全部待办的调用方"""
    def display_todo_with_condition(self, condition) -> None: ...
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

**调用方如何受益？**

```python
def show_single_todo(displayer: SingleTodoDisplayer, title: str):
    displayer.display_one_todo(title)  # 只依赖SingleTodoDisplayer
```

`show_single_todo`不知道`View`的存在。它只知道传进来的对象能满足它需要的合同。未来你想换成网页版，只需要写一个满足相同协议的新类，`show_single_todo`不需要任何修改。


## 📋 MVC vs MVP：调用方向对比

| MVC               | MVP              |
|-------------------|------------------|
| Controller调用`view.display_one_todo()` | Presenter调用`single_displayer.display_one_todo()`，通过协议 |
| Controller知道View的具体类型 | Presenter只知道协议，不知道View的类型 |
| View被动等待Controller调用 | View通过协议定义“我需要什么”，Presenter通过协议提供服务 |


## 📁 文件结构

```
MVP模式/
├── todo_mvp.py          # 完整MVP代码（本文档的完整实现）
└── README.md            # 本文件
```
