from app.models.Database import get_connection
from decimal import Decimal

# ✅ ایجاد کاربر جدید
def create_user(first_name, last_name, phone, address, postal_code, username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (first_name, last_name, phone, address, postal_code, username, password, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, phone, address, postal_code, username, password, Decimal('0.0')))
        conn.commit()
        return True, "Account created successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

# ✅ ورود کاربر
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# ✅ انتقال پول بین کاربران با Decimal
def transfer_money(sender_username, receiver_username, amount):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # گرفتن اطلاعات کاربران
        cursor.execute("SELECT * FROM users WHERE username=%s", (sender_username,))
        sender = cursor.fetchone()
        cursor.execute("SELECT * FROM users WHERE username=%s", (receiver_username,))
        receiver = cursor.fetchone()

        if not sender or not receiver:
            return {"success": False, "message": "User not found"}

        # تبدیل موجودی‌ها و مبلغ به Decimal
        sender_balance = Decimal(sender["balance"])
        receiver_balance = Decimal(receiver["balance"])
        amount = Decimal(str(amount))

        if sender_balance < amount:
            return {"success": False, "message": "Insufficient funds"}

        # بروزرسانی موجودی
        new_sender_balance = sender_balance - amount
        new_receiver_balance = receiver_balance + amount

        cursor.execute("UPDATE users SET balance=%s WHERE username=%s", (new_sender_balance, sender_username))
        cursor.execute("UPDATE users SET balance=%s WHERE username=%s", (new_receiver_balance, receiver_username))
        conn.commit()

        return {"success": True, "message": f"Transferred ${float(amount):.2f} to {receiver_username} successfully!"}

    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()
