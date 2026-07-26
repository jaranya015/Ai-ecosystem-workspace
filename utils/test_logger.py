from logger import setup_logger

logger = setup_logger()

def run_test():
    logger.info("เริ่มต้นการทำงานของระบบ AI Workspace")
    logger.debug("รายละเอียดสำหรับการ Debug ระบบ...")
    try:
        result = 10 / 0
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}", exc_info=True)

if __name__ == "__main__":
    run_test()