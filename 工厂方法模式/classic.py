class Police:
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.weight = weight

    def draw(self):
        print(f"name: {self.name}, age: {self.age}, weight: {self.weight} kg")


class Car:
    def __init__(self, type, weight):
        self.type = type
        self.weight = weight

    def draw(self):
        print(f"type: {self.type}, weight: {self.weight} kg")


# 使用
Police("Mr.Green", 30, 70).draw()
Car("Car", 1200).draw()
