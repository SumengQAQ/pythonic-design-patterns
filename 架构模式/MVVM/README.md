# 🎓 学生成绩管理系统（MVVM实战）

## 🎯 什么是MVVM？

MVVM是MVC和MVP的**数据绑定增强版**。核心变化只有一步：

> **ViewModel持有缓存，通过回调函数自动通知View刷新。View不需要知道数据从哪来，ViewModel不需要知道View怎么显示。**

| MVC | MVP | MVVM |
|-----|-----|------|
| Controller协调View和Model | Presenter通过协议更新View | **ViewModel + 数据绑定** |
| View可能知道Model | View完全不碰Model | View完全不碰Model |
| Controller手动调View | Presenter手动调View | **ViewModel自动通知View** |

## 🏗️ 架构图

```
用户输入 → View → ViewModel → Service → Repository → 字典数据库
              ↑          ↓
              └─ bind() ─┘  (数据绑定：ViewModel自动通知View刷新)
```

每一层的职责：
- **Model**：纯数据容器（`@dataclass`），只有属性，没有行为
- **Repository**：封装数据访问，对上层隐藏数据库实现
- **Service**：业务校验 + 调用Repository
- **ViewModel**：持有缓存 + 数据绑定 + 增量更新
- **View**：纯显示 + 接收用户输入，不碰任何业务逻辑

## 🔥 核心亮点

| 亮点 | 说明 | 在哪里体现 |
|------|------|-----------|
| **数据绑定** | ViewModel通过`bind(callback)`自动通知View刷新 | `view_model.bind(self.display_all)` |
| **增量更新** | 增删改时只更新变化的部分，不重新拉全量 | `add_student`里只追加新数据 |
| **职责分离** | 每层只做一件事，换数据库只改Repository，换界面只改View | 五层清晰分离 |
| **依赖注入** | Service不直接操作全局变量，而是通过Repository | `Service.add_student`调`Repository.add_one` |
| **单文件纯Python** | 不依赖任何框架、数据库、前端 | 一个`grade_mvvm.py`搞定 |

## 📁 文件结构

```
MVVM模式/
├── grade_mvvm.py        # 完整MVVM代码
└── README.md            # 本文件
└── todo_mvvm.py         # 之前的待办系统（MVVM版）
```

## 🙋‍♂️ 关于作者

- **塑梦** / SumengQAQ
- GitHub：[pythonic-design-patterns](https://github.com/SumengQAQ/pythonic-design-patterns)

