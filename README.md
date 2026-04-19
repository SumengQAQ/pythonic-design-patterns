# 🐍 Pythonic 设计模式

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

## 📖 关于本项目

这是一个用**现代 Python 语法**重写 GoF 23 种设计模式的教程仓库。

市面上大多数设计模式教程都是用 Java 写的，充满了 `AbstractSingletonProxyFactoryBean` 式的冗长代码。但 Python 有自己的语法糖和惯用法——我们用**协议、描述符、装饰器、元类**来实现同样的模式，代码量减少 50%，可读性提升 100%。

## 🎯 适合谁

- 学过 Python 基础，想进阶的开发者
- 被 Java 设计模式教程劝退的 Pythonista
- 想知道 `__get__`、`__new__`、`@dataclass` 怎么用在真实场景中的人

## 📚 目录

| 模式 | 核心 Python 特性 | 一句话总结 |
|------|-----------------|-----------|
| 单例模式 | `__new__`、元类、模块级单例 | 全局唯一，资源共享 |
| 原型模式 | `copy.copy()`、`__copy__` | 复制比新建更划算 |
| 适配器模式 | 组合、`__getitem__` | 把德国插头转成中国插座 |
| 桥接模式 | 抽象基类、组合 | 让抽象和实现独立变化 |
| ... | ... | ... |

## 🚀 快速开始

```bash
git clone https://github.com/SumengQAQ/pythonic-design-patterns.git
cd pythonic-design-patterns
```

## ⚠️ 许可证

本项目**没有**选择标准开源许可证。这意味着：

- 你可以自由查看、学习、吐槽本代码
- 如果你真的想用于商业或二次分发，请先联系我

## 🙋‍♂️ 作者

- **塑梦**
- 新媒体技术专业（对，不是计算机系）
- 邮箱：sumengovocn@gmail.com

