# config.py
# Configuration file for the Telegram bot

import os
from dotenv import load_dotenv
load_dotenv()
# Telegram Bot Token (get from @BotFather)
TELEGRAM_BOT_TOKEN = "8228046986:AAE0No9cx6GVD7FGLt5x1qr1xUvf6NusAUQ"

# Blitz VPN API Configuration
BLITZ_API_BASE_URL = os.getenv('BLITZ_API_BASE_URL')  # Replace with actual URL
BLITZ_API_USERNAME = os.getenv('BLITZ_API_USERNAME')
BLITZ_API_PASSWORD = os.getenv('BLITZ_API_PASSWORD')

# Database file
DATABASE_FILE = 'bot_database.db'

# Admin user IDs (list of Telegram user IDs who have admin access)
ADMIN_IDS = [1226699653 ]  # Replace with actual admin user IDs

# Subscription plans
SUBSCRIPTION_PLANS = {
    'econom': {'traffic_gb': 100, 'expiration_days': 30, 'device_limit': None, 'price': 5.0},  # Эконом: 100GB, без лимита устройств
    'basic': {'traffic_gb': None, 'expiration_days': 30, 'device_limit': 1, 'price': 10.0},   # Базовый: без лимита трафика, 1 устройство
    'premium': {'traffic_gb': None, 'expiration_days': 30, 'device_limit': None, 'price': 30.0} # Premium: без лимита трафика и устройств
}