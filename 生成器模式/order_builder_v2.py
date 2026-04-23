from dataclasses import dataclass, field
import copy

LATEST_ORDER_ID = 0
ITEMS = [
    {"name": "铅笔", "price": 2},
    {"name": "笔记本电脑", "price": 7500},
    {"name": "可乐", "price": 3.5},
]


def generate_order_id() -> int:
    global LATEST_ORDER_ID
    LATEST_ORDER_ID += 1
    return LATEST_ORDER_ID


def get_price(item_list: list[int]) -> list[float]:
    return [
        ITEMS[item_id]["price"] for item_id in item_list if 0 <= item_id < len(ITEMS)
    ]


@dataclass(slots=True)
class Order:
    """产品：要构建的复杂对象"""

    id: int = field(default_factory=generate_order_id)
    address: str | None = None
    price: float | None = None
    item_list: list[int] = field(default_factory=list)

    def count_price(self) -> None:
        self.price = sum(get_price(self.item_list))

    def __str__(self):
        return "\n".join(f"{value}: {getattr(self, value)}" for value in self.__slots__)


@dataclass(slots=True)
class OrderBuilder(Order):
    def set_address(self, address: str) -> "OrderBuilder":
        self.address = address
        return self

    def add_item(self, item_id: int) -> "OrderBuilder":
        self.item_list.append(item_id)
        return self

    def get_order(self) -> Order:
        self.count_price()
        if not all(getattr(self, value) for value in self.__slots__):
            raise ValueError
        return Order(
            address=self.address,
            price=self.price,
            item_list=copy.deepcopy(self.item_list),
        )


def main():
    order = OrderBuilder().set_address("北京").add_item(0).add_item(1).get_order()
    print(order)


if __name__ == "__main__":
    main()
