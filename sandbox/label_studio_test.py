from label_studio_sdk.client import LabelStudio
from core.config import settings  # ดึงค่า URL และ API KEY มาจาก pydantic Settings ของคุณ

def test_label_studio():
    # 1. สร้าง client เชื่อมต่อ Label Studio
    print("🔌 Connecting to Label Studio...")
    ls = LabelStudio(
        base_url=settings.LABEL_STUDIO_URL, 
        api_key=settings.LABEL_STUDIO_API_KEY
    )

# 2. List all projects 
    print("\n📁 --- All Projects in Label Studio ---")
    
    # แปลงผลลัพธ์จาก Pager ให้กลายเป็น List ปกติ
    projects_list = list(ls.projects.list())
    
    if not projects_list:
        print("❌ No projects found.")
        return

    for project in projects_list:
        print(f"🔹 ID: {project.id} | Name: {project.title} | Description: {project.description}")

    # 3. เลือกตัวอย่างโปรเจกต์แรกมา 1 อัน โดยดึงจาก List ที่เราแปลงแล้ว
    target_project = projects_list[0]
    print(f"\n🎯 --- Tasks inside Project: '{target_project.title}' (ID: {target_project.id}) ---")
    
    # ดึง tasks ทั้งหมดภายในโปรเจกต์นั้น และแปลงเป็น List เช่นกัน
    tasks_list = list(ls.tasks.list(project=target_project.id))
    
    if not tasks_list:
        print("ℹ️ This project has no tasks.")
        return

    for task in tasks_list:
        print(f"🔸 Task ID: {task.id} | Data: {task.data} | Created At: {task.created_at}")

    # 3. เลือกตัวอย่างโปรเจกต์แรกมา 1 อัน เพื่อดึง tasks 
    target_project = projects[0]
    print(f"\n🎯 --- Tasks inside Project: '{target_project.title}' (ID: {target_project.id}) ---")
    
    # ดึง tasks ทั้งหมดภายในโปรเจกต์นั้น
    tasks = ls.tasks.list(project=target_project.id)
    
    if not tasks:
        print("ℹ️ This project has no tasks.")
        return

    for task in tasks:
        print(f"🔸 Task ID: {task.id} | Data: {task.data} | Created At: {task.created_at}")

if __name__ == "__main__":
    test_label_studio()