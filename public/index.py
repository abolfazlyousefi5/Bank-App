#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import json
from app.controllers.AccountController import AccountController

print("Content-Type: application/json\n")  # خروجی JSON برای تعامل با فرانت‌اند

controller = AccountController()
form = cgi.FieldStorage()

action = form.getvalue("action")

# پاسخ نهایی
response = {"status": "error", "message": "Invalid action"}

try:
    if action == "create":
        username = form.getvalue("username")
        password = form.getvalue("password")

        if controller.create_account(username, password):
            response = {"status": "success",
                        "message": "Account created successfully!"}
        else:
            response = {"status": "error",
                        "message": "Username already exists!"}

    elif action == "login":
        username = form.getvalue("username")
        password = form.getvalue("password")

        user = controller.login(username, password)
        if user:
            response = {
                "status": "success",
                "message": "Login successful!",
                "user": user
            }
        else:
            response = {"status": "error", "message": "Invalid credentials!"}

# index.py (فقط بخش transfer)
    elif action == "transfer":
        from_user = form.getvalue("from_user") or ""
        to_user = form.getvalue("to_user") or ""
        amt_raw = form.getvalue("amount") or "0"
        try:
            amount = float(amt_raw)
        except Exception:
            amount = 0.0

        # فرض می‌کنیم controller.transfer_money(from_user, to_user, amount) وجود دارد
        result = controller.transfer_money(from_user, to_user, amount)
        # نمایش خروجی ساده به مرورگر
        if result.get("success"):
            print(f"<h1>✅ {result.get('message')}</h1>")
        else:
            print(f"<h1>❌ {result.get('message')}</h1>")
        print('<a href="../app/public/dashboard.html">Back to Dashboard</a>')

    elif action == "get_balance":
        username = form.getvalue("username")
        balance = controller.get_balance(username)
        response = {"status": "success", "balance": balance}

except Exception as e:
    response = {"status": "error", "message": str(e)}

# چاپ خروجی JSON
print(json.dumps(response))
