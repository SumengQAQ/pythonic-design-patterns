## 一、故事：从一把锁开始

想象你开了一个社区网站。用户注册后需要：

1. 发一封欢迎邮件（耗时 2 秒）
2. 发一张新人优惠券（耗时 1 秒）
3. 记录注册行为到分析系统（耗时 0.5 秒）

最粗暴的写法：

```python
def register_user(name, email):
    save_to_db(name, email)
    send_email(name, email)        # 等 2 秒
    issue_coupon(name)             # 再等 1 秒
    track_analytics(name)          # 再等 0.5 秒
```

一个注册请求卡 3.5 秒——用户等得想摔键盘。

## 二、第一次进化：异步 + 并发

用协程让三个操作**同时跑**，而不是依次跑：

```python
async def register_user(name, email):
    user = await save_to_db(name, email)
    await asyncio.gather(
        send_email(user),        # 2 秒
        issue_coupon(user),      # 1 秒
        track_analytics(user),   # 0.5 秒
    )
    # 总耗时 ≈ 2 秒（取最慢的）
```

好了一些，但这把业务逻辑硬编码在注册流程里了。每加一个新功能就要改 `register_user` 核心函数。

所以我们需要**事件驱动架构**。

## 三、事件驱动的核心思想

> **"发生了某事"和"怎么处理它"分开。**

注册成功只管发一个 `UserRegisteredEvent`，不关心谁在处理。加功能就加新处理器——不碰原来的代码。

```
注册成功 → UserRegisteredEvent
               ↓
          发邮件（2 秒）
          发优惠券（1 秒）
          记录分析（0.5 秒）
```

## 四、版本一：中介拓扑（Mediator Topology）

### 4.1 设计思路

一个中心化的 `EventBus` 管理事件和处理器之间的映射。

```
发布者 → EventBus（中心调度器） → 处理器 A
                               → 处理器 B
                               → 处理器 C
```

### 4.2 定义领域对象

```python
@dataclass
class User:
    id: str
    name: str
    email: str
```

### 4.3 设计 BaseEvent 与 **init_subclass**

处理器需要限流——同一事件不能无限制并发。但**限流是事件级别的，不是处理器级别的**。三个处理器应该共享同一个事件类型的信号量，而不是各自声明。

最自然的做法：让每个事件子类在定义时自动获得一个独立的信号量。

```python
@dataclass
class BaseEvent:
    _semaphore: ClassVar[asyncio.Semaphore]

    def __init_subclass__(cls, semaphore_num: int = 3) -> None:
        cls._semaphore = asyncio.Semaphore(semaphore_num)
```

`__init_subclass__` 是 Python 3.6（PEP 487）引入的特性——当一个类继承了 `BaseEvent` 时，`__init_subclass__` 自动调用。这里的作用是：**每个事件子类被定义时自动创建自己的信号量**。

```python
@dataclass
class UserRegisteredEvent(BaseEvent, semaphore_num=3):
    user: User
```

`UserRegisteredEvent` 被定义时，`__init_subclass__` 执行 `cls._semaphore = asyncio.Semaphore(3)`。

为什么不用每个处理器自己写 `async with asyncio.Semaphore(3)`？

因为如果三个处理器各自声明信号量，每个限制并发为 3，那一个事件最多可以有 3×3 = 9 个并发执行，和"限制这个事件最多 3 个并发"的预期不符。

### 4.4 装饰器注册到 EventBus

```python
@classmethod
def register(cls, func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with cls._semaphore:
            await func(*args, **kwargs)
    EventBus.register(cls, wrapper)
    return wrapper
```

`register` 做了两件事：

1. 用 `cls._semaphore` 包装原函数——执行时获取信号量
2. 把包装后的函数注册到 `EventBus`——EventBus 知道"这个事件有这个处理器"

```python
@UserRegisteredEvent.register
async def email_notifier(event: UserRegisteredEvent):
    await asyncio.sleep(2)
    print(f"📧 发送邮件给 {event.user.name}({event.user.email})")
```

### 4.5 EventBus

```python
class EventBus:
    _events: dict[Type[BaseEvent], list[Callable]] = defaultdict(list)

    @classmethod
    def register(cls, event: Type[BaseEvent], callback: Callable) -> None:
        cls._events[event].append(callback)

    @classmethod
    async def emit(cls, event: BaseEvent) -> None:
        tasks = [
            asyncio.create_task(callback(event))
            for callback in cls._events[type(event)]
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        exceptions = [r for r in results if r]
        if exceptions: await cls.emit(ErrorEvent(exceptions))
```

`emit` 用 `gather` 并发执行所有处理器，并用 `return_exceptions=True` 捕获异常——如果有处理器挂了，触发新的 `ErrorEvent`，不影响其他处理器。

### 4.6 错误也是事件

```python
@dataclass
class ErrorEvent(BaseEvent, semaphore_num=10):
    exceptions: list[BaseException]

@ErrorEvent.register
async def error_handler(event: ErrorEvent):
    for exception in event.exceptions:
        await asyncio.sleep(0.5)
        print(f"❌ {type(exception).__name__}：{exception}")
```

错误本身也是一个事件。**EventBus 发现 gather 返回了异常时，自动 emit ErrorEvent**。错误处理和其他业务逻辑在架构级别是对等的——同一个 EventBus 调度，同样的信号量限流。

### 4.7 运行

```python
async def main():
    user = User(id="123456", name="塑梦", email="sumeng@example.com")
    await EventBus.emit(UserRegisteredEvent(user))

# 输出：
# 📊 记录注册事件：塑梦(123456)
# 🎉 发放欢迎优惠券给 塑梦
# 📧 发送邮件给 塑梦(sumeng@example.com)
# ⏱  耗时 2.01 秒
```

三个处理器并发执行，总耗时 ≈ 最慢的那个（2 秒）。

### 4.8 中介拓扑的局限

EventBus 直接调处理器，没有缓冲区。瞬间来 10000 个事件就创建 10000×3 个 Task，没有削峰能力。

## 五、版本二：代理拓扑（Broker Topology）

### 5.1 设计思路

在发布者和处理器之间加一层**消息队列**解耦，事件先入队，Worker 从队列取事件执行。

```
发布者 → 队列 → Worker 1 → 处理器 A,B,C
              → Worker 2 → 处理器 A,B,C
```

### 5.2 注册目标变了

中介拓扑里，装饰器注册到 `EventBus`：

```python
EventBus.register(cls, wrapper)
```

代理拓扑里，装饰器注册到全局字典 `EVENT_CALLBACK`：

```python
EVENT_CALLBACK[cls].append(wrapper)
```

为什么变？**因为代理拓扑中没有中心 EventBus 了。** 事件不经过 EventBus 调度，直接入队列。但"声明处理器"的机制应该保留——所以把注册目标从 EventBus 改为一个纯粹的注册表（`EVENT_CALLBACK` 字典），Worker 再去注册表里读取处理器列表。

**注册机制不变，变化的是谁去读注册表。**

### 5.3 Worker 与处理器注入

```python
class UserRegisteredWorker:
    handlers: list[Callable] = []

    @classmethod
    def set_handlers(cls, handlers):
        cls.handlers = handlers
        return cls

    @classmethod
    async def worker(cls, queue: asyncio.Queue):
        while True:
            event = await queue.get()
            if event is None: break
            await asyncio.gather(*[h(event) for h in cls.handlers])
```

Worker 只做两件事：从队列拿事件，然后对 `handlers` 里的每个函数并发执行。

`handlers` 列表在 `main()` 里通过 `set_handlers` 注入——控制反转，Worker 不自己去查列表，调用方告诉它"你该执行这些"。

### 5.4 结束信号的坑

```python
@classmethod
async def close(cls, event_type: Type[BaseEvent], worker_num: int):
    for _ in range(worker_num):
        await cls.event_queues[event_type].put(None)
```

用 `None` 通知 Worker 退出。**结束信号的数量必须等于 Worker 数**——少放一个就有一个 Worker 永远在等 `queue.get()`，程序卡死。第一个版本我就在这里栽了。

### 5.5 运行

```python
async def main():
    worker_num = 2
    users = [
        User(id="123456", name="塑梦", email="sumeng@example.com"),
        User(id="789012", name="虚幻", email="xuhuan@example.com"),
    ]
    UserRegisteredWorker.set_handlers(EVENT_CALLBACK[UserRegisteredEvent])
    worker_task = asyncio.create_task(UserRegisteredWorker.start_work(worker_num))
    for user in users:
        await BrokerHandler.emit(UserRegisteredEvent(user))
    await BrokerHandler.close(UserRegisteredEvent, worker_num)
    await worker_task

# 输出：
# 📊 记录注册事件：塑梦(123456)
# 🎉 发放欢迎优惠券给 塑梦
# 📧 发送邮件给 塑梦(sumeng@example.com)
# 📊 记录注册事件：虚幻(789012)
# 🎉 发放欢迎优惠券给 虚幻
# 📧 发送邮件给 虚幻(xuhuan@example.com)
# ⏱  耗时 2.50 秒
```

两个 Worker 同时处理两个事件。

## 六、对比与选择

| 维度       | 中介拓扑                     | 代理拓扑               |
| ---------- | ---------------------------- | ---------------------- |
| 中心组件   | EventBus                     | 消息队列               |
| 注册目标   | `EventBus._events`           | `EVENT_CALLBACK` 字典  |
| 限流机制   | `__init_subclass__` + 信号量 | 同左（共享 BaseEvent） |
| 处理器调度 | EventBus 直接 gather         | Worker 内 gather       |
| 削峰能力   | 无                           | 有（队列缓冲）         |
| 容错性     | ErrorEvent 兜底              | Worker 独立，互不影响  |
| 代码量     | ~50 行核心                   | ~80 行核心             |

**一句话选择**：不需要削峰时中介拓扑够了。需要高可靠性和解耦时上代理拓扑。

## 七、为什么协程是事件驱动的基础

发邮件等网络、发券查数据库、埋点写日志——都涉及 I/O 等待。

协程的 `await` 解决这个问题：在等待时让出控制权，事件循环去跑别的处理器。

```python
async def email_notifier(event):
    await asyncio.sleep(2)         # 让出控制权
    # 2 秒后回来继续

# 三个 await 操作的等待时间被事件循环利用
# 1000 个并发 = 1000 个协程 = 1 个线程
```

没有协程的话每个 I/O 等待都要一个线程——1000 个并发 = 1000 个线程，线程切换开销远大于协程。

## 八、总结

事件驱动 = 发布 - 订阅。代码走到某处"大喊一声"，不关心谁在听。

`__init_subclass__` 让每个事件子类自动获得独立信号量，`register` 装饰器统一处理注册和限流，`ErrorEvent` 本身也是 EventBus 上的一个普通事件——这些设计让核心代码不到 50 行。

你会发现很多框架在用同样的思路：

- **Flask/FastAPI 路由** → 中介拓扑
- **Celery 任务队列** → 代理拓扑
- **Vue $emit / React 事件** → 中介拓扑

## 九、别以为很简单

看到这里你可能觉得：就这？几十行代码的事？

但实际上这只是**最最最核心的骨架**。生产级的事件驱动系统还要补一堆东西，想到就头疼 😭

```
现在的代码：事件 → 处理 → 完事
生产级的：事件 → 反序列化 → 校验 → 幂等检查 →
          处理 → 重试(3次) → 死信队列 → 报警 →
          回滚补偿 → 分布式事务 → 链路追踪
```

说几个让人崩溃的场景：

- **处理器挂了怎么办**——现在 `gather` 里一个炸了虽然不影响其他的，但炸掉的那个操作就这样丢了吗？要不要重试？
- **重试还失败怎么办**——要不要扔死信队列？要不要告警？
- **队列里的事件处理到一半服务重启了**——那些事件是丢了还是等恢复后再处理？
- **同一个事件被重复投递**——你的邮箱可能会收到 5 封一样的欢迎邮件。幂等性怎么保证？
- **回滚怎么搞**——邮件发出去了，但优惠券发放失败了。邮件能撤回吗？（不能）要不要补偿机制？
- **多个服务之间怎么追踪一个事件的完整链路**——事件从注册服务发到通知服务，再到分析服务，中间跨了三个进程，出问题了怎么查？

这些才是生产级事件驱动的真正复杂度。你现在看到的几十行玩具代码，只是冰山浮在水面上的那个尖尖。

但没有一步到位的架构。先跑通核心流程，量大了再加削峰，出问题了再加重试，搞崩了再加回滚——**架构从来不是设计出来的，是事故堆出来的** (´;ω;｀)
