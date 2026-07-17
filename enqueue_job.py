# backend/enqueue_job.py
import asyncio
from arq import create_pool
from arq.connections import RedisSettings

async def main():
    # เชื่อมต่อกับ Redis Pool
    redis = await create_pool(RedisSettings(host="localhost", port=6379))
    
    # ส่งงานชื่อ 'simple_work' พร้อมส่งข้อมูลอาร์กิวเมนต์เข้าไปในคิว
    print("🚀 Enqueuing a simple_work job...")
    job = await redis.enqueue_job("simple_work", "Hello World! This is Assignment #03")
    
    print(f"✨ Job enqueued. Job ID: {job.job_id}")

if __name__ == "__main__":
    asyncio.run(main())