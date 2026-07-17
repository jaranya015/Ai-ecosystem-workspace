
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

def test_app_settings():
    print("=" * 50)
    print("🔌 TESTING PROJECT SETTINGS")
    print("=" * 50)
    print(f"Project Name : {settings.PROJECT_NAME}")
    print(f"API Prefix   : {settings.API_V1_STR}")
    print(f"Database URL : {settings.DATABASE_URL}")
    print(f"Secret Key   : {settings.SECRET_KEY}")
    print("=" * 50)
    print("✅ Load settings from .env successfully!")

if __name__ == "__main__":
    test_app_settings()