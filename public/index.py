#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import cgitb
cgitb.enable()  # برای نمایش خطاها در مرورگر (خیلی مفید برای دیباگ)

from app.controllers.AccountController import AccountController
from app.models.AccountModel import create_user, login_user

print("Content-type: text/html\n")  # برای خروجی HTML به مرورگر

form = cgi.FieldStorage()  # گرفتن اطلاعات فرم

action = form.getvalue("action")  # تشخیص نوع درخواست (create یا login)

# ✅ اگر کاربر می‌خواهد اکانت جدید بسازد
if action == "create":
    first_name = form.getvalue("first_name")
    last_name = form.getvalue("last_name")
    phone = form.getvalue("phone")
    address = form.getvalue("address")
    postal_code = form.getvalue("postal_code")
    pin = form.getvalue("pin")

    # اعتبارسنجی اولیه
    if not pin or len(pin) != 4 or not pin.isdigit():
        print("<h1 style='color:red;'>❌ PIN must be exactly 4 digits!</h1>")
        print('<a href="../create_account.html">Back</a>')
    else:
        success, message, card_number = create_user(
            first_name, last_name, phone, address, postal_code, pin
        )
        if success:
            print("<h1 style='color:green;'>✅ Account Created Successfully!</h1>")
            print(f"<p>{message}</p>")
            print(f"<p>Your card number: <strong>{card_number}</strong></p>")
            print("<p>Keep it safe and use your PIN to log in.</p>")
            print('<a href="../login.html">Go to Login</a>')
        else:
            print(f"<h1 style='color:red;'>❌ {message}</h1>")
            print('<a href="../create_account.html">Back</a>')

# ✅ اگر کاربر می‌خواهد لاگین کند
elif action == "login":
    card_number = form.getvalue("card_number")
    pin = form.getvalue("pin")

    if not card_number or not pin:
        print("<h1 style='color:red;'>❌ Please enter both card number and PIN!</h1>")
        print('<a href="../login.html">Back</a>')
    else:
        user = login_user(card_number, pin)
        if user:
            print(f"<h1 style='color:green;'>✅ Welcome, {user['first_name']} {user['last_name']}!</h1>")
            print(f"<p>💳 Card Number: {user['card_number']}</p>")
            print(f"<p>💰 Balance: ${user['balance']:.2f}</p>")
            print('<a href="../dashboard.html">Go to Dashboard</a>')
        else:
            print("<h1 style='color:red;'>❌ Invalid card number or PIN!</h1>")
            print('<a href="../login.html">Back</a>')

# ✅ اگر هیچ اکشنی مشخص نشده (باز شدن مستقیم فایل)
else:
    print('<meta http-equiv="refresh" content="0; URL=../index.html">')
