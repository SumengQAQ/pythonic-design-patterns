from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field, Column, JSON
from ..command import Item
from ..event_bus import AddedItemsToOrderEvent
from ..unit_of_work import UnitOfWork


class OrderDetail(SQLModel, table=True):
    order_id: int = Field(primary_key=True)
    items: list[Item] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    total_item_count: int = Field(default=0)
    total_item_price: Decimal = Field(default_factory=Decimal)
    average_item_price: Decimal = Field(default_factory=Decimal)

    @staticmethod
    @AddedItemsToOrderEvent.register
    def update(event: AddedItemsToOrderEvent) -> None:
        order_id, item = event.order_id, event.item

        with UnitOfWork() as uow:
            repo = uow.query

            order_detail = repo.get_order_detail_by_id(order_id)
            if not order_detail: order_detail = OrderDetail(order_id=order_id)

            order_detail.items.append(item.to_dict())
            order_detail.total_item_count += item.count
            order_detail.total_item_price += item.price * item.count
            order_detail.average_item_price = order_detail.total_item_price / order_detail.total_item_count
            repo.save_order_detail(order_detail)

    @staticmethod
    def get_by_id(order_id: int) -> "OrderDetail | None":
        with UnitOfWork() as uow:
            repo = uow.query
            return repo.get_order_detail_by_id(order_id)
