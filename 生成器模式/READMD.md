# 🐍 Pythonic 设计模式：生成器模式

## 📚 目录

- [📖 什么是生成器模式？](#-什么是生成器模式)
- [🤔 为什么需要生成器模式？](#-为什么需要生成器模式)
- [🏗️ 核心结构](#️-核心结构)
- [📋 例子：简易订单生成器](#-例子简易订单生成器)
- [🔀 生成器模式的两种实现模式](#-生成器模式的两种实现模式)
- [📊 和策略模式对比](#-和策略模式对比)
- [🎁 进阶](#-进阶)
- [📝 总结](#-总结)

---

## 📖 什么是生成器模式？

生成器模式的主要目的是**将一个复杂对象的构建过程与其表示相分离**，从而可以创建具有不同表示形式的对象。

在软件系统中，一个复杂对象的创建通常由多个部分组成：这些部分的**组合经常变化**，但**组合的算法相对稳定**。当一些基本部件不变，而其组合经常变化时，就可以使用生成器模式。

> 📌 **人话**：把对象的属性和行为与创建此对象的逻辑分开。抽象 xxx 就是为了定义产品/建造者要拥有的属性/方法。

## 🤔 为什么需要生成器模式？

| 不使用生成器模式                                         | 使用生成器模式                         |
| -------------------------------------------------------- | -------------------------------------- |
| 构造函数参数爆炸                                         | 构造函数只需让建造者持有一个产品的实例 |
| 很难在修改引用类型的属性时增加副作用                     | 只需要在建造者相应的函数中编写逻辑即可 |
| 很难撤销对产品属性的修改                                 | 在建造者中可借鉴命令模式的思想         |
| 当面对一个**产品族**而非单一产品时，创建实例显得有心无力 | 便于统一管理同一产品族的产品创建       |

## 🏗️ 核心结构

| 角色                               | 职责                                                   | 示例代码中                    |
| ---------------------------------- | ------------------------------------------------------ | ----------------------------- |
| **产品（Product）**                | 要构建的复杂对象                                       | `Order`                       |
| **抽象建造者（Builder）**          | 定义构建产品的抽象接口                                 | （本例省略，Python 中非必须） |
| **具体建造者（Concrete Builder）** | 实现抽象建造者接口，负责返回最终产品                   | `OrderBuilder`                |
| **指导者（Director）**             | 模板方法模式，调用建造者的方法构建产品（**可有可无**） | `main()` 函数手动调用         |

> 📌 **例如**：产品族是汽车，则定义具有车身、颜色、车轮的抽象产品；再定义组装车身、喷漆、组装车轮的抽象建造者。

### 生成器模式的「指导者」：你真的需要吗？

在 GoF 原著里，生成器模式有一个 **Director（指导者）**，它负责**固定构建顺序**。

```python
class OrderDirector:
    def __init__(self, builder: OrderBuilder):
        self.builder = builder

    def create_default_order(self) -> Order:
        return self.builder.set_address('北京').add_item(0).get_order()

    def create_premium_order(self) -> Order:
        return self.builder.set_address('上海').add_item(0).add_item(1).get_order()
```

**什么时候需要 Director？**

- 多个建造者需要**统一的构建流程**
- 构建步骤有**严格的顺序依赖**

## 📋 例子：简易订单生成器

```python
from dataclasses import dataclass, field

LATEST_ORDER_ID = 0
ITEMS = [
    {'name': '铅笔', 'price': 2},
    {'name': '笔记本电脑', 'price': 7500},
    {'name': '可乐', 'price': 3.5}
]


def generate_order_id() -> int:
    global LATEST_ORDER_ID
    LATEST_ORDER_ID += 1
    return LATEST_ORDER_ID


def get_price(item_list: list[int]) -> list[float]:
    return [ITEMS[item_id]['price'] for item_id in item_list if 0 <= item_id < len(ITEMS)]


@dataclass(slots=True)
class Order:
    """产品：要构建的复杂对象"""
    id: str = field(default_factory=generate_order_id)
    address: str = None
    price: float = None
    item_list: list[int] = field(default_factory=list)

    def count_price(self) -> None:
        self.price = sum(get_price(self.item_list))

    def __str__(self):
        return '\n'.join(f'{value}: {getattr(self, value)}' for value in self.__slots__)


@dataclass(slots=True)
class OrderBuilder:
    """具体建造者：分步构建订单"""
    order: Order = field(default_factory=Order)

    def set_address(self, address: str) -> 'OrderBuilder':
        self.order.address = address
        return self

    def add_item(self, item_id: int) -> 'OrderBuilder':
        self.order.item_list.append(item_id)
        return self

    def get_order(self) -> Order:
        """构建完成：统一执行最终计算和校验"""
        self.order.count_price()
        if not all(getattr(self.order, value) for value in self.order.__slots__):
            raise ValueError
        return self.order


def main():
    order = OrderBuilder().set_address('北京').add_item(0).add_item(1).get_order()
    print(order)


if __name__ == '__main__':
    main()
```

**输出：**

```
id: 1
address: 北京
price: 7502
item_list: [0, 1]
```

### 🔗 链式调用的关键

| 写法                                    | 目的                     | 要点                                                        |
| --------------------------------------- | ------------------------ | ----------------------------------------------------------- |
| `set_address` 和 `add_item` 返回 `self` | 实现**链式调用**         | 这是生成器模式的标志性特征，让代码读起来像一句流畅的话      |
| `get_order` 方法                        | 作为**"构建完成"的信号** | 在这个方法里统一执行最终计算（`count_price`）和校验         |
| `Order` 类保持简单                      | 分离了**"构建"和"表示"** | `Order` 只负责存储数据，`OrderBuilder` 负责如何一步步构建它 |

## 🔀 生成器模式的两种实现模式

| 方式         | 代码示例               | 特点                   |
| ------------ | ---------------------- | ---------------------- |
| **持有实例** | `self.order = Order()` | 直接在原对象上修改     |
| **持有属性** | `self._address = None` | `build()` 时创建新对象 |

### 📋 持有实例的缺点

- `get_order()` 返回的是**同一个实例**，调用多次会拿到同一个对象
- 无法实现**不可变对象**（调用者可以继续修改返回的订单）
- 构建器状态和产品对象**绑定**，无法复用构建器生成多个变体

### 🔧 改成「持有属性」

```python
import copy

@dataclass(slots=True)
class OrderBuilder(Order):

    def set_address(self, address: str) -> 'OrderBuilder':
        self.address = address
        return self

    def add_item(self, item_id: int) -> 'OrderBuilder':
        self.item_list.append(item_id)
        return self

    def get_order(self) -> Order:
        self.count_price()
        if not all(getattr(self, value) for value in self.__slots__):
            raise ValueError
        return Order(address=self.address, price=self.price, item_list=copy.deepcopy(self.item_list))
```

## 📊 和策略模式对比

| 对比维度     | 生成器模式                       | 策略模式                         |
| ------------ | -------------------------------- | -------------------------------- |
| **关注点**   | **对象的构建过程**               | **算法的可替换性**               |
| **调用方式** | 链式调用，分步构建               | 构造函数注入，运行时切换         |
| **返回结果** | 最终返回一个**完整产品**         | 执行某个**操作**，不一定返回产品 |
| **典型场景** | 制作一个汉堡（加肉、加菜、加酱） | 支付方式（微信/支付宝/银行卡）   |

**一句话区分**：生成器是 **"怎么做一个东西"** ，策略是 **"用一个东西怎么做事"** 。

## 🎁 进阶

如果你想让建造者**根据参数类型自动选择不同的构建逻辑**，可以用 Python 的 `singledispatchmethod`：

```python
from functools import singledispatchmethod

class OrderBuilder:
    @singledispatchmethod
    def add_item(self, item):
        raise TypeError(f"不支持的类型: {type(item)}")

    @add_item.register
    def _(self, item_id: int) -> 'OrderBuilder':
        self.item_list.append(item_id)
        return self

    @add_item.register
    def _(self, item_name: str) -> 'OrderBuilder':
        item_id = next(i for i, item in enumerate(ITEMS) if item['name'] == item_name)
        self.item_list.append(item_id)
        return self

# 使用
OrderBuilder().add_item(0).add_item('可乐').get_order()
```

**效果**：既可以 `add_item(0)`（按 ID），也可以 `add_item('可乐')`（按名称）。

## 📝 总结

| 概念             | 说明                                         |
| ---------------- | -------------------------------------------- |
| **产品**         | 要构建的复杂对象（`Order`）                  |
| **具体建造者**   | 分步构建产品，支持链式调用（`OrderBuilder`） |
| **指导者**       | 调用建造者的方法，控制构建顺序（可选）       |
| **链式调用**     | `return self` 让代码像流水线一样流畅         |
| **构建完成信号** | `get_order()` 统一执行校验和最终计算         |
