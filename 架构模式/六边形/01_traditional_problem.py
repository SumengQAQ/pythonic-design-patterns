"""
==========================
六边形架构 · Lesson 1 — 传统分层架构的痛点
==========================

「分层架构（Layered Architecture）」是我们最熟悉的架构：
Controller → Service → Repository → Database

看起来很美，但实际用起来有很多坑……
"""

import sqlite3
from dataclasses import dataclass
from enum import Enum, auto


class CoffeeMachineStatus(Enum):
    IDLE = auto()
    WORKING = auto()
    HIBERNATION = auto()
    FAULT = auto()


@dataclass
class CoffeeMachine:
    serial_number: str
    capacity: float
    status: CoffeeMachineStatus = CoffeeMachineStatus.HIBERNATION
    consecutive_count: int = 0


# ============================================================
# ❌ 传统三层：Service 层
# ============================================================

# 问题 1：Service 直接依赖具体数据库实现


class CoffeeMachineService:
    """
    业务逻辑 —— 表面上很干净，实际上已和数据库绑定。

    如果哪天你想从 SQLite 换成 PostgreSQL，或者从 Django ORM
    换成 SQLAlchemy，这个类必须改。
    """

    def __init__(self):
        # ❌ 直接依赖具体数据库！
        self._db = sqlite3.connect("coffee_shop.db")
        self._db.execute("CREATE TABLE IF NOT EXISTS machines (...)")

    def make_coffee(self, machine_id: str) -> bool:
        # ❌ SQL 查询散落在业务代码中
        cursor = self._db.execute("SELECT capacity, status FROM machines WHERE id = ?", (machine_id,))
        row = cursor.fetchone()
        if not row:
            return False

        capacity, status = row

        if status != "IDLE":
            return False

        # ❌ 业务逻辑和数据库操作混在一起
        if capacity < 15.0:
            return False

        self._db.execute(
            "UPDATE machines SET capacity = capacity - 15.0, status = 'WORKING' WHERE id = ?",
            (machine_id,),
        )
        return True


# ============================================================
# ❌ 问题 2：Service 直接调用 print() / input()
# ============================================================

class CoffeeMachineService2:
    """业务层居然直接调 print？换 GUI 就废了"""

    def make_coffee(self, machine_id: str) -> bool:
        # ... 业务逻辑 ...
        print("☕ 咖啡机制作中！")  # ❌❌❌ 业务层不该知道 print 的存在！
        return True


# ============================================================
# ❌ 问题 3：单元测试困难
# ============================================================

"""
你想测试 CoffeeMachineService.make_coffee()：

  1. 需要有一个真实的数据库（SQLite 文件）
  2. 测试前要插入数据
  3. 测试后要清理
  4. 如果使用 Django ORM，还要加载整个 Django 框架！
  5. 测试速度慢 —— 读写磁盘

这就是分层架构的"隐式耦合"——
分层只解决了代码组织问题，没解决依赖方向问题。
"""

# ============================================================
# ⚡ 总结：三个致命问题
# ============================================================

"""
1️⃣ 依赖方向错误 — 高层业务依赖低层数据库，而不是反过来
2️⃣ 副作用散落 — print/input/数据库查询散落在业务代码中
3️⃣ 测试困难 — 测业务逻辑必须先搭基础设施

六边形架构就是来解决这三个问题的。
下节课见！👉 02_ports_and_adapters.py
"""
