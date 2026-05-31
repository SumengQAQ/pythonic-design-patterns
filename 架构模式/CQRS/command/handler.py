from sqlmodel import Session, select
from .model import Item, Order


class CommandRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_item(self, item: Item):
        self.session.add(item)

    def get_item_by_name(self, name: str) -> Item | None:
        item = self.session.exec(select(Item).where(Item.name == name)).first()
        return item

    def save_order(self, order: Order):
        self.session.add(order)

    def get_order_by_id(self, order_id: int) -> Order | None:
        order = self.session.get(Order, order_id)
        return order
