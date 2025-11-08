from app.models.Database import get_connection

def create_user(first_name, last_name, phone, address, postal_code, username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (first_name, last_name, phone, address, postal_code, username, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (first_name, last_name, phone, address, postal_code, username, password))
        conn.commit()
        return True, "Account created successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user
