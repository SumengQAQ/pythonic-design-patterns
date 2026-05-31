from __future__ import annotations
from typing import Callable, Type, TYPE_CHECKING, NamedTuple
from collections import defaultdict
from dataclasses import dataclass

if TYPE_CHECKING:
    from .command import Item


class EventBus:
    event: dict[str, list[Callable[[BaseEvent], None]]] = defaultdict(list)

    @classmethod
    def register(cls, event: Type[BaseEvent], func: Callable[[BaseEvent], None]):
        cls.event[event.__name__].append(func)

    @classmethod
    def emit(cls, event: BaseEvent):
        for func in cls.event[type(event).__name__]:
            func(event)


@dataclass
class BaseEvent:
    @classmethod
    def register(cls, func: Callable[[BaseEvent], None]):
        EventBus.register(cls, func)


@dataclass
class AddedItemsToOrderEvent(BaseEvent):
    # NOTE 直接把当前新增的 item 也加上，做增量
    # 事件的好处就是可以做增量，如果还是全量的话，那不用 CQRS + EDA 也行啊，体现不出来优势了🫠
    order_id: int
    item: Item
