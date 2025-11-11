# app/controllers/AccountController.py
from http.server import SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import json

# وارد کردن توابع مدل بر اساس نام‌هایی که شما استفاده کردی
# (فرض: AccountModel.create_user returns (success, message, card_number_or_None))
from app.models.AccountModel import create_user, login_user

class AccountController(SimpleHTTPRequestHandler):
    """
    کنترلر ساده برای /register و /login
    پاسخ‌ها JSON هستند (برای fetch). اما اگر فرم معمولی ارسال شد،
    کنترلر به‌صورت HTML پاسخ کوتاه می‌دهد تا کاربر در مرورگر پیام ببیند.
    """

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        ctype = self.headers.get("Content-Type", "")
        if "application/json" in ctype:
            try:
                return json.loads(raw)
            except:
                return {}
        else:
            # parse_qs -> values are lists
            return parse_qs(raw)

    def _send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # اگر بخوای CORS باز باشه:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload, default=str).encode("utf-8"))

    def _send_html(self, status_code, html):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_OPTIONS(self):
        # برای اجازه دادن به درخواست‌های fetch از جاوااسکریپت
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        data = self._read_body()

        # Helper to read either dict (JSON) or parse_qs (lists)
        def getf(k):
            v = data.get(k)
            if isinstance(v, list):
                return v[0] if v else ""
            return v

        if self.path == "/register":
            # از فرم ما باید فیلد pin وجود داشته باشه (کاربر وارد می‌کنه)، کارت سرور میسازه
            first_name = getf("first_name") or ""
            last_name = getf("last_name") or ""
            pin = getf("pin") or ""
            phone = getf("phone") or ""
            address = getf("address") or ""
            postal_code = getf("postal_code") or ""

            # اعتبارسنجی PIN ساده
            if not (isinstance(pin, str) and pin.isdigit() and len(pin) == 4):
                # اگر درخواست JSON بوده => JSON برگردون
                if isinstance(data, dict):
                    return self._send_json(400, {"success": False, "message": "PIN must be a 4-digit number."})
                else:
                    html = "<h2 style='color:red;'>PIN must be a 4-digit number.</h2><a href='/create_account.html'>Back</a>"
                    return self._send_html(400, html)

            # فراخوانی مدل (expect: create_user returns (success, message, card_number_or_None))
            success, message, card_number = create_user(first_name, last_name, phone, address, postal_code, pin)

            if isinstance(data, dict):
                # JSON response
                return self._send_json(200 if success else 400, {
                    "success": success,
                    "message": message,
                    "card_number": card_number
                })
            else:
                # HTML response for regular form submit
                if success and card_number:
                    html = (f"<h2 style='color:green;'>{message}</h2>"
                            f"<p>Your card number: <strong>{card_number}</strong></p>"
                            "<p>Keep it safe. Use card number and PIN to login.</p>"
                            "<a href='/login.html'>Login</a>")
                    return self._send_html(200, html)
                else:
                    html = f"<h2 style='color:red;'>{message}</h2><a href='/create_account.html'>Back</a>"
                    return self._send_html(400, html)

        elif self.path == "/login":
            # login expects card_number and pin
            card_number = getf("card_number") or getf("card") or ""
            pin = getf("pin") or ""

            if not card_number or not pin:
                if isinstance(data, dict):
                    return self._send_json(400, {"success": False, "message": "Card number and PIN required."})
                else:
                    return self._send_html(400, "<h2 style='color:red;'>Card number and PIN required.</h2><a href='/login.html'>Back</a>")

            user = login_user(card_number, pin)
            if user:
                # user should be serializable dict from model (id, first_name, last_name, card_number, balance,...)
                if isinstance(data, dict):
                    return self._send_json(200, {"success": True, "user": user})
                else:
                    html = (f"<h2 style='color:green;'>Welcome {user.get('first_name')} {user.get('last_name')}!</h2>"
                            f"<p>Balance: ${float(user.get('balance',0)):.2f}</p>"
                            "<a href='/dashboard.html'>Go to Dashboard</a>")
                    return self._send_html(200, html)
            else:
                if isinstance(data, dict):
                    return self._send_json(401, {"success": False, "message": "Invalid card number or PIN."})
                else:
                    return self._send_html(401, "<h2 style='color:red;'>Invalid card number or PIN.</h2><a href='/login.html'>Back</a>")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
