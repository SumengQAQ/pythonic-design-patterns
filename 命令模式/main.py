# main.py
from command import Command
from todo import TodoList

# 用 Command 包装 TodoList
TodoListCommand = Command(TodoList)  # 等价于 @Command 装饰器


def test_normal():
    """测试 1：正常使用，不触发回滚"""
    print("=" * 50)
    print("测试 1：正常操作")
    print("=" * 50)

    todo_list = TodoListCommand()

    # 创建
    todo_list.create_todo("学 Python", "今天要学元编程")
    todo_list.create_todo("写博客", "写 CQRS 技术文章")
    todo_list.create_todo("跑步", "校园跑还有 85 公里")

    # 查看
    print("\n--- 当前列表 ---")
    todo_list.display_all_todo()

    # 完成一个
    todo_list.done_todo(2)

    # 更新一个
    todo_list.update_todo(1, "今天要学元编程 + 描述符")

    # 查看
    print("\n--- 更新后 ---")
    todo_list.display_all_todo()

    # 删除已完成的
    todo_list.delete_done_todo()

    # 查看
    print("\n--- 删除后 ---")
    todo_list.display_all_todo()

    print("\n✅ 测试 1 通过：所有操作正常完成")


def test_rollback_single():
    """测试 2：单步操作失败，回滚"""
    print("\n" + "=" * 50)
    print("测试 2：单步操作失败 → 回滚")
    print("=" * 50)

    todo_list = TodoListCommand()

    # 先创建几个
    todo_list.create_todo("任务1", "内容1")
    todo_list.create_todo("任务2", "内容2")
    print(f"当前数量：{len(todo_list.todos)}")  # 2

    # 尝试更新一个不存在的 Todo（会报错）
    try:
        todo_list.update_todo(999, "这不可能成功")  # 💥
    except ValueError as e:
        print(f"捕获异常：{e}")

    # 检查：之前创建的两个还在吗？（应该在，因为 update 没修改创建操作）
    print(f"回滚后数量：{len(todo_list.todos)}")  # 2 ✅


def test_rollback_chain():
    """测试 3：链式操作失败 → 回滚整个链"""
    print("\n" + "=" * 50)
    print("测试 3：链式操作失败 → 回滚整个链")
    print("=" * 50)

    todo_list = TodoListCommand()

    # 连续操作
    todo_list.create_todo("任务A", "内容A")
    todo_list.create_todo("任务B", "内容B")

    # 🔥 拿真实的 ID，不要写死 1！
    # 拿到刚刚创建的 ID
    first_id = todo_list.todos[0].id  # 任务A 的 ID
    todo_list.done_todo(first_id)  # 完成第一个 ✅

    print(f"操作后数量：{len(todo_list.todos)}")  # 2

    # 这一步会失败
    try:
        todo_list.update_todo(888, "不存在")  # 💥
    except ValueError:
        print("捕获异常，开始回滚...")

    # 回滚后：
    print(f"回滚后数量：{len(todo_list.todos)}")  # 0


def test_no_undo_available():
    """测试 4：方法没有对应的 undo，就不记录撤销"""
    print("\n" + "=" * 50)
    print("测试 4：没有 undo 的方法")
    print("=" * 50)

    todo_list = TodoListCommand()

    todo_list.create_todo("任务", "内容")
    # display_all_todo 没有对应的 undo，不记录
    todo_list.display_all_todo()

    print("✅ 测试 4 通过：没有 undo 的方法正常执行")


if __name__ == "__main__":
    test_normal()
    test_rollback_single()
    test_rollback_chain()
    test_no_undo_available()
    print("\n🎉 全部测试完成！")
