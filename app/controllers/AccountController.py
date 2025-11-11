import mysql.connector

class AccountController:
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",       # در صورت نیاز تغییر بده
            database="bank_db" # نام دیتابیس
        )
        self.cursor = self.db.cursor(dictionary=True)

    def create_account(self, username, password):
        try:
            self.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if self.cursor.fetchone():
                return False

            self.cursor.execute(
                "INSERT INTO users (username, password, balance, card_number) VALUES (%s, %s, %s, %s)",
                (username, password, 100.00, self.generate_card_number())
            )
            self.db.commit()
            return True
        except Exception as e:
            print("Error creating account:", e)
            return False

    def login(self, username, password):
        self.cursor.execute(
            "SELECT id, username, balance, card_number FROM users WHERE username = %s AND password = %s",
            (username, password)
        )
        user = self.cursor.fetchone()
        return user

    def get_balance(self, username):
        self.cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        user = self.cursor.fetchone()
        return user["balance"] if user else 0.0

    def transfer_money(self, from_user, to_user, amount):
        try:
            if amount <= 0:
                return {"status": "error", "message": "Amount must be greater than zero!"}

            self.cursor.execute("SELECT balance FROM users WHERE username = %s", (from_user,))
            sender = self.cursor.fetchone()
            if not sender:
                return {"status": "error", "message": "Sender not found!"}

            if sender["balance"] < amount:
                return {"status": "error", "message": "Insufficient balance!"}

            self.cursor.execute("SELECT id FROM users WHERE username = %s", (to_user,))
            receiver = self.cursor.fetchone()
            if not receiver:
                return {"status": "error", "message": "Receiver not found!"}

            # کاهش از فرستنده
            self.cursor.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (amount, from_user))
            # افزودن به گیرنده
            self.cursor.execute("UPDATE users SET balance = balance + %s WHERE username = %s", (amount, to_user))
            self.db.commit()

            return {"status": "success", "message": f"Transferred ${amount:.2f} successfully!"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_card_number(self):
        import random
        return str(random.randint(1000000000000000, 9999999999999999))
