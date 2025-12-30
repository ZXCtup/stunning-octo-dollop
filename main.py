# main.py
# Main Telegram bot file

import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, SUBSCRIPTION_PLANS, ADMIN_IDS
from database import create_tables, add_user, get_user, update_subscription, get_referral_code, get_active_subscription
from config import DATABASE_FILE
from api_client import api_client
import random
import string

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_password(length=12):
    """Generate a random password with only letters and digits."""
    characters = string.ascii_letters + string.digits  # Only letters and digits, no special characters
    return ''.join(random.choice(characters) for i in range(length))

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("Профиль", callback_data='profile')],
        [InlineKeyboardButton("Реферальная ссылка", callback_data='referral')],
        [InlineKeyboardButton("Купить подписку", callback_data='buy_subscription')],
        [InlineKeyboardButton("Помощь", callback_data='help')]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("Админ панель", callback_data='admin_panel')])

    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    # Add user to database
    add_user(user_id, username, first_name, last_name)

    reply_markup = get_main_menu_keyboard(user_id)

    text = f"Привет, {first_name}! Добро пожаловать в Blitz VPN Bot.\n\nВыберите действие:"

    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_main_menu(query):
    """Show main menu."""
    user_id = query.from_user.id
    user = query.from_user

    reply_markup = get_main_menu_keyboard(user_id)

    text = f"Привет, {user.first_name}! Добро пожаловать в Blitz VPN Bot.\n\nВыберите действие:"

    await query.edit_message_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == 'profile':
        await show_profile(query, user_id)
    elif data == 'referral':
        await show_referral(query, user_id)
    elif data == 'buy_subscription':
        await show_subscription_plans(query)
    elif data == 'help':
        await show_help(query)
    elif data == 'admin_panel':
        if user_id in ADMIN_IDS:
            await show_admin_panel(query)
        else:
            keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("У вас нет доступа к админ панели.", reply_markup=reply_markup)
    elif data == 'back_to_menu':
        await show_main_menu(query)
    elif data == 'show_keys':
        await show_keys(query, user_id)
    elif data.startswith('buy_'):
        plan = data.split('_')[1]
        await process_purchase(query, user_id, plan)

async def show_profile(query, user_id):
    """Show user profile."""
    user = get_user(user_id)
    subscription = get_active_subscription(user_id)
    
    keyboard = [
        [InlineKeyboardButton("Ключи", callback_data='show_keys')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user:
        status = "Активна" if subscription else "Не активирована"
        text = f"Профиль:\nID: {user[0]}\nИмя пользователя: {user[1]}\nИмя: {user[2]} {user[3] or ''}\nСтатус подписки: {status}"
    else:
        text = "Профиль не найден."

    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_keys(query, user_id):
    """Show user's VPN keys."""
    subscription = get_active_subscription(user_id)
    
    keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if subscription:
        plan, device_limit, vpn_username, vpn_password, vpn_key, end_date = subscription
        if vpn_key:
            text = f"Ваш VPN ключ:\n\n📝 <b>Ключ:</b>\n<code>{vpn_key}</code>\n\n⏰ <b>Действительно до:</b> {end_date}"
        else:
            text = "Ключ не найден. Обратитесь в поддержку."
    else:
        text = "У вас нет активной подписки."

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

async def show_referral(query, user_id):
    """Show referral link."""
    referral_code = get_referral_code(user_id)
    referral_link = f"https://t.me/your_bot_username?start={referral_code}"
    
    keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"Ваша реферальная ссылка:\n{referral_link}\n\nПригласите друзей и получите бонусы!"

    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_subscription_plans(query):
    """Show available subscription plans."""
    keyboard = []
    for plan, details in SUBSCRIPTION_PLANS.items():
        device_text = f", {details['device_limit']} устройств" if details['device_limit'] else ", безлимит устройств"
        traffic_text = f"{details['traffic_gb']}GB" if details['traffic_gb'] else "безлимит трафика"
        button_text = f"{plan.capitalize()} - {details['price']}$ ({traffic_text}{device_text}, {details['expiration_days']} дней)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'buy_{plan}')])

    # Add back button
    keyboard.append([InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Выберите план подписки:"

    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def process_purchase(query, user_id, plan):
    """Process subscription purchase."""
    details = SUBSCRIPTION_PLANS.get(plan)
    if not details:
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Неверный план.", reply_markup=reply_markup)
        return

    # Generate username and password
    username = f"user_{user_id}_{plan}"
    password = generate_password()

    # Create user via API
    try:
        logger.info(f"Starting purchase process for user {user_id}, plan: {plan}")
        
        # Prepare traffic_limit - API might expect GB instead of bytes
        traffic_limit_gb = details['traffic_gb'] if details['traffic_gb'] else 0
        
        response = api_client.create_user(
            username=username,
            password=password,
            traffic_limit=traffic_limit_gb,  # Send GB directly
            expiration_days=details['expiration_days'],
            unlimited=details['device_limit'] is None,  # True if unlimited devices
            note=f"Telegram user {user_id} - Plan: {plan}"
        )
        
        logger.info(f"User creation response: {response}")
        
        # Update database after successful creation
        from datetime import datetime, timedelta
        end_date = datetime.now() + timedelta(days=details['expiration_days'])
        
        # Get user URI
        uri_response = None
        vpn_key = ""
        try:
            uri_response = api_client.get_user_uri(username)
            logger.info(f"URI response: {uri_response}")
            
            # Use IPv4 key only
            if uri_response.get('ipv4'):
                vpn_key = uri_response['ipv4']
        except Exception as e:
            logger.error(f"Error getting user URI: {e}")
        
        # Save subscription to database with VPN credentials
        update_subscription(user_id, plan, details['device_limit'], end_date.isoformat(), 
                           vpn_username=username, vpn_password=password, vpn_key=vpn_key)
        
        # Get user URI
        try:
            if not uri_response:  # Only get if not already fetched
                uri_response = api_client.get_user_uri(username)
                logger.info(f"URI response: {uri_response}")
            
            key = vpn_key if vpn_key else None
            
            # Use IPv4 key only
            if not key and uri_response.get('ipv4'):
                key = uri_response['ipv4']
            
            if key:
                keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = f"✅ Подписка активирована!\n\n📝 <b>Ваш ключ:</b>\n<code>{key}</code>\n\nСохраните его в безопасном месте."
            else:
                # If no keys available, show username and password as fallback
                logger.warning(f"No keys available in response: {uri_response}")
                keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = f"✅ Подписка активирована!\n\n👤 <b>Ваше имя пользователя:</b> {username}\n🔑 <b>Пароль:</b> {password}\n\n⚠️ Используйте эти учетные данные для входа в VPN."
        except Exception as e:
            logger.error(f"Error getting user URI: {e}")
            # If URI fails but user was created, still show success with credentials
            keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"✅ Подписка активирована!\n\n👤 <b>Ваше имя пользователя:</b> {username}\n🔑 <b>Пароль:</b> {password}\n\nПожалуйста, используйте эти учетные данные для входа."
            
    except Exception as e:
        logger.error(f"Error processing purchase: {e}")
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"❌ Ошибка при активации подписки:\n{str(e)}\n\nПожалуйста, свяжитесь с поддержкой."

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')

async def show_help(query):
    """Show help information."""
    keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "Помощь:\n\n- Профиль: Просмотр информации о вашем аккаунте\n- Реферальная ссылка: Получите ссылку для приглашения друзей\n- Купить подписку: Выберите и оплатите план\n\nЕсли есть вопросы, обратитесь в поддержку."
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def show_admin_panel(query):
    """Show admin panel."""
    try:
        # Get server status
        status = api_client.get_server_status()
        online_users = status.get('online_users', 'N/A')
        cpu_usage = status.get('cpu_usage', 'N/A')
        ram_usage = status.get('ram_usage', 'N/A')

        # Get user count from database
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()

        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"Админ панель:\n\nОбщее количество пользователей: {user_count}\nОнлайн пользователей: {online_users}\nCPU: {cpu_usage}\nRAM: {ram_usage}"
    except Exception as e:
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Ошибка получения данных: {e}"

    await query.edit_message_text(text=text, reply_markup=reply_markup)

def main() -> None:
    """Start the bot."""
    # Create database tables
    create_tables()

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()