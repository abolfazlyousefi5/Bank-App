import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # پسورد MySQL خودت
        database="bank_app"
    )
