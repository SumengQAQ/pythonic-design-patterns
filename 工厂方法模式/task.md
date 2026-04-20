## 🏭 工厂方法模式：从硬编码到 Pythonic

### 1. 需求场景

我们要打印**警察**和**汽车**的信息：

- **警察**：显示 `name: Mr.Green, age: 30, weight: 70 kg`
- **汽车**：显示 `type: Car, weight: 1200 kg`

如果只是为了完成需求，直接重写 `__str__` 即可。但我们要展示的是**工厂方法模式的演化过程**。

### 2. 版本 0：硬编码（最直观，但最僵化）

```python
class Police:
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight

    def draw(self):
        print(f'name: {self.name}, age: {self.age}, weight: {self.weight} kg')

class Car:
    def __init__(self, type, weight):
        self.type = type
        self.weight = weight

    def draw(self):
        print(f'type: {self.type}, weight: {self.weight} kg')

# 使用
Police("Mr.Green", 30, 70).draw()
Car("Car", 1200).draw()
```

**问题：**

- 每个类都要写自己的 `draw` 方法
- 绘制逻辑和业务逻辑混在一起
- 如果绘制方式变化，每个类都要改

### 3. 版本 1：工厂方法（Java 思维版）

把「绘制」抽成独立的 `Drawer` 类，让每个业务类决定用哪个 `Drawer`：

```python
from abc import ABC, abstractmethod

# 抽象产品
class Drawer(ABC):
    @abstractmethod
    def draw(self): pass

# 具体产品
class PoliceDrawer(Drawer):
    def __init__(self, person):
        self.person = person
    def draw(self):
        print(f'name: {self.person.name}, age: {self.person.age}, weight: {self.person.weight} kg')

class CarDrawer(Drawer):
    def __init__(self, car):
        self.car = car
    def draw(self):
        print(f'type: {self.car.type}, weight: {self.car.weight} kg')

# 抽象创建者
class Drawable(ABC):
    @abstractmethod
    def create_drawer(self) -> Drawer: pass

    def draw(self):
        drawer = self.create_drawer()
        drawer.draw()

# 具体创建者
class Police(Drawable):
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight
    def create_drawer(self):
        return PoliceDrawer(self)

class Car(Drawable):
    def __init__(self, type, weight):
        self.type = type
        self.weight = weight
    def create_drawer(self):
        return CarDrawer(self)

# 使用
Police("Mr.Green", 30, 70).draw()
Car("Car", 1200).draw()
```

**问题：**

- 代码量翻了几倍，每个业务类都要多写一个 `create_drawer` 方法
- `draw` 是无状态的，使用函数即可
- 职责不清晰：`create_drawer` 并非 `Police` 和 `Car` 的本质行为，而是一种**附加能力**

### 4. 最终版：Pythonic 工厂方法

用**装饰器**动态给类添加 `draw` 方法，保持业务类的纯粹：

```python
from functools import wraps
from dataclasses import dataclass


class Draw:
    """绘制器集合（相当于工厂）"""
    @staticmethod
    def police(obj: "Police") -> None:
        print(f"name: {obj.name}, age: {obj.age}, weight: {obj.weight} kg")

    @staticmethod
    def car(obj: "Car") -> None:
        print(f"type: {obj.type}, weight: {obj.weight} kg")


def can_draw(drawer_func):
    """装饰器：给类动态添加 draw 方法（相当于工厂方法）"""
    def decorator(cls):
        @wraps(cls)
        def wrapper(*args, **kwargs):
            obj = cls(*args, **kwargs)
            obj.draw = lambda: drawer_func(obj)
            return obj
        return wrapper
    return decorator


# 业务类只关心自己的数据
@can_draw(Draw.police)
@dataclass
class Police:
    name: str
    age: int
    weight: int


@can_draw(Draw.car)
@dataclass
class Car:
    type: str
    weight: int


# 使用
Police("Mr.Green", 30, 70).draw()
Car("Car", 1200).draw()
```

**优势：**

- 业务类只关心数据，不关心绘制逻辑
- 绘制逻辑集中在 `Draw` 类中，易于维护和扩展
- 装饰器动态添加 `draw` 方法，无需侵入业务类
- 符合**开闭原则**：新增绘制方式只需加静态方法，无需改业务类

### 5. 工厂方法模式 vs Pythonic 装饰器

| 维度         | 经典工厂方法              | Pythonic 装饰器             |
| ------------ | ------------------------- | --------------------------- |
| **代码量**   | 多（抽象类 + 多个具体类） | 少（一个装饰器 + 静态方法） |
| **侵入性**   | 业务类必须继承抽象类      | 业务类完全无感知            |
| **灵活性**   | 运行时绑定                | 编译时（定义时）绑定        |
| **适合场景** | 需要运行时切换工厂        | 工厂策略固定                |

### 6. 总结

| 模式              | 一句话                                             |
| ----------------- | -------------------------------------------------- |
| **工厂方法**      | 定义一个用于创建对象的接口，让子类决定实例化哪个类 |
| **Pythonic 替代** | 用装饰器 + 静态方法，保持业务类的纯粹              |
