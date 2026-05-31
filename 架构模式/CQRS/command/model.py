from sqlmodel import Field, Relationship, SQLModel
from decimal import Decimal
from datetime import datetime

from ..unit_of_work import UnitOfWork
from ..event_bus import EventBus, AddedItemsToOrderEvent


class ItemOrderLink(SQLModel, table=True):
    item_id: int = Field(foreign_key='item.id', primary_key=True)
    order_id: int = Field(foreign_key='order.id', primary_key=True)


class Item(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    price: Decimal
    count: int = Field(default=1)
    orders: list["Order"] = Relationship(back_populates="items", link_model=ItemOrderLink)

    @staticmethod
    def create_and_restock(name: str, price: Decimal, count: int) -> 'Item':
        with UnitOfWork() as uow:
            repo = uow.command
            item = repo.get_item_by_name(name) or Item(name=name, price=price, count=0)
            item.count += count
            repo.save_item(item)
            return item

    @staticmethod
    def get_by_name(name: str, need: int = None) -> "Item | None":

        with UnitOfWork() as uow:
            repo = uow.command
            item = repo.get_item_by_name(name)
            if need:
                if item.count < need: raise ValueError(f'{item.name}库存不足')
                item.count = need
            return item

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count,
            "price": float(self.price)
        }


class Order(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    items: list[Item] = Relationship(back_populates="orders", link_model=ItemOrderLink)
    created_at: datetime = Field(default_factory=datetime.now)

    @staticmethod
    def create(items: list[Item]) -> "Order":
        order = Order()
        for item in items:
            Order.add_item(order=order, item=item)
        return order

    @staticmethod
    def get_by_id(id: int) -> "Order | None":
        with UnitOfWork() as uow:
            repo = uow.command
            return repo.get_order_by_id(id)

    @staticmethod
    def add_item(order: "Order", item: Item) -> "Order":
        with UnitOfWork() as uow:
            repo = uow.command
            order.items.append(item)
            repo.save_order(order)

        EventBus.emit(AddedItemsToOrderEvent(order.id, item))
        return order
