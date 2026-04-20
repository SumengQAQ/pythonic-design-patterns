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
Police("Mr.Green", 30, 70).draw()  # pyright:ignore
Car("Car", 1200).draw()  # pyright:ignore
