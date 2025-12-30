# database.py
# Module for handling SQLite database operations

import sqlite3
from config import DATABASE_FILE

def create_tables():
    """Create necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            subscription_status TEXT DEFAULT 'Не активирована',
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            device_limit INTEGER,
            vpn_username TEXT,
            vpn_password TEXT,
            vpn_key TEXT,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Add migration for new columns
    try:
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN vpn_username TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN vpn_password TEXT")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN vpn_key TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name, referral_code=None, referred_by=None):
    """Add a new user to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name, referral_code, referred_by))

    conn.commit()
    conn.close()

def get_user(user_id):
    """Get user information by user_id."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    conn.close()
    return user

def update_subscription(user_id, plan, device_limit, end_date, vpn_username="", vpn_password="", vpn_key=""):
    """Update user's subscription."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO subscriptions (user_id, plan, device_limit, end_date, vpn_username, vpn_password, vpn_key)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, plan, device_limit, end_date, vpn_username, vpn_password, vpn_key))

    cursor.execute('''
        UPDATE users SET subscription_status = 'active' WHERE user_id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()

def get_referral_code(user_id):
    """Generate or get referral code for user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        referral_code = result[0]
    else:
        referral_code = f"REF{user_id}"
        cursor.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (referral_code, user_id))
        conn.commit()

    conn.close()
    return referral_code

def get_active_subscription(user_id):
    """Get user's active subscription with VPN details."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT plan, device_limit, vpn_username, vpn_password, vpn_key, end_date
        FROM subscriptions
        WHERE user_id = ? AND end_date > datetime('now')
        ORDER BY end_date DESC
        LIMIT 1
    ''', (user_id,))

    subscription = cursor.fetchone()
    conn.close()
    return subscription