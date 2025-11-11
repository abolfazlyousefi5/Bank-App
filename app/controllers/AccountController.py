# app/controllers/AccountController.py
import random
from decimal import Decimal, InvalidOperation
import mysql.connector
from mysql.connector import Error

class AccountController:
    def __init__(self, host="localhost", user="root", password="", database="bank_db"):
        """
        تنظیم اتصال به دیتابیس — در صورت نیاز پارامترها را تغییر بده.
        """
        self.db_config = dict(host=host, user=user, password=password, database=database)
        self._connect()

    def _connect(self):
        # اتصال جدید ایجاد می‌کنیم (برای پایداری در طول درخواست‌ها)
        try:
            self.db = mysql.connector.connect(**self.db_config)
            self.cursor = self.db.cursor(dictionary=True)
        except Error as e:
            raise RuntimeError(f"DB connection error: {e}")

    def _ensure_connection(self):
        # در صورت قطع اتصال، مجدداً وصل شو
        if not getattr(self, "db", None) or not self.db.is_connected():
            self._connect()

    def _generate_card_with_prefix(self, prefix="58598311"):
        """
        تولید شماره کارت 16 رقمی که با prefix شروع می‌شود و یکتا بودن را با DB چک می‌کند.
        """
        prefix = str(prefix)
        if not prefix.isdigit() or len(prefix) >= 16:
            raise ValueError("prefix must be numeric and shorter than 16 digits")

        self._ensure_connection()
        while True:
            remaining = 16 - len(prefix)
            rnd = "".join(str(random.randint(0, 9)) for _ in range(remaining))
            candidate = (prefix + rnd)[:16]
            self.cursor.execute("SELECT id FROM users WHERE card_number = %s", (candidate,))
            if not self.cursor.fetchone():
                return candidate
            # اگر تصادف شد (خیلی نادر) دوباره تلاش کن

    def create_account(self, first_name, last_name, phone, address, id_card, pin):
        """
        ایجاد حساب جدید:
        - pin: باید رشته‌ای از 4 رقم باشد.
        - phone: باید 11 رقم و با '09' شروع کند (چک روی سرور نیز انجام می‌شود).
        - id_card: 10 رقم عددی.
        خروجی: (success: bool, message: str, card_number or None)
        """
        # اعتبارسنجی ساده
        if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
            return False, "PIN must be a 4-digit numeric string.", None
        if not (isinstance(phone, str) and phone.isdigit() and len(phone) == 11 and phone.startswith("09")):
            return False, "Phone must be 11 digits and start with '09'.", None
        if not (isinstance(id_card, str) and id_card.isdigit() and len(id_card) == 10):
            return False, "ID Card must be 10 digits.", None

        self._ensure_connection()
        try:
            # جلوگیری از تکرار: اگر همین id_card یا همین phone قبلا ثبت شده بود
            self.cursor.execute("SELECT card_number FROM users WHERE id_card=%s OR phone=%s LIMIT 1", (id_card, phone))
            existing = self.cursor.fetchone()
            if existing:
                return False, "Account already exists for this national ID or phone. Use existing card.", existing.get("card_number")

            card_number = self._generate_card_with_prefix(prefix="58598311")

            # درج کاربر با بالانس صفر
            self.cursor.execute("""
                INSERT INTO users
                (first_name, last_name, phone, address, id_card, card_number, pin, balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, phone, address, id_card, card_number, pin, Decimal("0.00")))
            self.db.commit()
            return True, "Account created successfully.", card_number
        except Exception as e:
            try:
                self.db.rollback()
            except:
                pass
            return False, f"DB error: {e}", None

    def login(self, card_number, pin):
        """
        لاگین با card_number و pin — اگر موفق بود دیتای یوزر را برمی‌گرداند (dict) وگرنه None.
        """
        if not card_number or not pin:
            return None
        self._ensure_connection()
        self.cursor.execute("SELECT id, first_name, last_name, card_number, balance FROM users WHERE card_number=%s AND pin=%s", (card_number, pin))
        user = self.cursor.fetchone()
        if user:
            # ensure balance is plain float for frontend
            user["balance"] = float(user.get("balance") or 0.0)
        return user

    def transfer_money(self, sender_card, receiver_card, amount):
        """
        انتقال پول بین کارت‌ها. مقدار را با Decimal پردازش می‌کنیم.
        خروجی: dict { success: bool, message: str }
        """
        try:
            amount_dec = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return {"success": False, "message": "Invalid amount format."}

        if amount_dec <= 0:
            return {"success": False, "message": "Amount must be greater than zero."}

        self._ensure_connection()
        try:
            # قفل خواندن و نوشتن را با transaction انجام می‌دهیم
            # ابتدا اطلاعات فرستنده و گیرنده را بگیر
            self.cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (sender_card,))
            sender = self.cursor.fetchone()
            self.cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (receiver_card,))
            receiver = self.cursor.fetchone()

            if not sender:
                return {"success": False, "message": "Sender card not found."}
            if not receiver:
                return {"success": False, "message": "Receiver card not found."}

            sender_balance = Decimal(str(sender.get("balance") or "0.00"))
            receiver_balance = Decimal(str(receiver.get("balance") or "0.00"))

            if sender_balance < amount_dec:
                return {"success": False, "message": "Insufficient funds."}

            new_sender = sender_balance - amount_dec
            new_receiver = receiver_balance + amount_dec

            # آپدیت‌ها
            self.cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_sender, sender_card))
            self.cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_receiver, receiver_card))

            # ثبت تراکنش در جدول transactions
            self.cursor.execute(
                "INSERT INTO transactions (sender, receiver, amount) VALUES (%s, %s, %s)",
                (sender_card, receiver_card, float(amount_dec))
            )

            self.db.commit()
            return {"success": True, "message": f"Transferred ${float(amount_dec):.2f} to {receiver_card} successfully!"}
        except Exception as e:
            try:
                self.db.rollback()
            except:
                pass
            return {"success": False, "message": f"DB error: {e}"}

    def get_transactions(self, card_number, limit=200):
        """
        برگرداندن لیست تراکنش‌ها مربوط به یک کارت (فرستنده یا گیرنده).
        خروجی: [{id, sender, receiver, amount, date}, ...]
        """
        self._ensure_connection()
        try:
            self.cursor.execute(
                "SELECT id, sender, receiver, amount, date FROM transactions "
                "WHERE sender=%s OR receiver=%s ORDER BY date DESC LIMIT %s",
                (card_number, card_number, limit)
            )
            rows = self.cursor.fetchall()
            # اطمینان از نوع مناسب برای جاوااسکریپت (float برای amount)
            for r in rows:
                r["amount"] = float(r["amount"]) if r.get("amount") is not None else 0.0
            return rows
        except Exception:
            return []

    def close(self):
        try:
            if getattr(self, "cursor", None):
                self.cursor.close()
            if getattr(self, "db", None) and self.db.is_connected():
                self.db.close()
        except:
            pass
