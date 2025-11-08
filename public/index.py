#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
from app.controllers.AccountController import AccountController

controller = AccountController()

print("Content-type: text/html\n")  # مهم: برای نمایش HTML در مرورگر

form = cgi.FieldStorage()  # گرفتن اطلاعات فرم

action = form.getvalue("action")  # مشخص کردن عملیات

# اگر فرم ایجاد حساب فرستاده شده
if action == "create":
    username = form.getvalue("username")
    password = form.getvalue("password")
    if controller.create_account(username, password):
        print(f"<h1>✅ Account created successfully for {username}</h1>")
    else:
        print(f"<h1>❌ Failed to create account. Username may exist.</h1>")
    print('<a href="../app/views/index.html">Back to Home</a>')

# اگر فرم ورود فرستاده شده
elif action == "login":
    username = form.getvalue("username")
    password = form.getvalue("password")
    user = controller.login(username, password)
    if user:
        balance = controller.get_balance(username)
        print(f"<h1>✅ Welcome, {username}!</h1>")
        print(f"<p>💰 Your Balance: {balance}</p>")
    else:
        print("<h1>❌ Invalid login credentials!</h1>")
    print('<a href="../app/views/index.html">Back to Home</a>')

# اگر صفحه بدون فرم باز شد
else:
    print('<meta http-equiv="refresh" content="0; URL=../app/views/index.html">')
