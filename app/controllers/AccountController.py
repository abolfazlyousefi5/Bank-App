# app/controllers/AccountController.py

import random
from decimal import Decimal, InvalidOperation
import mysql.connector
from mysql.connector import Error

class AccountController:

    def __init__(self, host="localhost", user="root", password="", database="bank_db"):
        """
         Initialize controller and database connection configuration.
         مقداردهی اولیه و تنظیمات اتصال دیتابیس.
        """
        self.db_config = dict(host=host, user=user, password=password, database=database)
        self._connect()

    def _connect(self):
        """
        EN: Create a new DB connection when the controller is initialized.
        FA: هنگام ساخته شدن کنترلر، یک اتصال جدید به دیتابیس ایجاد می‌کند.
        """
        try:
            self.db = mysql.connector.connect(**self.db_config)
            self.cursor = self.db.cursor(dictionary=True)
        except Error as e:
            raise RuntimeError(f"DB connection error: {e}")

    def _ensure_connection(self):
        """
        EN: Reconnect automatically if connection is lost.
        FA: اگر اتصال قطع شده باشد، دوباره وصل می‌شود.
        """
        if not getattr(self, "db", None) or not self.db.is_connected():
            self._connect()

    def _generate_card_with_prefix(self, prefix="58598311"):
        """
        EN: Generate a unique 16-digit card number starting with a given prefix.
        FA: تولید شماره کارت ۱۶ رقمی که با پیش‌وند مشخص شروع شده و تکراری نبودنش توسط دیتابیس چک می‌شود.
        """
        prefix = str(prefix)

        if not prefix.isdigit() or len(prefix) >= 16:
            raise ValueError("prefix must be numeric and shorter than 16 digits")

        self._ensure_connection()

        while True:
            # EN: Generate random digits to complete 16-digit card number
            # FA: تولید بقیه ارقام شماره کارت به صورت تصادفی
            remaining = 16 - len(prefix)
            rnd = "".join(str(random.randint(0, 9)) for _ in range(remaining))
            candidate = (prefix + rnd)[:16]

            self.cursor.execute("SELECT id FROM users WHERE card_number = %s", (candidate,))
            if not self.cursor.fetchone():
                return candidate
            # EN: If duplicate card_number detected (rare), try again
            # FA: اگر تکراری بود (نادر)، دوباره تلاش کن

    def create_account(self, first_name, last_name, phone, address, id_card, pin):
        """
        EN: Create a new bank account with validation for national ID, phone, PIN.
        FA: ساخت حساب بانکی با اعتبارسنجی کد ملی، شماره موبایل، و پین کد.
        """
        # --- VALIDATIONS ---

        # PIN
        if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
            return False, "PIN must be a 4-digit numeric string.", None

        # Phone number
        if not (isinstance(phone, str) and phone.isdigit() and len(phone) == 11 and phone.startswith("09")):
            return False, "Phone must be 11 digits and start with '09'.", None

        # National ID
        if not (isinstance(id_card, str) and id_card.isdigit() and len(id_card) == 10):
            return False, "ID Card must be 10 digits.", None

        self._ensure_connection()

        try:
            # EN: Prevent duplicates (same national ID or phone)
            # FA: چک می‌کند شماره‌ملی یا تلفن قبل‌تر ثبت نشده باشند
            self.cursor.execute(
                "SELECT card_number FROM users WHERE id_card=%s OR phone=%s LIMIT 1",
                (id_card, phone)
            )
            existing = self.cursor.fetchone()

            if existing:
                return False, "Account already exists for this national ID or phone.", existing["card_number"]

            # EN: Generate new unique card number
            # FA: ساخت شماره کارت یکتا
            card_number = self._generate_card_with_prefix(prefix="58598311")

            # EN: Insert new account with zero balance
            # FA: ثبت حساب جدید با موجودی صفر
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
        EN: Login using card_number and PIN. Returns user info on success.
        FA: ورود با شماره کارت و پین — در صورت موفق بودن اطلاعات کاربر بازگردانده می‌شود.
        """
        if not card_number or not pin:
            return None

        self._ensure_connection()

        self.cursor.execute(
            "SELECT id, first_name, last_name, card_number, balance "
            "FROM users WHERE card_number=%s AND pin=%s",
            (card_number, pin)
        )

        user = self.cursor.fetchone()

        if user:
            # EN: Convert Decimal to float for frontend compatibility
            # FA: تبدیل Decimal به float برای سازگاری با جاوااسکریپت
            user["balance"] = float(user["balance"])

        return user

    def transfer_money(self, sender_card, receiver_card, amount):
        """
        EN: Transfer money between two accounts safely using SQL transaction.
        FA: انتقال پول امن بین دو کارت با استفاده از تراکنش دیتابیس.
        """
        # --- Validate amount ---
        try:
            amount_dec = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return {"success": False, "message": "Invalid amount format."}

        if amount_dec <= 0:
            return {"success": False, "message": "Amount must be greater than zero."}

        self._ensure_connection()

        try:
            # EN: Fetch sender and receiver rows with a FOR UPDATE lock
            # FA: گرفتن اطلاعات فرستنده/گیرنده همراه با قفل برای جلوگیری از تداخل تراکنش‌ها
            self.cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (sender_card,))
            sender = self.cursor.fetchone()

            self.cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (receiver_card,))
            receiver = self.cursor.fetchone()

            if not sender:
                return {"success": False, "message": "Sender card not found."}
            if not receiver:
                return {"success": False, "message": "Receiver card not found."}

            sender_balance = Decimal(str(sender["balance"]))
            receiver_balance = Decimal(str(receiver["balance"]))

            # EN: Check insufficient funds
            # FA: چک موجودی کافی
            if sender_balance < amount_dec:
                return {"success": False, "message": "Insufficient funds."}

            # EN: Calculate new balances
            # FA: محاسبه موجودی جدید
            new_sender = sender_balance - amount_dec
            new_receiver = receiver_balance + amount_dec

            # --- Update balances ---
            self.cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_sender, sender_card))
            self.cursor.execute("UPDATE users SET balance=%s WHERE card_number=%s", (new_receiver, receiver_card))

            # --- Log transaction ---
            self.cursor.execute(
                "INSERT INTO transactions (sender, receiver, amount) VALUES (%s, %s, %s)",
                (sender_card, receiver_card, float(amount_dec))
            )

            self.db.commit()

            return {
                "success": True,
                "message": f"Transferred ${float(amount_dec):.2f} to {receiver_card} successfully!"
            }

        except Exception as e:
            try:
                self.db.rollback()
            except:
                pass

            return {"success": False, "message": f"DB error: {e}"}

    def get_transactions(self, card_number, limit=200):
        """
        EN: Fetch list of transactions involving the given card.
        FA: دریافت لیست تراکنش‌هایی که کارت مورد نظر در آن‌ها نقش داشته.
        """
        self._ensure_connection()

        try:
            self.cursor.execute("""
                SELECT id, sender, receiver, amount, date
                FROM transactions
                WHERE sender=%s OR receiver=%s
                ORDER BY date DESC
                LIMIT %s
            """, (card_number, card_number, limit))

            rows = self.cursor.fetchall()

            # EN: Convert Decimal amounts to float
            # FA: تبدیل amount به float برای کار با جاوااسکریپت
            for r in rows:
                r["amount"] = float(r["amount"])

            return rows

        except Exception:
            return []

    def close(self):
        """
        EN: Close DB connection safely.
        FA: بستن امن اتصال به دیتابیس.
        """
        try:
            if getattr(self, "cursor", None):
                self.cursor.close()
            if getattr(self, "db", None) and self.db.is_connected():
                self.db.close()
        except:
            pass
