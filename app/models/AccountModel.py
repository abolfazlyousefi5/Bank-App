# app/models/AccountModel.py
from app.models.Database import get_connection
from decimal import Decimal, InvalidOperation
import random

def generate_card_number_with_prefix(cursor, prefix="58598311"):
    prefix = str(prefix)
    if not prefix.isdigit() or len(prefix) >= 16:
        raise ValueError("prefix must be numeric and shorter than 16 digits")

    while True:
        remaining_len = 16 - len(prefix)
        random_part = "".join(str(random.randint(0, 9)) for _ in range(remaining_len))
        candidate = (prefix + random_part)[:16]
        cursor.execute("SELECT id FROM users WHERE card_number=%s", (candidate,))
        if not cursor.fetchone():
            return candidate

def create_user(first_name, last_name, phone, address, id_card, pin):
    # validation done in controller; here assume valid
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT card_number FROM users WHERE id_card=%s OR phone=%s LIMIT 1", (id_card, phone))
        existing = cursor.fetchone()
        if existing:
            return False, "Account already exists for this national ID or phone. Using existing card.", existing.get("card_number")

        card_number = generate_card_number_with_prefix(cursor, prefix="58598311")
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
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def login_user(card_number, pin):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE card_number=%s AND pin=%s", (card_number, pin))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def transfer_money(sender_card, receiver_card, amount):
    """
    amount can be float, int or string. We'll convert it to Decimal safely.
    """
    from decimal import Decimal
    try:
        # normalize amount
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
        # read balances
        cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (sender_card,))
        sender = cursor.fetchone()
        cursor.execute("SELECT id, balance FROM users WHERE card_number=%s FOR UPDATE", (receiver_card,))
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
        try: conn.rollback()
        except: pass
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
        # normalize amount to float
        for r in rows:
            r["amount"] = float(r["amount"]) if r.get("amount") is not None else 0.0
        return rows
    except Exception:
        return []
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass
