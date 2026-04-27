from typing import Callable

DATABASE: dict[str, "Model"] = {}


class Repository:
    @staticmethod
    def add_one(student_name: str, student: "Model"):
        DATABASE[student_name] = student

    @staticmethod
    def get_all() -> dict[str, "Model"]:
        return DATABASE

    @staticmethod
    def get_one(student_name: str) -> "Model":
        return DATABASE[student_name]

    @staticmethod
    def exists(student_name: str) -> bool:
        return student_name in DATABASE


from dataclasses import dataclass, field


@dataclass(slots=True)
class Model:
    name: str
    subject_sorce: dict[str, float] = field(default_factory=dict)


class Service:
    @staticmethod
    def add_student(student_name: str, subject_sorce: dict[str, float]) -> None:
        if Repository.exists(student_name):
            raise KeyError("此学生已存在")
        Repository.add_one(student_name, Model(student_name, subject_sorce))

    @staticmethod
    def get_student(student_name: str) -> "Model":
        if not Repository.exists(student_name):
            raise KeyError("此学生不存在")
        return Repository.get_one(student_name)

    @staticmethod
    def get_all_student() -> dict[str, "Model"]:
        return Repository.get_all()


class ViewModel:
    def __init__(self) -> None:
        self._stduents: dict[str, "Model"] = {}
        self._on_data_change: Callable = lambda: None

    def bind(self, callback: Callable):
        self._on_data_change = callback

    def _refresh(self):
        self._stduents = Service.get_all_student()
        self._on_data_change()

    def add_student(self, student_name: str, subject_sorce: dict):
        Service.add_student(student_name, subject_sorce)
        # TODO: 可以改成增量更新
        self._refresh()

    def average_score(self) -> float:
        """计算所有学生的平均分"""
        all_scores = []
        for student in self._stduents.values():
            all_scores.extend(student.subject_sorce.values())
        return sum(all_scores) / len(all_scores) if all_scores else 0.0

    def top_student(self) -> Model | None:
        """找出总分最高的学生"""
        if not self._stduents:
            return None
        return max(self._stduents.values(), key=lambda s: sum(s.subject_sorce.values()))


class View:
    def __init__(self, view_model: ViewModel) -> None:
        self.view_model = view_model
        self.view_model.bind(self.display_all)

    def add_student(self):
        subject_sorce = {}
        student_name = input("学生姓名")
        while True:
            subject = input("科目")
            if subject == "exit":
                print("已退出")
                break
            sorce = input("成绩")
            subject_sorce[subject] = float(sorce)
        self.view_model.add_student(student_name, subject_sorce)

    def display_all(self):
        for name, student in self.view_model._stduents.items():
            print(f"{name}的成绩是{student.subject_sorce}")


def main():
    view_model = ViewModel()
    view = View(view_model)
    while True:
        action = input("请输入操作：")
        if action == "exit":
            print("已退出")
            break
        if action == "add":
            view.add_student()


if __name__ == "__main__":
    main()
