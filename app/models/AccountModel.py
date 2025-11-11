# app/models/AccountModel.py
from app.models.Database import get_connection
from decimal import Decimal
import random

def generate_card_number_with_prefix(cursor, prefix="58598311"):
    """
    تولید شماره کارت 16 رقمی که با prefix شروع می‌شود و یکتا بودن را چک می‌کند.
    """
    prefix = str(prefix)
    if not prefix.isdigit() or len(prefix) >= 16:
        raise ValueError("prefix must be numeric and shorter than 16 digits")

    while True:
        remaining_len = 16 - len(prefix)
        random_part = "".join(str(random.randint(0, 9)) for _ in range(remaining_len))
        candidate = (prefix + random_part)[:16]

        # چک یکتا بودن
        cursor.execute("SELECT id FROM users WHERE card_number=%s", (candidate,))
        if not cursor.fetchone():
            return candidate
        # در صورت تصادف (خیلی نادر) دوباره تلاش می‌کنیم

def create_user(first_name, last_name, phone, address, postal_code, pin):
    """
    ایجاد کاربر جدید:
    - کاربر خودش PIN را وارد می‌کند.
    - شماره کارت خودکار ساخته می‌شود و با prefix '58598311' شروع می‌گردد.
    - اگر رکوردی با first_name+last_name+phone قبلا وجود داشته باشد، از تکرار جلوگیری می‌شود
      و اطلاعات کارت فعلی بازگردانده می‌شود.
    خروجی: (success: bool, message: str, card_number_or_None)
    """
    # اعتبارسنجی PIN ساده (4 رقم)
    if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
        return False, "PIN must be a 4-digit numeric string.", None

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # اول بررسی می‌کنیم آیا همین کاربر از قبل وجود دارد (بر اساس نام+نام خانوادگی+شماره)
        cursor.execute("""
            SELECT card_number FROM users
            WHERE first_name=%s AND last_name=%s AND phone=%s
            LIMIT 1
        """, (first_name, last_name, phone))
        existing = cursor.fetchone()
        if existing:
            # اگر قبلاً ساخته شده، جلوی تکرار را می‌گیریم و کارت موجود را برمی‌گردانیم
            return False, "Account already exists for this person. Using existing card.", existing.get("card_number")

        # تولید شماره کارت یکتا
        card_number = generate_card_number_with_prefix(cursor, prefix="58598311")

        # درج کاربر جدید با balance صفر
        cursor.execute('''
            INSERT INTO users
            (first_name, last_name, phone, address, postal_code, card_number, pin, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, phone, address, postal_code, card_number, pin, Decimal('0.00')))

        conn.commit()
        return True, "Account created successfully.", card_number
    except Exception as e:
        conn.rollback()
        return False, str(e), None
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

def login_user(card_number, pin):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE card_number=%s AND pin=%s", (card_number, pin))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def transfer_money(sender_card, receiver_card, amount):
    try:
        amount_dec = Decimal(str(amount))
    except Exception:
        return {"success": False, "message": "Invalid amount format."}

    if amount_dec <= 0:
        return {"success": False, "message": "Amount must be greater than zero."}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE card_number=%s", (sender_card,))
        sender = cursor.fetchone()
        cursor.execute("SELECT * FROM users WHERE card_number=%s", (receiver_card,))
        receiver = cursor.fetchone()

        if not sender:
            return {"success": False, "message": "Sender card not found."}
        if not receiver:
            return {"success": False, "message": "Receiver card not found."}

        sender_balance = Decimal(str(sender.get("balance", "0.00")))
        receiver_balance = Decimal(str(receiver.get("balance", "0.00")))

        if sender_balance < amount_dec:
            return {"success": False, "message": "Insufficient funds."}

        new_sender = sender_balance - amount_dec
        new_receiver = receiver_balance + amount_dec

        cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_sender, sender_card))
        cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_receiver, receiver_card))

        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount) VALUES (%s, %s, %s)",
            (sender_card, receiver_card, float(amount_dec))
        )

        conn.commit()
        return {"success": True, "message": f"Transferred ${float(amount_dec):.2f} to {receiver_card} successfully!"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def get_transactions(card_number, limit=200):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, sender, receiver, amount, date FROM transactions "
            "WHERE sender=%s OR receiver=%s ORDER BY date DESC LIMIT %s",
            (card_number, card_number, limit)
        )
        rows = cursor.fetchall()
        return rows
    except Exception:
        return []
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass
