# api_client.py
# Module for interacting with Blitz VPN API

import requests
import logging
from config import BLITZ_API_BASE_URL, BLITZ_API_USERNAME, BLITZ_API_PASSWORD

logger = logging.getLogger(__name__)

class BlitzAPIClient:
    def __init__(self):
        self.base_url = BLITZ_API_BASE_URL.rstrip('/')  # Remove trailing slash
        self.username = BLITZ_API_USERNAME
        self.password = BLITZ_API_PASSWORD
        self.session = requests.Session()
        self.token = None
        self.login()

    def login(self):
        """Authenticate with the API."""
        try:
            # Try to login and get authentication token
            logger.info(f"Attempting login with username: {self.username}")
            
            # Method 1: Try token-based auth (if API provides one)
            login_url = f"{self.base_url}/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(login_url, data=login_data, timeout=10)
            logger.info(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                # Store session cookies for future requests
                logger.info("Login successful - session cookies stored")
                return
            
            # Method 2: Try basic auth if login endpoint fails
            logger.warning(f"Login endpoint returned {response.status_code}, trying basic auth")
            self.session.auth = (self.username, self.password)
            
        except Exception as e:
            logger.warning(f"Login failed: {e}, will try basic auth")
            # Fallback to basic auth
            self.session.auth = (self.username, self.password)

    def create_user(self, username, password, traffic_limit, expiration_days, unlimited=False, note=""):
        """Create a new user via API.
        
        Args:
            username: Username for the new user
            password: Password for the new user
            traffic_limit: Traffic limit in bytes (0 if unlimited)
            expiration_days: Days until expiration
            unlimited: If True, user has unlimited traffic
            note: Optional note for the user
        """
        from datetime import datetime
        
        url = f"{self.base_url}/api/v1/users/"
        
        # Build request data according to API documentation
        data = {
            "username": username,
            "password": password,
            "expiration_days": int(expiration_days),
            "unlimited": bool(unlimited),
            "note": note
        }
        
        # Set traffic_limit in bytes
        if unlimited:
            # Don't include traffic_limit for unlimited users
            pass
        elif traffic_limit and traffic_limit > 0:
            data["traffic_limit"] = int(traffic_limit)
        else:
            data["traffic_limit"] = 0
        
        # Add creation_date if needed (optional, uses current date if not provided)
        # data["creation_date"] = datetime.now().isoformat()
        
        try:
            logger.info(f"Creating user {username} with URL: {url}")
            logger.info(f"Request data: {data}")
            response = self.session.post(url, json=data, timeout=10, verify=False)
            logger.info(f"API response status: {response.status_code}, body: {response.text}")
            
            # Handle specific error codes
            if response.status_code == 409:
                error_data = response.json()
                error_msg = error_data.get('detail', 'User already exists')
                logger.error(f"User already exists: {error_msg}")
                raise Exception(f"User already exists: {error_msg}")
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    logger.error(f"Validation error details: {error_data}")
                    if 'detail' in error_data:
                        raise Exception(f"API Validation Error: {error_data['detail']}")
                except:
                    pass
            
            response.raise_for_status()  # Raise exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {e}")

    def get_user_uri(self, username):
        """Get user URI."""
        url = f"{self.base_url}/api/v1/users/{username}/uri"
        try:
            response = self.session.get(url, timeout=10, verify=False)
            logger.info(f"Get URI response status: {response.status_code}, body: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user URI: {e}")
            raise Exception(f"Failed to get user URI: {e}")
    
    def get_user(self, username):
        """Get user details."""
        url = f"{self.base_url}/api/v1/users/{username}"
        try:
            response = self.session.get(url, timeout=10, verify=False)
            logger.info(f"Get user response status: {response.status_code}, body: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user details: {e}")
            raise Exception(f"Failed to get user details: {e}")

    def get_server_status(self):
        """Get server status."""
        url = f"{self.base_url}/api/v1/server/status"
        try:
            response = self.session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get server status: {e}")
            raise Exception(f"Failed to get server status: {e}")

# Global client instance
api_client = BlitzAPIClient()