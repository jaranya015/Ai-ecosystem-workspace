# backend/worker_settings.py
import asyncio
from arq.connections import RedisSettings

# 1. ฟังก์ชันงานที่เราต้องการให้ประมวลผลหลังบ้าน (Background Job)
async def simple_work(ctx, job_data: str):
    # ctx คือ Context ที่ส่งผ่านมาจาก ARQ โดยอัตโนมัติ
    print("=" * 50)
    print(f"📥 [Worker] Received Job with Data: {job_data}")
    print("=" * 50)
    return f"Job completed with data: {job_data}"

# 2. ตั้งค่าการทำงานของ Worker
class WorkerSettings:
    functions = [simple_work]                  # ทะเบียนรายชื่อฟังก์ชันงานที่ Worker ตัวนี้จะรับทำ
    redis_settings = RedisSettings(host="localhost", port=6379) # การตั้งค่าเชื่อมต่อไปยัง Redis