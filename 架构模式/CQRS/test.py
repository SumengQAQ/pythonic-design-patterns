from pathlib import Path
from decimal import Decimal
import pytest
from sqlmodel import create_engine, SQLModel
from .command import Item, Order
from .query import OrderDetail


@pytest.fixture(scope="session")
def init_database():
    database_path = Path(__file__).parent / "test.db"
    engine = create_engine(f"sqlite:///{database_path}")
    SQLModel.metadata.create_all(engine)
    yield
    database_path.unlink(missing_ok=True)


def test_insert_items(init_database):
    coffee = Item.create_and_restock(name='coffee', price=Decimal(15), count=12)
    water = Item.create_and_restock(name='water', price=Decimal(3), count=5)
    assert Item.get_by_name(coffee.name) == coffee
    assert Item.get_by_name(water.name) == water


def test_create_order(init_database):
    order = Order.create([Item.get_by_name('coffee', 5), Item.get_by_name('water', 3)])
    assert Order.get_by_id(order.id) == order


def test_get_order_detail(init_database):
    assert OrderDetail.get_by_id(1)
    assert OrderDetail.get_by_id(1).total_item_price == Decimal(15 * 5 + 3 * 3)
