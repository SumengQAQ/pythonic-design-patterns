import copy
from typing import Any
from dataclasses import dataclass, field


@dataclass(slots=True)
class PrototypeManager:
    _prototype_dict: dict = field(default_factory=dict)

    def register(self, prototype_name: str, prototype: Any) -> None:
        """注册原型"""
        self._prototype_dict[prototype_name] = prototype

    def clone(self, prototype_name: str, **kwargs):
        """克隆并微调"""
        obj = copy.deepcopy(self._prototype_dict[prototype_name])
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj


@dataclass(slots=True)
class Enemy:
    name: str
    health: int
    attack: int

    def __str__(self):
        return f"name: {self.name}, health: {self.health}, attack: {self.attack}"


def main():
    manager = PrototypeManager()
    manager.register("goblin", Enemy("哥布林", 50, 10))
    manager.register("dragon", Enemy("龙", 500, 80))

    # 克隆并微调
    boss = manager.clone("dragon", health=800)
    print(boss)


if __name__ == "__main__":
    main()
