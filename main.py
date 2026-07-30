def main():
    print("Hello from backend!")


if __name__ == "__main__":
    main()
from fastapi import FastAPI

# 1. สร้างตัวแปร app
app = FastAPI(
    title="AI Ecosystem API",
    version="1.0.0"
)

# 2. เพิ่ม Endpoint ทดสอบ /readyz
@app.get("/readyz")
def readiness_check():
    return {
        "status": "ready",
        "components": {
            "database": "ok",
            "storage": "ok"
        }
    }

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

def main():
    print("Hello from backend!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)