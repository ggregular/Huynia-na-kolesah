from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Drone Control System API")


# Функція для підключення до твоєї бази
def get_db_connection():
    conn = sqlite3.connect('newdb.db')  # Переконайся, що файл лежить в тій же папці
    conn.row_factory = sqlite3.Row
    return conn


# Модель даних для замовлення (те, що прийде з сайту)
class TaskCreate(BaseModel):
    sender_id: str
    from_location_id: int
    to_location_id: int


# 1. Ендпоінт для створення нового завдання
@app.post("/tasks/")
def create_task(task: TaskCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (sender_id, from_location_id, to_location_id, status) VALUES (?, ?, ?, ?)",
        (task.sender_id, task.from_location_id, task.to_location_id, 'pending')
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return {"message": "Завдання створено", "task_id": task_id}


# 2. Ендпоінт для дрона: отримати наступне завдання
@app.get("/drone/next_task")
def get_next_task():
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at LIMIT 1").fetchone()

    if not task:
        conn.close()
        return {"message": "Завдань немає"}

    # Одразу міняємо статус на 'in_progress'
    conn.execute("UPDATE tasks SET status = 'in_progress' WHERE id = ?", (task['id'],))
    conn.commit()
    conn.close()
    return task


# 3. Ендпоінт для безпеки: логування газу (від дрона)
class GasLog(BaseModel):
    level: float


@app.post("/drone/log_gas")
def log_gas(data: GasLog):
    status = "Норма" if data.level < 0.5 else "ТРИВОГА"
    conn = get_db_connection()
    conn.execute("INSERT INTO safety_logs (gas_level, status) VALUES (?, ?)", (data.level, status))
    conn.commit()
    conn.close()
    return {"status": status}