# 🧪 MVC模式实战：纯Python控制台待办系统

## 📖 什么是MVC？

MVC是一种**分层架构**，把代码分成三个部分：

| 层 | 职责 | 生活类比 |
|---|------|---------|
| **Model** | 数据本身 | 菜单上的菜 |
| **View** | 显示给用户看 | 服务员把菜端上来 |
| **Controller** | 协调Model和View | 厨师长：接到订单→做菜→让服务员上菜 |

**核心原则：View不直接碰Model，必须通过Controller。**

---

## 🎯 为什么需要MVC？

### 没有MVC时（意大利面代码）

```python
# 所有逻辑混在一起
def add_todo():
    title = input("标题：")
    if not title:
        print("标题不能为空")
        return
    # 直接操作全局变量
    DATABASE[title] = {"title": title, "done": False}
    print(f"添加成功：{title}")
```

**问题**：显示逻辑（`print`）和数据操作（`DATABASE[title]=...`）混在一起。以后想换成网页界面，整个函数都要重写。

### 有MVC后（分层代码）

```python
# View层：只处理显示
def display_success(title):
    print(f"添加成功：{title}")

# Service层：只处理业务逻辑
def add_todo(title, database):
    if not title:
        raise ValueError("标题不能为空")
    database[title] = {"title": title, "done": False}
    return title

# Controller层：协调两者
def handle_add():
    title = input("标题：")
    try:
        result = add_todo(title, DATABASE)
        display_success(result)
    except ValueError as e:
        print(f"错误：{e}")
```

**好处**：以后想换成网页界面，只需要改View层，Service层不用动。

---

## 🏗️ 完整的MVC架构

```
用户输入 → View → Controller → Service → Repository → 数据库
```

| 层 | 职责 | 依赖方向 |
|---|------|---------|
| **Model** | 纯数据容器（`@dataclass`） | 不依赖任何层 |
| **Repository** | 封装数据访问（增删改查） | 依赖Model |
| **Service** | 业务校验 + 调用Repository | 依赖Repository |
| **Controller** | 协调View和Service，统一处理异常 | 依赖Service和View |
| **View** | 纯显示（`print`/`input`） | 依赖Controller传回的数据 |

---

## 📋 本项目用到的技术

| 技术 | 用在哪儿 | 为什么用 |
|------|---------|---------|
| `@dataclass` | Model层 | 纯数据容器，不需要写`__init__` |
| `OrderedDict` | Repository层 | 模拟数据库，保持插入顺序 |
| `lambda` + `Enum` | 筛选条件 | 函数式编程，三种筛选（全部/已完成/未完成） |
| 默认参数 | Repository层 | 依赖注入：Service不直接操作全局变量，而是通过参数接收数据库 |
| `try/except` | Controller层 | 统一处理异常，View只需要显示结果 |

---

## 🔥 依赖注入是怎么实现的？

```python
# 全局变量（模拟数据库）
mock_database = OrderedDict()

# Repository层：通过默认参数接收数据库
def _add_todo(title, content="", database=mock_database):
    database[title] = ToDo(title, content)
```

**好处**：测试时可以传入假数据库，生产环境传入真实数据库，Service层不需要改。

---

## 📁 文件结构

```
MVC/
├── todo_mvc.py          # 完整MVC代码
├── README.md            # 本文件
└── test_todo_mvc.py     # 单元测试（待补充）
```

---

## 🙋‍♂️ 关于作者

- **塑梦** / SumengQAQ
- 新媒体技术专业（对，不是计算机系专业）
- GitHub：[pythonic-design-patterns](https://github.com/SumengQAQ/pythonic-design-patterns)
