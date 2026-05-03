"""
==========================
六边形架构 · Lesson 2 — Ports & Adapters
==========================

核心思想就两句话：
  1️⃣ 核心层定义接口（Ports），不关心谁来实现
  2️⃣ 外层实现接口（Adapters），可以被替换

用咖啡店来举例：
  核心：做咖啡的配方和流程 —— 不管咖啡豆从哪来、咖啡做给谁
  适配器：咖啡豆供应商、出杯窗口 —— 可以换，不影响配方
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable


# ============================================================
# 🎯 第 1 步：定义领域模型（纯数据，零依赖）
# ============================================================
# 这些类不知道数据库、不知道终端、不知道任何外部世界。


class CoffeeMachineStatus(Enum):
    IDLE = auto()
    HIBERNATION = auto()
    WORKING = auto()
    FAULT = auto()


class OrderStatus(Enum):
    TO_BE_PRODUCTED = auto()
    IN_PRODUCTION = auto()
    AWAITING_PICKUP = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class CoffeeTypes(Enum):
    AMERICANO = auto()
    LATTE = auto()
    FLAT_WHITE = auto()
    CAPPUCCINO = auto()


@dataclass(slots=True)
class CoffeeMachine:
    _serial_number: str
    waiting_time: int
    create_at: int
    consecutive_count: int = 0
    capacity: float = 0.0
    status: CoffeeMachineStatus = CoffeeMachineStatus.HIBERNATION


@dataclass(slots=True)
class Order:
    customer_name: str
    coffee_type: CoffeeTypes
    create_at: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.TO_BE_PRODUCTED
    id: int | None = None


# ============================================================
# 🎯 第 2 步：定义 Ports（抽象接口）
# ============================================================
# Ports 是核心层对外的"需求清单"：
#   "我需要一个地方存咖啡机数据，不管你是 MySQL 还是文件"
#   "我需要一个地方显示信息，不管你是终端还是网页"
#
# 关键：Ports 属于核心层（内层），定义在内层代码中！


class CoffeeMachineRepository(ABC):
    """Port：咖啡机存储——核心层说"我要这个能力" """

    @abstractmethod
    def save(self, coffee_machine: CoffeeMachine) -> bool: ...

    @abstractmethod
    def get_all(self) -> list[CoffeeMachine]: ...

    @abstractmethod
    def get_one(self, serial_number: str) -> CoffeeMachine | None: ...


class OrderRepository(ABC):
    """Port：订单存储"""

    @abstractmethod
    def save(self, order: Order) -> bool: ...

    @abstractmethod
    def get_all(self) -> list[Order]: ...

    @abstractmethod
    def get_one(self, id: int) -> Order | None: ...


# ============================================================
# 🎯 第 3 步：实现业务逻辑（只依赖 Ports）
# ============================================================
# Service 只依赖抽象接口，不依赖具体实现。
# 这就是传说中的"依赖反转"——高层不依赖低层，大家都依赖抽象。


COFFEE_BEANS_PER_CUP = 15.0
MAX_CAPACITY = 500.0


class CoffeeMachineService:
    """核心业务：制作咖啡、管理咖啡机
       只依赖 CoffeeMachineRepository 接口（Port）"""

    def __init__(self, repo: CoffeeMachineRepository):
        self._repo = repo
        self._machines = repo.get_all()

    def make_coffee(self, index: int, waiting_time: int) -> bool:
        machines = self._machines
        if index < 0 or index >= len(machines):
            return False

        cm = machines[index]

        # 状态机校验
        if cm.status != CoffeeMachineStatus.IDLE:
            return False
        if cm.capacity < COFFEE_BEANS_PER_CUP:
            return False

        # 执行制作
        cm.capacity -= COFFEE_BEANS_PER_CUP
        cm.status = CoffeeMachineStatus.WORKING
        cm.create_at = waiting_time
        self._repo.save(cm)
        return True

    def add_beans(self, index: int, grams: float) -> int | None:
        machines = self._machines
        if index < 0 or index >= len(machines):
            return None

        cm = machines[index]
        if cm.capacity + grams > MAX_CAPACITY:
            return None

        cm.capacity += grams
        self._repo.save(cm)
        return int(cm.capacity)

    def get_all(self) -> list[CoffeeMachine]:
        self._machines = self._repo.get_all()
        return self._machines


class OrderService:
    """核心业务：订单管理
       只依赖 OrderRepository 接口（Port）"""

    def __init__(self, repo: OrderRepository):
        self._repo = repo

    def create(self, customer_name: str, coffee_type: CoffeeTypes) -> Order | None:
        order = Order(customer_name=customer_name, coffee_type=coffee_type)
        if self._repo.save(order):
            return order
        return None

    def get_all(self) -> list[Order]:
        return self._repo.get_all()


# ============================================================
# 🎯 第 4 步：实现 Adapters（适配器）
# ============================================================
# Adapters 实现 Ports 接口，把核心层和具体技术连接起来。
# Adapters 在外面，可以随便换！


class MemoryCoffeeMachineRepository(CoffeeMachineRepository):
    """Adapter：内存版咖啡机仓库 —— 测试/开发用"""

    def __init__(self):
        self._storage: list[CoffeeMachine] = []

    def save(self, coffee_machine: CoffeeMachine) -> bool:
        for i, cm in enumerate(self._storage):
            if cm._serial_number == coffee_machine._serial_number:
                self._storage[i] = coffee_machine  # upsert
                return True
        self._storage.append(coffee_machine)
        return True

    def get_all(self) -> list[CoffeeMachine]:
        return self._storage.copy()

    def get_one(self, serial_number: str) -> CoffeeMachine | None:
        for cm in self._storage:
            if cm._serial_number == serial_number:
                return cm
        return None


class MemoryOrderRepository(OrderRepository):
    """Adapter：内存版订单仓库"""

    def __init__(self):
        self._storage: list[Order] = []
        self._next_id = 1

    def save(self, order: Order) -> bool:
        if order.id is not None:
            for i, o in enumerate(self._storage):
                if o.id == order.id:
                    self._storage[i] = order
                    return True
        if order.id is None:
            order.id = self._next_id
            self._next_id += 1
        self._storage.append(order)
        return True

    def get_all(self) -> list[Order]:
        return self._storage.copy()

    def get_one(self, id: int) -> Order | None:
        for o in self._storage:
            if o.id == id:
                return o
        return None


# ============================================================
# 🎯 第 5 步：View（也是 Adapter！）
# ============================================================
# CLI 终端 View 也是一个 Adapter —— 它适配了"用户交互"这个 Port
# 以后想换成 PyQt / Web，只需要写新的 View Adapter


def terminal_output(message: str) -> None:
    print(message)


def terminal_input(prompt: str) -> str:
    return input(prompt)


class CoffeeShopView:
    """Adapter：终端界面的咖啡店视图"""

    def __init__(
        self,
        cm_service: CoffeeMachineService,
        order_service: OrderService,
        output: Callable[[str], None] = terminal_output,
        input_func: Callable[[str], str] = terminal_input,
    ):
        self._cm_service = cm_service
        self._order_service = order_service
        self._output = output
        self._input = input_func

    def show_machines(self):
        machines = self._cm_service.get_all()
        self._output("\n=== 咖啡机列表 ===")
        for i, cm in enumerate(machines):
            self._output(f"  [{i}] {cm._serial_number} | {cm.status.name} | 豆: {cm.capacity:.0f}g")


# ============================================================
# 🎯 第 6 步：组装（Wiring）
# ============================================================
# 把所有东西"接"在一起的地方就是 main
# 这是整个系统唯一知道"谁依赖谁"的地方


def main():
    # 1. 创建 Adapters（具体实现）
    cm_repo = MemoryCoffeeMachineRepository()
    order_repo = MemoryOrderRepository()

    # 2. 注入到 Service（核心业务）
    cm_svc = CoffeeMachineService(cm_repo)
    order_svc = OrderService(order_repo)

    # 3. 准备演示数据
    demo = CoffeeMachine(_serial_number="CM-001", waiting_time=30, create_at=0, capacity=200.0, status=CoffeeMachineStatus.IDLE)
    cm_repo.save(demo)

    # 4. View
    view = CoffeeShopView(cm_svc, order_svc)
    view.show_machines()

    # 5. 制作一杯咖啡
    print("\n☕ 制作咖啡...")
    success = cm_svc.make_coffee(0, 20)
    print(f"{'✅ 成功' if success else '❌ 失败'}")

    print("\n制作后状态：")
    view.show_machines()


"""
==========================
📐 架构总览
==========================

 src/
 ├── adapters/        ← 内层（核心）
 │   ├── model.py     ──── 领域模型（纯数据）
 │   ├── ports.py     ──── 抽象接口（Ports）
 │   └── service.py   ──── 业务逻辑（只依赖 Ports）
 │
 ├── domain/          ← 外层（适配器）
 │   ├── repository_memory.py  ──── 仓库实现（Adapter）
 │   └── view.py      ──── 视图实现（Adapter）
 │
 └── main.py          ──── 组装（Dependency Injection）

关键规则：
  ✅ 核心层✋不import外层任何东西
  ✅ 外层可以import核心层
  ✅ Ports定义在核心层
  ✅ Service只通过Ports操作数据
"""


if __name__ == "__main__":
    main()
