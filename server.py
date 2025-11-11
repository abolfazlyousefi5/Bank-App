import os
import json
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
        data = parse_qs(body)

        # helper برای خواندن داده از parse_qs
        def getf(k):
            v = data.get(k)
            if isinstance(v, list):
                return v[0]
            return v

        # ---------- REGISTER ----------
        if self.path == "/register":
            first_name = getf("first_name") or ""
            last_name = getf("last_name") or ""
            pin = getf("pin") or ""
            phone = getf("phone") or ""
            address = getf("address") or ""
            postal_code = getf("postal_code") or ""

            # validate pin
            if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
                success, message, card_number = False, "PIN must be a 4-digit number!", None
            else:
                success, message, card_number = create_user(first_name, last_name, phone, address, postal_code, pin)

            self.send_response(200 if success else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if card_number:
                html = f"""
                <html>
                <body>
                    <h2>{message}</h2>
                    <p><strong>Your Card Number:</strong> {card_number}</p>
                    <p>Keep it safe. Use your card number and PIN to login.</p>
                    <a href='/login.html'>Login</a>
                </body>
                </html>
                """
            else:
                html = f"""
                <html>
                <body>
                    <h2>{message}</h2>
                    <a href='/create_account.html'>Back</a>
                </body>
                </html>
                """
            self.wfile.write(html.encode("utf-8"))
            return

        # ---------- LOGIN ----------
        if self.path == "/login":
            card_number = getf("card_number") or ""
            pin = getf("pin") or ""

            if not card_number or not pin:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Card number and PIN required."}).encode())
                return

            user = login_user(card_number, pin)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if user:
                response = {
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "card_number": user.get("card_number") or "",
                        "first_name": user.get("first_name", ""),
                        "last_name": user.get("last_name", ""),
                        "balance": float(user.get("balance", 0.0))
                    }
                }
            else:
                response = {"success": False, "message": "Invalid card number or PIN."}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        # ---------- TRANSFER ----------
        if self.path == "/transfer":
            sender = getf("sender") or ""
            receiver = getf("receiver") or ""
            amt = getf("amount") or "0"
            try:
                amount = float(str(amt).strip())
            except:
                amount = 0.0


            if amount <= 0:
                result = {"success": False, "message": "Amount must be greater than zero!"}
            else:
                result = transfer_money(sender, receiver, amount)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        # ---------- TRANSACTIONS ----------
        if self.path == "/transactions":
            card = getf("card_number") or ""
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
