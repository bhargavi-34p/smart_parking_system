import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_MYSQL_PASSWORD",
        database="parking_db"
    )

    return connection


connection = get_connection()

if connection.is_connected():
    print("MySQL connected successfully!")

connection.close()