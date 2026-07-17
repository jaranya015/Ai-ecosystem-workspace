import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. โหลดการตั้งค่าจาก .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# 2. สร้าง Engine และ Session
engine = create_engine(DATABASE_URL, echo=True)  # echo=True เพื่อให้แสดง SQL Logs ใน Terminal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. นิยามโครงสร้างตาราง Model Students
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer)
    major = Column(String(100))

    def __repr__(self):
        return f""

# === ฟังก์ชันสำหรับทดสอบตามโจทย์ ===

# A. สร้างตาราง (Create Table)
def create_table():
    print("\n🔨 --- 1. Creating Table: students ---")
    Base.metadata.create_all(bind=engine)
    print("✅ Table created successfully.")

# B. เพิ่มข้อมูล (Insert Data)
def insert_data():
    print("\n➕ --- 2. Inserting Data ---")
    db = SessionLocal()
    try:
        student1 = Student(name="John Doe", age=21, major="Computer Science")
        student2 = Student(name="Jane Smith", age=20, major="Information Technology")
        db.add_all([student1, student2])
        db.commit()
        print(f"✅ Added students: {student1}, {student2}")
    finally:
        db.close()

# C. อัปเดตข้อมูล (Update Data)
def update_data():
    print("\n✏️ --- 3. Updating Data ---")
    db = SessionLocal()
    try:
        # ค้นหาคนแรกที่เจอเพื่ออัปเดต
        student = db.query(Student).filter(Student.name == "John Doe").first()
        if student:
            print(f"Before update: {student}")
            student.age = 22
            student.major = "Data Science"
            db.commit()
            # รีเฟรชข้อมูล
            db.refresh(student)
            print(f"✅ After update : {student}")
        else:
            print("❌ Student 'John Doe' not found.")
    finally:
        db.close()

# D. ลบข้อมูล (Delete Data)
def delete_data():
    print("\n🗑️ --- 4. Deleting Data ---")
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.name == "Jane Smith").first()
        if student:
            db.delete(student)
            db.commit()
            print("✅ Deleted Jane Smith successfully.")
        else:
            print("❌ Student 'Jane Smith' not found.")
    finally:
        db.close()

# E. ลบตารางทิ้ง (Delete Table)
def delete_table():
    print("\n🔥 --- 5. Dropping Table: students ---")
    Base.metadata.drop_all(bind=engine)
    print("✅ Table dropped successfully.")

# รันการทดสอบทั้งหมดเรียงลำดับ
if __name__ == "__main__":
    print("🚀 Starting PostgreSQL and SQLAlchemy Test...")
    try:
        create_table()
        insert_data()
        update_data()
        delete_data()
        delete_table()
        print("\n🎉 All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")