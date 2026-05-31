from sqlmodel import Session
from .model import OrderDetail


class QueryRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_order_detail(self, order_detail: OrderDetail):
        self.session.add(order_detail)

    def get_order_detail_by_id(self, id: int) -> OrderDetail | None:
        return self.session.get(OrderDetail, id)
