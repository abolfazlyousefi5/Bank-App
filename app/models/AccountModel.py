# app/models/AccountModel.py
from app.models.Database import get_connection
from decimal import Decimal, InvalidOperation
import random

def generate_card_number_with_prefix(cursor, prefix="58598311"):
    prefix = str(prefix)
    # بررسی معتبر بودن پیش‌شماره
    if not prefix.isdigit() or len(prefix) >= 16:
        raise ValueError("prefix must be numeric and shorter than 16 digits")

    # تولید شماره کارت منحصربه‌فرد
    while True:
        remaining_len = 16 - len(prefix)
        random_part = "".join(str(random.randint(0, 9)) for _ in range(remaining_len))
        candidate = (prefix + random_part)[:16]
        cursor.execute("SELECT id FROM users WHERE card_number=%s", (candidate,))
        if not cursor.fetchone():
            return candidate

def create_user(first_name, last_name, phone, address, id_card, pin):
    # اتصال به دیتابیس
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # جلوگیری از ساخت حساب تکراری
        cursor.execute("SELECT card_number FROM users WHERE id_card=%s OR phone=%s LIMIT 1", (id_card, phone))
        existing = cursor.fetchone()
        if existing:
            return False, "Account already exists for this national ID or phone. Using existing card.", existing.get("card_number")

        # تولید شماره کارت جدید
        card_number = generate_card_number_with_prefix(cursor, prefix="58598311")

        # درج کاربر جدید
        cursor.execute('''
            INSERT INTO users
            (first_name, last_name, phone, address, id_card, card_number, pin, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, phone, address, id_card, card_number, pin, Decimal('0.00')))
        conn.commit()
        return True, "Account created successfully.", card_number
    except Exception as e:
        conn.rollback()
        return False, str(e), None
    finally:
        # بستن کانکشن‌ها
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def login_user(card_number, pin):
    # ورود کاربر با شماره کارت و پین
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE card_number=%s AND pin=%s", (card_number, pin))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def transfer_money(sender_card, receiver_card, amount):
    """
    تبدیل امن amount به Decimal
    """
    from decimal import Decimal
    try:
        # نرمال‌سازی مقدار ورودی
        if isinstance(amount, (float, int)):
            amount_dec = Decimal(str(amount))
        else:
            amount_dec = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError, TypeError):
        return {"success": False, "message": "Invalid amount format."}

    if amount_dec <= 0:
        return {"success": False, "message": "Amount must be greater than zero."}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # قفل کردن رکورد‌ها برای جلوگیری از نقل‌و‌انتقال همزمان
        cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (sender_card,))
        sender = cursor.fetchone()
        cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (receiver_card,))
        receiver = cursor.fetchone()

        # بررسی وجود داشتن کارت‌ها
        if not sender:
            return {"success": False, "message": "Sender card not found."}
        if not receiver:
            return {"success": False, "message": "Receiver card not found."}

        # دریافت موجودی‌ها
        sender_balance = Decimal(str(sender.get("balance", "0.00")))
        receiver_balance = Decimal(str(receiver.get("balance", "0.00")))

        # بررسی موجودی کافی
        if sender_balance < amount_dec:
            return {"success": False, "message": "Insufficient funds."}

        # محاسبه موجودی جدید
        new_sender = sender_balance - amount_dec
        new_receiver = receiver_balance + amount_dec

        # بروزرسانی موجودی‌ها
        cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_sender, sender_card))
        cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_receiver, receiver_card))

        # ثبت تراکنش
        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount) VALUES (%s, %s, %s)",
            (sender_card, receiver_card, float(amount_dec))
        )

        conn.commit()
        return {"success": True, "message": f"Transferred ${float(amount_dec):.2f} to {receiver_card} successfully!"}
    except Exception as e:
        try: conn.rollback()
        except: pass
        return {"success": False, "message": str(e)}
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def get_transactions(card_number, limit=200):
    # دریافت آخرین تراکنش‌های کارت
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, sender, receiver, amount, date FROM transactions "
            "WHERE sender=%s OR receiver=%s ORDER BY date DESC LIMIT %s",
            (card_number, card_number, limit)
        )
        rows = cursor.fetchall()

        # تبدیل amount به float
        for r in rows:
            r["amount"] = float(r["amount"]) if r.get("amount") is not None else 0.0

        return rows
    except Exception:
        return []
    finally:
        # بستن کانکشن
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass
