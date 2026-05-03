"""
==========================
六边形架构 · Lesson 3 — 完整咖啡店案例
==========================

把前两课的概念整合起来，实现一个可运行的咖啡店系统。
包含：异步制作咖啡、状态机校验、清洁提醒、异常处理。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable


# ============================================================
# 核心层 · 领域模型
# ============================================================


class CoffeeMachineStatus(Enum):
    IDLE = 0
    HIBERNATION = 1
    WORKING = 2
    FAULT = 3


class OrderStatus(Enum):
    TO_BE_PRODUCTED = 0
    IN_PRODUCTION = 1
    AWAITING_PICKUP = 2
    COMPLETED = 3
    CANCELLED = 4


class CoffeeTypes(Enum):
    AMERICANO = 0
    LATTE = 1
    FLAT_WHITE = 2
    CAPPUCCINO = 3


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
# 核心层 · 自定义异常
# ============================================================


class CoffeeMachineFaultError(Exception): ...


class CoffeeMachineAlreadyWorkingError(Exception): ...


class CoffeeMachineNotTurnOn(Exception): ...


class InsufficientCoffeeBeansError(Exception): ...


class CoffeeBeanOverflowError(Exception): ...


class OrderNotFoundError(Exception): ...


# ============================================================
# 核心层 · Ports（抽象接口）
# ============================================================


class CoffeeMachineRepository(ABC):
    @abstractmethod
    def save(self, cm: CoffeeMachine) -> bool: ...

    @abstractmethod
    def get_all(self) -> list[CoffeeMachine]: ...


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> bool: ...

    @abstractmethod
    def get_all(self) -> list[Order]: ...

    @abstractmethod
    def get_one(self, id: int) -> Order | None: ...


# ============================================================
# 核心层 · 业务服务
# ============================================================

COFFEE_BEANS_PER_CUP = 15.0
CLEAN_THRESHOLD = 5
MAX_CAPACITY = 500.0


class CoffeeMachineService:
    def __init__(self, repo: CoffeeMachineRepository):
        self._repo = repo
        self._machines = repo.get_all()

    def get_all(self) -> list[CoffeeMachine]:
        self._machines = self._repo.get_all()
        return self._machines

    def make_coffee(self, index: int, waiting_time: int) -> bool:
        machines = self.get_all()
        if index < 0 or index >= len(machines):
            raise CoffeeMachineNotFoundError()
        cm = machines[index]

        if cm.status == CoffeeMachineStatus.FAULT:
            raise CoffeeMachineFaultError()
        if cm.status == CoffeeMachineStatus.WORKING:
            raise CoffeeMachineAlreadyWorkingError()
        if cm.status == CoffeeMachineStatus.HIBERNATION:
            raise CoffeeMachineNotTurnOn()
        if cm.capacity < COFFEE_BEANS_PER_CUP:
            raise InsufficientCoffeeBeansError()

        cm.capacity -= COFFEE_BEANS_PER_CUP
        cm.status = CoffeeMachineStatus.WORKING
        cm.create_at = waiting_time
        self._repo.save(cm)
        return True

    def change_status(self, index: int, status: CoffeeMachineStatus) -> bool:
        machines = self.get_all()
        if index < 0 or index >= len(machines):
            return False
        machines[index].status = status
        self._repo.save(machines[index])
        return True

    def increace_consecutive_count(self, index: int) -> int:
        machines = self.get_all()
        machines[index].consecutive_count += 1
        self._repo.save(machines[index])
        return machines[index].consecutive_count

    def add_beans(self, index: int, grams: float) -> int:
        machines = self.get_all()
        if index < 0 or index >= len(machines):
            raise CoffeeMachineNotFoundError()
        cm = machines[index]
        if cm.capacity + grams > MAX_CAPACITY:
            raise CoffeeBeanOverflowError()
        cm.capacity += grams
        self._repo.save(cm)
        return int(cm.capacity)

    def clean(self, index: int) -> bool:
        machines = self.get_all()
        machines[index].consecutive_count = 0
        self._repo.save(machines[index])
        return True


class CoffeeMachineNotFoundError(Exception): ...


class OrderService:
    def __init__(self, repo: OrderRepository):
        self._repo = repo

    def create(self, name: str, coffee_type: CoffeeTypes) -> Order:
        order = Order(customer_name=name, coffee_type=coffee_type)
        self._repo.save(order)
        return order

    def change_status(self, order_id: int, status: OrderStatus) -> bool:
        order = self._repo.get_one(order_id)
        if order is None:
            raise OrderNotFoundError()
        order.status = status
        self._repo.save(order)
        return True

    def get_all(self) -> list[Order]:
        return self._repo.get_all()

    def get_one(self, order_id: int) -> Order | None:
        return self._repo.get_one(order_id)


# ============================================================
# 适配器层 · 内存仓库
# ============================================================


class MemoryCoffeeMachineRepository(CoffeeMachineRepository):
    def __init__(self):
        self._storage: list[CoffeeMachine] = []

    def save(self, cm: CoffeeMachine) -> bool:
        for i, m in enumerate(self._storage):
            if m._serial_number == cm._serial_number:
                self._storage[i] = cm
                return True
        self._storage.append(cm)
        return True

    def get_all(self) -> list[CoffeeMachine]:
        return self._storage.copy()


class MemoryOrderRepository(OrderRepository):
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
# 适配器层 · ViewModel + View（CLI 终端）
# ============================================================


class CoffeeMachineViewModel:
    """协调 Service 和 View，处理用户操作流程"""

    def __init__(self, cm_service: CoffeeMachineService, order_service: OrderService):
        self._cm_service = cm_service
        self._order_service = order_service

    async def make_coffee(self, index: int, waiting_time: int, coffee_type: CoffeeTypes, name: str) -> bool:
        machines = self._cm_service.get_all()
        if index < 0 or index >= len(machines):
            print("❌ 咖啡机不存在")
            return False

        cm = machines[index]
        if cm.status != CoffeeMachineStatus.IDLE:
            msg = {
                CoffeeMachineStatus.FAULT: "☠️ 咖啡机故障中！",
                CoffeeMachineStatus.WORKING: "⚙️ 咖啡机正在工作中～",
                CoffeeMachineStatus.HIBERNATION: "💤 咖啡机休眠中，请先开机！",
            }.get(cm.status, "未知状态")
            print(msg)
            return False

        try:
            self._cm_service.make_coffee(index, waiting_time)
        except InsufficientCoffeeBeansError:
            print(f"🌱 咖啡豆不足！当前 {cm.capacity:.1f}g，需要 {COFFEE_BEANS_PER_CUP:.1f}g")
            return False
        except (CoffeeMachineFaultError, CoffeeMachineAlreadyWorkingError, CoffeeMachineNotTurnOn) as e:
            print(f"❌ {e}")
            return False

        order = self._order_service.create(name, coffee_type)
        self._order_service.change_status(order.id, OrderStatus.IN_PRODUCTION)  # type:ignore
        print(f"☕ 正在制作 {coffee_type.name}... 预计 {waiting_time} 秒")

        await asyncio.sleep(waiting_time)

        self._order_service.change_status(order.id, OrderStatus.AWAITING_PICKUP)  # type:ignore
        count = self._cm_service.increace_consecutive_count(index)
        self._cm_service.change_status(index, CoffeeMachineStatus.IDLE)

        if count >= CLEAN_THRESHOLD:
            print(f"🧹 清洁提醒！咖啡机 [{cm._serial_number}] 已连续制作 {count} 杯！")

        print(f"✅ {coffee_type.name} 制作完成！{name} 请取餐～")
        return True


class CoffeeShopView:
    """CLI 终端界面"""

    def __init__(self, vm: CoffeeMachineViewModel, order_service: OrderService, enter: Callable, output: Callable):
        self._vm = vm
        self._order_service = order_service
        self._enter = enter
        self._output = output

    def show_machines(self) -> int | None:
        machines = self._vm._cm_service.get_all()
        self._output("\n=== 咖啡机列表 ===")
        for i, cm in enumerate(machines):
            icons = {
                CoffeeMachineStatus.IDLE: "🟢",
                CoffeeMachineStatus.WORKING: "🟡",
                CoffeeMachineStatus.HIBERNATION: "🔴",
                CoffeeMachineStatus.FAULT: "💀",
            }
            self._output(
                f"  [{i}] {icons.get(cm.status, '❓')} {cm._serial_number} | {cm.status.name} | 豆: {cm.capacity:.0f}g"
            )
        return self._choose_machine(len(machines))

    def _choose_machine(self, count: int) -> int | None:
        try:
            idx = int(self._enter("选择咖啡机编号: "))
            if idx < 0 or idx >= count:
                self._output("❌ 编号超出范围！")
                return None
            return idx
        except ValueError:
            self._output("❌ 请输入数字！")
            return None

    def make_coffee_flow(self):
        idx = self.show_machines()
        if idx is None:
            return
        self._output("\n=== 咖啡种类 ===")
        for t in CoffeeTypes:
            self._output(f"  [{t.value}] {t.name}")
        try:
            type_val = int(self._enter("选择咖啡种类: "))
            coffee_type = CoffeeTypes(type_val)
            waiting = int(self._enter("制作时间(秒): "))
            name = self._enter("顾客姓名: ").strip()
            if not name:
                self._output("❌ 姓名不能为空！")
                return
            asyncio.create_task(self._vm.make_coffee(idx, waiting, coffee_type, name))
        except (ValueError, KeyError):
            self._output("❌ 无效输入！")

    def finish_order(self):
        orders = self._order_service.get_all()
        self._output("\n=== 订单列表 ===")
        icons = {
            OrderStatus.TO_BE_PRODUCTED: "📋",
            OrderStatus.IN_PRODUCTION: "⚙️",
            OrderStatus.AWAITING_PICKUP: "📦",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌",
        }
        for o in orders:
            self._output(
                f"  {icons.get(o.status, '❓')} #{o.id} {o.customer_name} {o.coffee_type.name} {o.status.name}"
            )
        try:
            oid = int(self._enter("完成订单编号: "))
            order = self._order_service.get_one(oid)
            if order is None:
                self._output("❌ 订单不存在")
                return
            if order.status == OrderStatus.IN_PRODUCTION:
                self._output("⏳ 订单制作中，请稍候～")
                return
            if order.status == OrderStatus.CANCELLED:
                self._output("❌ 订单已取消")
                return
            self._order_service.change_status(oid, OrderStatus.COMPLETED)
            self._output(f"✅ 订单 #{oid} 已完成！")
        except ValueError:
            self._output("❌ 请输入数字！")


# ============================================================
# 组装（Wiring）— 所有依赖在这里注入
# ============================================================


async def main():
    cm_repo = MemoryCoffeeMachineRepository()
    order_repo = MemoryOrderRepository()

    for m in [
        CoffeeMachine("CM-001", 30, 0, 0, 200.0, CoffeeMachineStatus.IDLE),
        CoffeeMachine("CM-002", 25, 0, 0, 150.0, CoffeeMachineStatus.IDLE),
        CoffeeMachine("CM-003", 20, 0, 0, 100.0, CoffeeMachineStatus.HIBERNATION),
    ]:
        cm_repo.save(m)

    cm_svc = CoffeeMachineService(cm_repo)
    order_svc = OrderService(order_repo)
    vm = CoffeeMachineViewModel(cm_svc, order_svc)
    view = CoffeeShopView(vm, order_svc, input, print)

    print("☕ 咖啡店管理系统（六边形架构版）")

    while True:
        print("\n[1] 制作咖啡  [2]查看订单  [3]完成订单  [0]退出")
        choice = input("选择: ").strip()

        if choice == "1":
            view.make_coffee_flow()
            await asyncio.sleep(0.1)
        elif choice == "2":
            for o in order_svc.get_all():
                print(f"  #{o.id} {o.customer_name} {o.coffee_type.name} {o.status.name}")
        elif choice == "3":
            view.finish_order()
        elif choice == "0":
            print("👋 再见！")
            break


"""
==========================
📐 学完本课你应该掌握：

1. 六边形的"内外"划分
   ─ 内层：领域模型、Ports 接口、业务 Service
   ─ 外层：Repository 实现、View 实现

2. 依赖反转
   ─ Service 不 import 具体仓库，只 import 接口
   ─ main.py 负责组装（Dependency Injection）

3. 可测试性
   ─ 想测 Service？传入 MemoryRepository 就行，零配置
   ─ 想换数据库？写一个新 Adapter 实现 Ports 接口就行

4. 可替换性
   ─ CLI View 可以换成 Web View，Service 和 Repository 不用改
   ─ 内存仓库可以换成 MySQL 仓库，Service 和 View 不用改
"""


if __name__ == "__main__":
    asyncio.run(main())
