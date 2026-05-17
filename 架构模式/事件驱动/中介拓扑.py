from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Callable, ClassVar, Type
import functools
import asyncio
import time


@dataclass
class User:
    id: str
    name: str
    email: str


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

        EventBus.register(cls, wrapper)
        return wrapper


@dataclass
class UserRegisteredEvent(BaseEvent, semaphore_num=3):
    user: User


@dataclass
class ErrorEvent(BaseEvent, semaphore_num=10):
    exceptions: list[BaseException]


class EventBus:
    _events: dict[Type[BaseEvent], list[Callable]] = defaultdict(list)

    @classmethod
    def register(cls, event: Type[BaseEvent], callback: Callable) -> None:
        cls._events[event].append(callback)

    @classmethod
    async def emit(cls, event: BaseEvent) -> None:
        tasks = [asyncio.create_task(callback(event)) for callback in cls._events[type(event)]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        exceptions = list(filter(lambda x: x, results))
        if not exceptions:
            return
        await EventBus.emit(ErrorEvent(exceptions))


@ErrorEvent.register
async def error_handler(event: ErrorEvent):
    try:
        for exception in event.exceptions:
            await asyncio.sleep(0.5)
            print(f"❌ {type(exception).__name__}：{exception}")
    except Exception as e:
        print(f"❌ 处理错误时发生了意外错误{type(e).__name__}：{e}")


@UserRegisteredEvent.register
async def email_notifier(event: UserRegisteredEvent):
    await asyncio.sleep(1)
    print(f"📧 发送邮件给 {event.user.name}({event.user.email})")


@UserRegisteredEvent.register
async def welcome_coupon_issuer(event: UserRegisteredEvent):
    await asyncio.sleep(0.5)
    print(f"🎉 发放欢迎优惠券给 {event.user.name}")


@UserRegisteredEvent.register
async def analytics_tracker(event: UserRegisteredEvent):
    await asyncio.sleep(2)
    print(f"📊 记录注册事件：{event.user.name}({event.user.id})")


async def main():
    user = User(id="123456", name="塑梦", email="sumeng@example.com")
    await EventBus.emit(UserRegisteredEvent(user))


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"⏱  耗时{end - start:.2f}")
