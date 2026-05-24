from typing import TypeVar, ParamSpec, Callable, Any, Generic
from copy import copy
from functools import wraps

T = TypeVar("T")
P = ParamSpec("P")


class Command(Generic[T]):
    """基于 Saga 模式的事务补偿框架，自动为类方法提供 undo 能力。

    通过装饰器或直接实例化包装目标类，使得目标类的每个公开方法
    都自动获得事务回滚能力：方法执行成功时记录对应的 undo 操作，
    方法抛出异常时自动逆序回滚之前执行成功的所有操作。

    已知限制：
    - 不支持 __slots__（除非在 slots 中加入 _command）
    - 不支持跨实例事务（每个实例有独立的撤销栈）
    - 回滚粒度依赖 undo 方法的幂等性

    使用示例：
        @Command
        class TodoList:
            def create_todo(self, title: str, content: str) -> Todo:
                todo = Todo(title, content)
                self.todos.append(todo)
                return todo

            def create_todo_undo(self, title: str, content: str) -> None:
                for todo in reversed(self.todos):
                    if todo.title == title and todo.content == content:
                        self.todos.remove(todo)
                        break

        todo_list = TodoList()
        todo_list.create_todo("任务A", "内容A")  # undo 自动入栈
        try:
            todo_list.update_todo(999, "不存在")
        except ValueError:
            pass  # 之前的操作被自动回滚
    """

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
        """将类的公开方法替换为带回滚能力的包装版本"""
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
