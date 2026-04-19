# 抽象工厂模式：车辆制造系统

## 🎯 需求描述

你需要设计一个**车辆制造系统**，能够根据不同的车辆类型，生产对应的车身和车轮部件。

### 1. 产品类

- **Body（车身）**
  - 属性：`type`（样式）、`color`（颜色，默认 "White"）
- **Wheel（车轮）**
  - 属性：`type`（样式）、`spoke_count`（辐条数量，默认 12）

### 2. 工厂类

- **抽象工厂 `VehiclePartsFactory`**
  - 定义两个抽象方法：
    - `create_body() -> Body`
    - `create_wheel() -> Wheel`

- **具体工厂 `CarPartsFactory`**
  - 生产小型车的车身（type="Mini"）和车轮（type="Mini"）

- **具体工厂 `TruckPartsFactory`**
  - 生产大型车的车身（type="Heavy"）和车轮（type="Big"）

### 3. 车辆类型枚举

- **`VehicleType`**
  - `CAR = "Car"`
  - `TRUCK = "Truck"`

### 4. 车辆类

- **`Vehicle`**
  - 属性：
    - `name`：车辆名称
    - `type`：车辆类型（`VehicleType` 枚举）
    - `body`：车身对象（可选）
    - `wheel_list`：车轮列表（默认为空）
  - 方法：
    - `run()`：启动车辆。如果缺少车身或车轮，抛出 `ValueError`
    - `__str__()`：返回车辆的描述信息

### 5. 客户端接口

- **函数 `make_vehicle(name: str, vehicle_type: VehicleType, wheel_count: int) -> Vehicle`**
  - 根据传入的车辆类型，选择对应的工厂
  - 创建车身和指定数量的车轮
  - 返回组装好的 `Vehicle` 实例
  - 如果传入未知的车辆类型，抛出 `TypeError`

## 🧪 测试用例

```python
# 创建一辆小型车，4 个轮子
car = make_vehicle("my_car", VehicleType.CAR, 4)
print(car)
car.run()

# 创建一辆卡车，6 个轮子
truck = make_vehicle("my_truck", VehicleType.TRUCK, 6)
print(truck)
truck.run()
```

**预期输出（格式大致如下）：**
```
=== my_car (Car) ===
车身: Mini
车轮:
1. Mini
2. Mini
3. Mini
4. Mini
my_car (Car) 发动了！

=== my_truck (Truck) ===
车身: Heavy
车轮:
1. Big
2. Big
3. Big
4. Big
5. Big
6. Big
my_truck (Truck) 发动了！
```

## 📐 设计约束

- 必须使用**抽象工厂模式**
- 工厂类的创建方法必须返回对应的产品对象
- 客户端代码（`make_vehicle`）不应直接依赖具体工厂类，而应通过映射选择

## 🎓 学习目标

- 理解抽象工厂模式的核心思想：**创建一系列相关或依赖的对象，而不指定它们的具体类**
- 区分抽象工厂与工厂方法：抽象工厂创建**一组产品**，工厂方法创建**单个产品**
- 体会抽象工厂在**产品族**（Car 系列 vs Truck 系列）场景下的优势
