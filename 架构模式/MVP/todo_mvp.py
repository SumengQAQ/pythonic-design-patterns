from typing import OrderedDict, Callable, Type
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass

# ============================================
# 事件总线
# ============================================


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable):
        self._subscribers[event].append(callback)

    def emit(self, event: str, *args, **kwargs):
        for callback in self._subscribers[event]:
            callback(*args, **kwargs)


event_bus = EventBus()

event_bus.on("todo_added", lambda title, _: print(f"[日志] 添加：{title}"))
event_bus.on("todo_deleted", lambda title: print(f"[日志] 删除：{title}"))

# ============================================
# Model层：纯数据容器
# ============================================

mock_database = OrderedDict()


@dataclass(slots=True)
class ToDo:
    title: str
    content: str = ""
    finish: bool = False

    def done(self):
        self.finish = True

    def __str__(self):
        return f"title:{self.title}\ncontent:{self.content}\nfinish:{self.finish}"


# ============================================
# Repository层：数据访问
# ============================================


def _add_todo(title: str, content: str = "", database=mock_database) -> None:
    database[title] = ToDo(title, content)


def _delete_todo(title: str, database=mock_database) -> None:
    database.pop(title)


def _exists_todo(title: str, database=mock_database) -> bool:
    return title in database


def _get_all_todo(database=mock_database) -> dict[str, ToDo]:
    return database


def _get_one_todo(title: str, database=mock_database) -> ToDo | None:
    return database.get(title)


# ============================================
# 筛选条件（函数式编程风格）
# ============================================

default = lambda _: True
finish = lambda todo: todo.finish
unfinish = lambda todo: not todo.finish


class Condition(Enum):
    default = default
    finish = finish
    unfinish = unfinish


# ============================================
# View层：纯显示 + 接口协议
# ============================================

from typing import Protocol


class SingleTodoDisplayer(Protocol):
    @staticmethod
    def display_one_todo(title: str) -> None: ...


class MultiTodoDisplayer(Protocol):
    @staticmethod
    def display_todo_with_condition(condition: Callable[[ToDo], bool] = Condition.default) -> None: ...


class View:
    @staticmethod
    def display_one_todo(title: str):
        print(_get_one_todo(title))

    @staticmethod
    def display_todo_with_condition(condition: Callable[[ToDo], bool] = Condition.default):
        print(f"All todo: \n{'\n\t'.join(str(todo) for todo in _get_all_todo().values() if condition(todo))}")


# ============================================
# Service层：业务逻辑 + 事件触发
# ============================================


class Service:
    @staticmethod
    def add_todo(title: str, content: str = ""):
        if not title:
            raise ValueError("标题缺失")
        if _exists_todo(title):
            raise ValueError("标题重复")
        _add_todo(title, content)
        event_bus.emit("todo_added", title, content)

    @staticmethod
    def delete_todo(title: str):
        if not _exists_todo(title):
            raise ValueError("标题不存在")
        _delete_todo(title)
        event_bus.emit("todo_deleted", title)


# ============================================
# Presenter层：依赖协议，协调View和Service
# ============================================


def todo_presenter(
    service: Type[Service],
    single_displayer: SingleTodoDisplayer,
    multi_displayer: MultiTodoDisplayer,
    action: str,
    *args,
):
    try:
        if action == "add":
            title = args[0] if args else input("请输入标题：")
            content = args[1] if len(args) > 1 else input("请输入内容（可选）：")
            service.add_todo(title, content)
            return f"✅ 待办 '{title}' 已添加"
        elif action == "delete":
            title = args[0] if args else input("请输入要删除的标题：")
            service.delete_todo(title)
            return f"✅ 待办 '{title}' 已删除"
        elif action == "show_all":
            multi_displayer.display_todo_with_condition()
            return ""
        elif action == "show_one":
            title = args[0] if args else input("请输入标题：")
            single_displayer.display_one_todo(title)
            return ""
        else:
            return f"❌ 未知操作：{action}"
    except ValueError as e:
        return f"❌ 错误：{e}"


# ============================================
# 主程序入口
# ============================================


def main():
    while True:
        action = input("请输入操作：")
        if action == "exit":
            print("已退出")
            break
        print(todo_presenter(Service, View, View, action))


if __name__ == "__main__":
    main()
