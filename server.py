import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from app.models.AccountModel import create_user, login_user

PORT = 8000

class BankHandler(SimpleHTTPRequestHandler):

    # مسیر فایل‌ها از public/
    def translate_path(self, path):
        root = os.path.join(os.getcwd(), "public")
        path = path.lstrip("/")
        return os.path.join(root, path)

    # GET requests
    def do_GET(self):
    # اگر مسیر ریشه باشه، index.html برگردان
        if self.path == "/":
            self.path = "/index.html"

        # مسیر کامل فایل در public/
        file_path = self.translate_path(self.path)

        if os.path.exists(file_path):
            # اگر فایل وجود داشت، خدمت بده
            return super().do_GET()
        else:
            # در غیر این صورت 404 بده
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")


    # POST requests
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(length).decode('utf-8')
        data = parse_qs(post_data)

        if self.path == "/register":
            self.handle_register(data)
        elif self.path == "/login":
            self.handle_login(data)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    # ثبت نام
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
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            f"<html><body><h2>{message}</h2><a href='/views/index.html'>Back to Home</a></body></html>".encode()
        )

    # ورود
    def handle_login(self, data):
        import json
        username = data.get("username", [""])[0]
        password = data.get("password", [""])[0]

        user = login_user(username, password)

        self.send_response(200)
        self.send_header("Content-type", "application/json")  # ✅ مهم!
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
            response = {
                "success": False,
                "message": "Invalid username or password!"
            }

        self.wfile.write(json.dumps(response).encode("utf-8"))

# ران کردن سرور
httpd = HTTPServer(("localhost", PORT), BankHandler)
print(f"Server running at http://localhost:{PORT}")
httpd.serve_forever()
