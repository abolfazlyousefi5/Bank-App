import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from app.models.AccountModel import create_user, login_user, transfer_money

PORT = 8000

class BankHandler(SimpleHTTPRequestHandler):

    # مسیر فایل‌ها از public/
    def translate_path(self, path):
        root = os.path.join(os.getcwd(), "public")
        path = path.lstrip("/")
        return os.path.join(root, path)

    # ✅ GET
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

    # ✅ POST
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(length).decode('utf-8')

        if self.headers.get("Content-Type") == "application/json":
            data = json.loads(post_data)
        else:
            data = parse_qs(post_data)

        if self.path == "/register":
            self.handle_register(data)
        elif self.path == "/login":
            self.handle_login(data)
        elif self.path == "/transfer":
            self.handle_transfer(data)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    # ✅ ثبت نام
    def handle_register(self, data):
        first_name = data.get("first_name", [""])[0]
        last_name = data.get("last_name", [""])[0]
        phone = data.get("phone", [""])[0]
        address = data.get("address", [""])[0]
        postal_code = data.get("postal_code", [""])[0]
        username = data.get("username", [""])[0]
        password = data.get("password", [""])[0]

        success, message = create_user(first_name, last_name, phone, address, postal_code, username, password)

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"<html><body><h2>{message}</h2><a href='/index.html'>Back</a></body></html>".encode())

    # ✅ ورود
    def handle_login(self, data):
        username = data.get("username", [""])[0]
        password = data.get("password", [""])[0]
        user = login_user(username, password)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        if user:
            response = {
                "success": True,
                "user": {
                    "id": user["id"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "username": user["username"],
                    "balance": float(user["balance"])
                }
            }
        else:
            response = {"success": False, "message": "Invalid username or password!"}

        self.wfile.write(json.dumps(response).encode("utf-8"))

    # ✅ انتقال پول
    def handle_transfer(self, data):
        sender = data.get("sender")
        receiver = data.get("receiver")
        try:
            amount = float(data.get("amount", 0))
        except:
            amount = 0

        if amount <= 0:
            result = {"success": False, "message": "Amount must be greater than zero!"}
        else:
            result = transfer_money(sender, receiver, amount)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))


# ✅ اجرای سرور
httpd = HTTPServer(("localhost", PORT), BankHandler)
print(f"Server running at http://localhost:{PORT}")
httpd.serve_forever()
