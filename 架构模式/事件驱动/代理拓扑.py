from __future__ import annotations
from collections import defaultdict
from typing import Callable, ClassVar, Type
from dataclasses import dataclass
import functools
import asyncio
import time


@dataclass
class BaseEvent:
    _semaphore: ClassVar[asyncio.Semaphore]

    def __init_subclass__(cls, semaphore_num: int) -> None:
        cls._semaphore = asyncio.Semaphore(semaphore_num)

    @classmethod
    def register(cls, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with cls._semaphore:
                await func(*args, **kwargs)

        EVENT_CALLBACK[cls].append(wrapper)
        return wrapper


@dataclass
class User:
    id: str
    name: str
    email: str


@dataclass
class UserRegisteredEvent(BaseEvent, semaphore_num=3):
    user: User


EVENT_CALLBACK = defaultdict(list)


@UserRegisteredEvent.register
async def email_notifier(event: UserRegisteredEvent):
    await asyncio.sleep(2)
    print(f"📧 发送邮件给 {event.user.name}({event.user.email})")


@UserRegisteredEvent.register
async def welcome_coupon_issuer(event: UserRegisteredEvent):
    await asyncio.sleep(1)
    print(f"🎉 发放欢迎优惠券给 {event.user.name}")


@UserRegisteredEvent.register
async def analytics_tracker(event: UserRegisteredEvent):
    await asyncio.sleep(0.5)
    print(f"📊 记录注册事件：{event.user.name}({event.user.id})")


class UserRegisteredWorker:
    handlers: list[Callable] = []
    _tasks: list[asyncio.Task]

    @classmethod
    def set_handlers(cls, handlers):
        cls.handlers = handlers
        return cls

    @classmethod
    async def start_work(cls, worker_num: int):
        cls._tasks = [
            asyncio.create_task(
                cls.worker(BrokerHandler.event_queues[UserRegisteredEvent])
            )
            for _ in range(worker_num)
        ]
        await asyncio.gather(*cls._tasks)

    @classmethod
    async def worker(cls, queue: asyncio.Queue):
        while True:
            event = await queue.get()
            if event is None:
                break
            await asyncio.gather(*[h(event) for h in cls.handlers])


class BrokerHandler:
    event_queues: ClassVar[dict[Type[BaseEvent], asyncio.Queue]] = defaultdict(
        asyncio.Queue
    )

    @classmethod
    async def emit(cls, event: BaseEvent):
        await cls.event_queues[type(event)].put(event)

    @classmethod
    async def close(cls, event_type: Type[BaseEvent], worker_num: int):
        for _ in range(worker_num):
            await cls.event_queues[event_type].put(None)


async def main():
    worker_num = 2
    users = [
        User(id="123456", name="塑梦", email="sumeng@example.com"),
        User(id="789012", name="虚幻", email="xuhuan@example.com"),
    ]
    UserRegisteredWorker.set_handlers(EVENT_CALLBACK[UserRegisteredEvent])
    worker_task = asyncio.create_task(
        UserRegisteredWorker.start_work(worker_num)
    )
    for user in users:
        await BrokerHandler.emit(UserRegisteredEvent(user))
    await BrokerHandler.close(UserRegisteredEvent, worker_num)
    await worker_task


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"⏱  耗时{end - start:.2f}")
