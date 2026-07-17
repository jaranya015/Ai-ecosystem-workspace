from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. กำหนดชื่อตัวแปรที่ต้องการ พร้อมชนิดข้อมูล (และกำหนดค่า Default ไว้เผื่อไม่มีใน .env)
    PROJECT_NAME: str = "My Awesome Backend"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    SECRET_KEY: str = "super-secret-key-change-me-in-production"

    LABEL_STUDIO_URL: str = "http://localhost:8080"
    LABEL_STUDIO_API_KEY: str

    # 2. ตั้งค่าให้ Pydantic อ่านค่าจากไฟล์ .env อัตโนมัติ
    model_config = SettingsConfigDict(
        env_file=".env",            # อ่านไฟล์ชื่อ .env
        env_file_encoding="utf-8",
        extra="ignore"             # ข้ามตัวแปรอื่นใน .env ที่ไม่ได้กำหนดไว้ข้างบน
    )

# สร้าง instance สำหรับนำไปเรียกใช้งานในที่อื่นๆ ของโปรเจกต์
settings = Settings()