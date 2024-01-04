import sqlite3
from cfg import sensor_amount

class Database:
    def __init__(self, database_name):
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def create_table(self, sql: str):
        self.cursor.execute(sql)
        self.connection.commit()

    def insert(self, table, *values):
        self.cursor.execute(f'INSERT INTO {table} VALUES ({",".join(["?" for _ in values])})', values)
        self.connection.commit()

    def fetch(self, selector, table, condition):
        return self.cursor.execute(f'SELECT {selector} FROM {table} WHERE {condition}')

    def fetch_all(self, selector, table):
        return self.cursor.execute(f'SELECT {selector} FROM {table}')

    def delete(self, table, condition):
        self.cursor.execute(f'DELETE FROM {table} WHERE {condition}')
        self.connection.commit()

    def update(self, table, column, condition):
        self.cursor.execute(f'UPDATE {table} SET {column} WHERE {condition}')
        self.connection.commit()
        
def create_database():
    print('Creating database')
    db = Database('database.db')
    sensors_str = ", ".join([f"t{num} INTEGER" for num in range(sensor_amount)])
    print(sensors_str)
    db.create_table(f"CREATE TABLE IF NOT EXISTS sensors (id INTEGER PRIMARY KEY AUTOINCREMENT, {sensors_str}, timestamp INTEGER);")

if __name__ == "__main__":
    create_database()