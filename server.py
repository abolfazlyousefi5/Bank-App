# server.py
import os
import json
from decimal import Decimal, InvalidOperation
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from app.models.AccountModel import create_user, login_user, transfer_money, get_transactions

PORT = 8000

class BankHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        root = os.path.join(os.getcwd(), "public")
        path = path.lstrip("/")
        return os.path.join(root, path)

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        file_path = self.translate_path(self.path)
        if os.path.exists(file_path):
            return super().do_GET()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else ""
        # parse JSON or form-encoded
        if self.headers.get("Content-Type", "").startswith("application/json"):
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}
        else:
            data = parse_qs(body)

        # helper to read field whether parse_qs(list) or json(dict)
        def getf(k):
            v = data.get(k)
            if isinstance(v, list):
                return v[0]
            return v

        # register (kept as HTML response)
        if self.path == "/register":
            first_name = getf("first_name") or ""
            last_name = getf("last_name") or ""
            pin = getf("pin") or ""
            phone = getf("phone") or ""
            address = getf("address") or ""
            id_card = getf("id_card") or ""

            # basic server-side validation (pin/phone/id)
            if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
                success, message, card = False, "PIN must be a 4-digit number!", None
            elif not (isinstance(phone, str) and phone.isdigit() and len(phone) == 11 and phone.startswith("09")):
                success, message, card = False, "Phone must be 11 digits and start with 09.", None
            elif not (isinstance(id_card, str) and id_card.isdigit() and len(id_card) == 10):
                success, message, card = False, "ID Card must be 10 digits.", None
            else:
                success, message, card = create_user(first_name, last_name, phone, address, id_card, pin)

            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if success and card:
                html = f"""
                <html><body>
                <h2>{message}</h2>
                <p><strong>Your Card Number:</strong> {card}</p>
                <p>Keep it safe. Use your card number and PIN to login.</p>
                <p><a href='/login.html'>Login</a></p>
                </body></html>
                """
            else:
                html = f"<html><body><h2>{message}</h2><p><a href='/create_account.html'>Back</a></p></body></html>"
            self.wfile.write(html.encode("utf-8"))
            return

        # login -> expects form-urlencoded (from login.html) or JSON
        if self.path == "/login":
            card_number = getf("card_number") or ""
            pin = getf("pin") or ""
            if isinstance(card_number, list): card_number = card_number[0]
            if isinstance(pin, list): pin = pin[0]

            user = login_user(card_number, pin)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if user:
                user_out = {
                    "id": user.get("id"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "card_number": user.get("card_number"),
                    "balance": float(user.get("balance") or 0.0)
                }
                self.wfile.write(json.dumps({"success": True, "user": user_out}).encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"success": False, "message": "Invalid card number or PIN."}).encode("utf-8"))
            return

        # transfer -> robust parsing and validation
        if self.path == "/transfer":
            sender = getf("sender") or ""
            receiver = getf("receiver") or ""
            amt = getf("amount") or "0"

            # normalize sender/receiver strings
            if isinstance(sender, list): sender = sender[0]
            if isinstance(receiver, list): receiver = receiver[0]

            # parse amount safely using Decimal
            try:
                # if JSON sent a number, amt may be numeric; convert to str
                amt_str = str(amt).strip()
                amount = Decimal(amt_str)
            except Exception:
                amount = Decimal("0")

            # validations
            if not isinstance(sender, str) or not sender or len(sender) != 16 or not sender.isdigit():
                result = {"success": False, "message": "Invalid sender card number."}
                status = 400
            elif not isinstance(receiver, str) or not receiver or len(receiver) != 16 or not receiver.isdigit():
                result = {"success": False, "message": "Invalid receiver card number."}
                status = 400
            elif amount <= 0:
                result = {"success": False, "message": "Amount must be greater than zero!"}
                status = 400
            else:
                # call model (transfer_money expects numeric/Decimal-compatible)
                # convert amount to float for compatibility (model handles Decimal too)
                result = transfer_money(sender, receiver, float(amount))
                status = 200

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        # transactions -> expects JSON { card_number: "..." }
        if self.path == "/transactions":
            card = getf("card_number") or ""
            if isinstance(card, list): card = card[0]
            transactions = get_transactions(card)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(transactions, default=str).encode("utf-8"))
            return

        # unknown
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"404 Not Found")


if __name__ == "__main__":
    httpd = HTTPServer(("localhost", PORT), BankHandler)
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()
