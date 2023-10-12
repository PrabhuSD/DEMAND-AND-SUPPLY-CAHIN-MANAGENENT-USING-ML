import sqlite3

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

cursor.execute("create table if not exists admin(email TEXT, password TEXT)")
cursor.execute("insert into admin values('admin@gmail.com', 'admin123')")
connection.commit()