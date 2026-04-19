from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


# ============================================================================
# 产品类
# ============================================================================


@dataclass(slots=True)
class Body:
    """
    车身类，可被 Vehicle 类中的 body 属性持有

    :param type: 车身的样式
    :param color: 车身的颜色
    """

    type: str
    color: str = "White"


@dataclass(slots=True)
class Wheel:
    """
    车轮类，可作为 Vehicle 类中 wheel_list 的元素

    :param type: 车轮的样式
    :param spoke_count: 车轮辐条的数量
    """

    type: str
    spoke_count: int = 12


# ============================================================================
# 抽象工厂
# ============================================================================


class VehiclePartsFactory(ABC):
    """创建车辆部件的抽象工厂"""

    @abstractmethod
    def create_body(self) -> Body:
        """
        创建车身。

        :return: Body 实例
        """
        ...

    @abstractmethod
    def create_wheel(self) -> Wheel:
        """
        创建车轮

        :return: Wheel 实例
        """
        ...


# ============================================================================
# 具体工厂
# ============================================================================


class CarPartsFactory(VehiclePartsFactory):
    """小型车辆部件工厂"""

    def create_body(self) -> Body:
        return Body(type="Mini")

    def create_wheel(self) -> Wheel:
        return Wheel(type="Mini")


class TruckPartsFactory(VehiclePartsFactory):
    """大型车辆部件工厂"""

    def create_body(self) -> Body:
        return Body(type="Heavy")

    def create_wheel(self) -> Wheel:
        return Wheel(type="Big")


# ============================================================================
# 车辆类型枚举
# ============================================================================


class VehicleType(Enum):
    """车辆类型枚举"""

    CAR = "Car"
    TRUCK = "Truck"


# ============================================================================
# 产品类
# ============================================================================


@dataclass(slots=True)
class Vehicle:
    """
    车辆类，由工厂方法 make_vehicle 创建

    :param name: 车辆的名称
    :param type: 车辆的类型
    :param body: 车身对象，默认为 None
    :param wheel_list: 车轮列表，默认为空列表
    """

    name: str
    type: VehicleType
    body: Optional[Body] = None
    wheel_list: List[Wheel] = field(default_factory=list)

    def run(self) -> None:
        """
        启动车辆。

        :raises ValueError: 当缺失车体或车轮时抛出
        """
        if not self.body or not self.wheel_list:
            raise ValueError("缺失车体或车轮")
        print(f"{self.name} ({self.type.value}) 发动了！")

    def __str__(self) -> str:
        wheel_info = "\n".join(
            f"{i}. {wheel.type}" for i, wheel in enumerate(self.wheel_list, 1)
        )
        return (
            f"=== {self.name} ({self.type.value}) ===\n"
            f"车身: {getattr(self.body, 'type', 'Unknown')}\n"
            f"车轮:\n{wheel_info}"
        )


# ============================================================================
# 工厂方法（客户端接口）
# ============================================================================


def make_vehicle(name: str, vehicle_type: VehicleType, wheel_count: int) -> Vehicle:
    """
    制作车辆的工厂方法

    :param name: 车辆名称
    :param vehicle_type: 车辆类型
    :param wheel_count: 车轮数量
    :raises TypeError: 当传入未知的车辆类型时
    :return: Vehicle 类的实例
    """
    factories = {
        VehicleType.CAR: CarPartsFactory,
        VehicleType.TRUCK: TruckPartsFactory,
    }

    factory_class = factories.get(vehicle_type)
    if not factory_class:
        raise TypeError(f"未知的车辆类型: {vehicle_type}")

    factory = factory_class()
    vehicle = Vehicle(name=name, type=vehicle_type)
    vehicle.body = factory.create_body()
    vehicle.wheel_list = [factory.create_wheel() for _ in range(wheel_count)]

    return vehicle


# ============================================================================
# 测试
# ============================================================================


def main():
    car = make_vehicle("my_car", VehicleType.CAR, 4)
    print(car)
    car.run()

    print()

    truck = make_vehicle("my_truck", VehicleType.TRUCK, 6)
    print(truck)
    truck.run()


if __name__ == "__main__":
    main()
