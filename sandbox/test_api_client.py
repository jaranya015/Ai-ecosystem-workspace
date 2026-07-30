import requests

BASE_URL = "http://localhost:8000"

def test_health():
    try:
        # ทดสอบ Liveness / Readiness
        response = requests.get(f"{BASE_URL}/readyz")
        print(" Readyness Status Code:", response.status_code)
        print(" Response:", response.json())
    except Exception as e:
        print(" Connection Error: ไม่สามารถเชื่อมต่อกับ Server ได้ กรุณาเช็กว่าเปิด uvicorn หรือยัง")
        print(" Error detail:", e)

if __name__ == "__main__":
    print("--- Starting API Connection Test ---")
    test_health()