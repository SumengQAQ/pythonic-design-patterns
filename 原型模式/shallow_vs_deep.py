import copy


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
