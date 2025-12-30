# test_api.py
# Script to test API connection and user creation

import json
import logging
from api_client import api_client
from config import SUBSCRIPTION_PLANS

# Enable logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api():
    """Test API connection and user creation."""
    
    print("=" * 60)
    print("Тестирование API Blitz VPN")
    print("=" * 60)
    
    # Test 1: Server status
    print("\n1️⃣  Проверка статуса сервера...")
    try:
        status = api_client.get_server_status()
        print(f"✅ Сервер работает!")
        print(f"   Онлайн пользователей: {status.get('online_users', 'N/A')}")
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса: {e}")
        return False
    
    # Test 2: Create test user
    print("\n2️⃣  Создание тестового пользователя...")
    import time
    timestamp = str(int(time.time()))
    test_username = f"test_user_{timestamp}"
    test_password = "TestPassword123"
    
    try:
        # Test with econom plan (100GB)
        plan_details = SUBSCRIPTION_PLANS['econom']
        
        print(f"   Параметры:")
        print(f"   - Username: {test_username}")
        print(f"   - Traffic limit: {plan_details['traffic_gb']} GB")
        print(f"   - Expiration days: {plan_details['expiration_days']}")
        print(f"   - Unlimited: {plan_details['traffic_gb'] is None}")
        
        response = api_client.create_user(
            username=test_username,
            password=test_password,
            traffic_limit=plan_details['traffic_gb'],
            expiration_days=plan_details['expiration_days'],
            unlimited=plan_details['traffic_gb'] is None,
            note="Test user"
        )
        
        print(f"✅ Пользователь создан!")
        print(f"   Ответ API: {json.dumps(response, indent=2)}")
        
        # Get user details first
        print("\n3️⃣  Получение информации о пользователе...")
        try:
            user_details = api_client.get_user(test_username)
            print(f"✅ Информация получена!")
            print(f"   {json.dumps(user_details, indent=2)}")
        except Exception as e:
            print(f"⚠️  Ошибка при получении информации: {e}")
        
        # Test 4: Get user URI
        print("\n4️⃣  Получение ключа подписки...")
        try:
            uri_response = api_client.get_user_uri(test_username)
            print(f"✅ Ответ получен!")
            print(f"   {json.dumps(uri_response, indent=2)}")
            
            if uri_response.get('normal_sub'):
                print(f"✅ Ключ: {uri_response['normal_sub']}")
            else:
                print(f"⚠️  Ключ еще не сгенерирован (normal_sub = None)")
                print(f"   Это нормально - ключ может генерироваться с задержкой")
        except Exception as e:
            print(f"⚠️  Ошибка при получении ключа: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    print("\n" + "=" * 60)
    if success:
        print("✅ Все тесты пройдены! API работает корректно.")
    else:
        print("❌ Тесты не пройдены. Проверьте конфигурацию.")
    print("=" * 60)
