# 🔐 Bank Management System

## سیستم مدیریت بانک

A lightweight banking application built with **Python**, **MySQL**, and
a simple **MVC-like structure**.\
یک برنامه بانکی سبک ساخته‌شده با **پایتون**، **MySQL** و یک ساختار ساده
مشابه MVC.

------------------------------------------------------------------------

## 📌 Features

## امکانات

### English

-   User registration with validation\
-   Secure login via card number + PIN\
-   Money transfer between accounts\
-   Transaction history\
-   Clean modular folder structure\
-   Fully frontend + backend separation\
-   Runs on a local HTTP server (no frameworks required)

### فارسی

-   ثبت‌نام کاربر همراه با اعتبارسنجی\
-   ورود امن با شماره کارت و پین\
-   انتقال پول بین حساب‌ها\
-   نمایش تاریخچه تراکنش‌ها\
-   ساختار پوشه‌بندی تمیز و ماژولار\
-   جداسازی کامل فرانت‌اند و بک‌اند\
-   اجرا روی یک سرور محلی بدون نیاز به فریم‌ورک

------------------------------------------------------------------------

## 📁 Project Structure

## ساختار پروژه

    project/
    ├── app/                  
    │   ├── controllers/
    |    __pycache__
    │   │   └── AccountController.py
    │   ├── models/
    |    __pycache__
    │   │   ├── Database.py
    │   │   └── AccountModel.py
    ├── public/
    │   ├── css/
    │   │   └── style.css
    |   ├──image/
    |        └── bank-logo.png
    |         └── icon.png     
    │   ├── create_account.html
    │   ├── login.html
    │   ├── index.html
    │   └── index.py  │
    └── database/             
    |   └── bank.db
    |──server.py
    |──README.md 

------------------------------------------------------------------------

## 🚀 How to Run

## چگونه اجرا کنیم

### English

1.  Install Python 3\

2.  Run the server:

        python server.py

3.  Open in browser:

        http://localhost:8000

### فارسی

1.  پایتون ۳ را نصب کنید\

2.  این دستور را اجرا کنید:

        python server.py

3.  سپس مرورگر را باز کنید:

        http://localhost:8000

------------------------------------------------------------------------

## 🧩 Technologies Used

## تکنولوژی‌های استفاده شده

-   Python (HTTPServer)
-   MySQL database
-   HTML, CSS, JavaScript
-   JSON API endpoints

------------------------------------------------------------------------

## 📜 License

MIT --- Free to use and modify.\
مجوز MIT --- آزاد برای استفاده و تغییر.

------------------------------------------------------------------------

## ✨ Author

Created by: **Abolfazl Yousefi**\
ساخته شده توسط: **ابوالفضل یوسفی**
