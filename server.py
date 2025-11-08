import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from app.models.AccountModel import create_user, login_user

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
        self.wfile.write(f"<html><body><h2>{message}</h2><a href='/index.html'>Back to Home</a></body></html>".encode())

    def handle_login(self, data):
        username = data.get("username", [""])[0]
        password = data.get("password", [""])[0]

        user = login_user(username, password)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if user:
            message = f"Welcome, {user['first_name']} {user['last_name']}! Balance: ${user['balance']:.2f}"
        else:
            message = "Invalid username or password!"
        self.wfile.write(f"<html><body><h2>{message}</h2><a href='/index.html'>Back to Home</a></body></html>".encode())


httpd = HTTPServer(("localhost", PORT), BankHandler)
print(f"Server running at http://localhost:{PORT}")
httpd.serve_forever()
