from dataclasses import dataclass, field

TODOID = 1


@dataclass
class Todo:
    title: str
    content: str
    id: int = field(default_factory=lambda: TODOID)
    done: bool = False

    def __post_init__(self):
        global TODOID
        TODOID += 1
        print(f"创建了Todo #{self.id}:{self.title}")

    def __str__(self):
        return f"Todo #{self.id}: {self.title}\n内容:{self.content}\n状态:{'完成' if self.done else '未完成'}"

    def update(self, content: str) -> None:
        self.content = content
        print(f"更新了Todo #{self.id}:{self.title}")

    def finish(self) -> None:
        self.done = True
        print(f"完成了Todo #{self.id}:{self.title}")


class TodoList:
    def __init__(self):
        self.todos: list[Todo] = []

    def _search_todo(self, todo_id: int) -> Todo | None:
        return next((todo for todo in self.todos if todo.id == todo_id), None)

    def create_todo(self, title: str, content: str) -> Todo:
        todo = Todo(title, content)
        self.todos.append(todo)
        return todo

    def create_todo_undo(self, title: str, content: str) -> None:
        """撤销创建：删除最后一个匹配的 Todo"""
        # 倒序找最后一个匹配的（因为可能同标题）
        for todo in reversed(self.todos):
            if todo.title == title and todo.content == content:
                self.todos.remove(todo)
                print(f"撤销创建：删除了 Todo #{todo.id}:{todo.title}")
                return

    def update_todo(self, todo_id: int, content: str) -> None:
        todo = self._search_todo(todo_id)
        if not todo:
            raise ValueError(f"未找到 Todo #{todo_id}")
        old_content = todo.content
        todo.content = content
        # 🔥 把旧内容存到实例上，undo 时用
        self._last_old_content = old_content

    def update_todo_undo(self, todo_id: int, content: str) -> None:
        """撤销更新：恢复旧内容"""
        todo = self._search_todo(todo_id)
        if not todo:
            return
        old = getattr(self, "_last_old_content", content)
        todo.content = old
        print(f"撤销更新：恢复了 Todo #{todo_id} 的内容")

    def done_todo(self, todo_id: int) -> None:
        todo = self._search_todo(todo_id)
        if not todo:
            raise ValueError(f"未找到 Todo #{todo_id}")
        todo.finish()

    def done_todo_undo(self, todo_id: int) -> None:
        """撤销完成：恢复为未完成"""
        todo = self._search_todo(todo_id)
        if not todo:
            return
        todo.done = False
        print(f"撤销完成：Todo #{todo_id} 恢复为未完成")

    def delete_done_todo(self) -> int:
        """删除已完成，返回被删除的数量"""
        done_todos = [todo for todo in self.todos if todo.done]
        self.todos = [todo for todo in self.todos if not todo.done]
        self._deleted_todos = done_todos  # ← 存下来给 undo 用
        print(f"删除了 {len(done_todos)} 个已完成的 Todo")
        return len(done_todos)

    def delete_done_todo_undo(self) -> None:
        """撤销删除：恢复被删的 Todo"""
        deleted = getattr(self, "_deleted_todos", [])
        self.todos.extend(deleted)
        print(f"撤销删除：恢复了 {len(deleted)} 个 Todo")

    def display_all_todo(self) -> None:
        print(f"共计 {len(self.todos)} 个 Todo")
        for todo in self.todos:
            print(todo)

    def display_todo(self, todo_id: int) -> None:
        todo = self._search_todo(todo_id)
        if not todo:
            print(f"未找到 Todo #{todo_id}")
            return
        print(todo)
