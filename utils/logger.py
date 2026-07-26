import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str = "AI_Workspace") -> logging.Logger:
    # กำหนด Path ให้ชี้ไปที่โฟลเดอร์ logs ในหน้าหลักเสมอ
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    log_file = os.path.join(log_dir, "app.log")
    
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] (%(filename)s:%(lineno)d) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (แสดงหน้าจอ)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    # File Handler (เซฟลงไฟล์ logs/app.log)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()