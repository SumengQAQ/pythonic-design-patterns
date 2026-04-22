import copy


class Connection:
    """模拟数据库连接（不可复制）"""

    def __init__(self, db_name):
        self.db_name = db_name
        print(f"建立连接: {db_name}")

    def __copy__(self):
        """浅拷贝时：创建新连接"""
        return Connection(self.db_name)

    def __deepcopy__(self, memo):
        """深拷贝时：也创建新连接"""
        return Connection(self.db_name)


class Config:
    def __init__(self, db_name):
        self.conn = Connection(db_name)
        self.settings = {"theme": "dark", "lang": "zh"}

    def __copy__(self):
        """浅拷贝：settings 浅复制，conn 通过 Connection.__copy__ 处理"""
        new = type(self)(self.conn.db_name)  # 复用原 db_name
        new.settings = self.settings.copy()
        return new

    def __deepcopy__(self, memo):
        """深拷贝：settings 深复制，conn 通过 Connection.__deepcopy__ 处理"""
        new = type(self)(self.conn.db_name)
        new.settings = copy.deepcopy(self.settings, memo)
        return new
