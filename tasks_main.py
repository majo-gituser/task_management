from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import bcrypt
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
import os
import uuid

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["task_management"]
users_collection = db["users"]
tasks_collection = db["tasks"]

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# User models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False  # Add is_admin field to UserRegister model

class UserLogin(BaseModel):
    username: str
    password: str

class Task(BaseModel):
    title: str
    details: str
    due_date: datetime

class SuccessResponse(BaseModel):
    message: str

# Helper functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# User registration endpoint
@app.post("/register")
def register(user: UserRegister):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "is_admin": user.is_admin  # Store is_admin status in MongoDB
    })
    return {"message": "User successfully registered"}

# User login endpoint
@app.post("/login")
def login(user: UserLogin):
    user_db = users_collection.find_one({"username": user.username})
    if not user_db or not bcrypt.checkpw(user.password.encode('utf-8'), user_db['password']):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username, "is_admin": user_db.get("is_admin", False)})
    return {"access_token": access_token}

# Helper function to check admin privileges
def is_admin(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("is_admin", False)

# Create task endpoint
@app.post("/tasks")
def create_task(task: Task, token: str = Depends(OAuth2PasswordBearer(tokenUrl='login'))):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    # Generate a random UUID for the task_id
    task_id = str(uuid.uuid4())
    task_data = task.model_dump()
    task_data["_id"] = task_id
    task_data["created_by"] = username  # Track the creator of the task
    tasks_collection.insert_one(task_data)
    return {"message": "Task created successfully", "task_id": task_id}

# Get task by ID endpoint
@app.get("/tasks/{task_id}")
def get_task(task_id: str, token: str = Depends(OAuth2PasswordBearer(tokenUrl='login'))):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    
    # Admin users can access all tasks, others can only access their own tasks
    task = tasks_collection.find_one({"_id": task_id} if is_admin(token) else {"_id": task_id, "created_by": username})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Update task endpoint
@app.put("/tasks/{task_id}")
def update_task(task_id: str, task: Task, token: str = Depends(OAuth2PasswordBearer(tokenUrl='login'))):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    
    # Admin users can update any task, others can only update their own tasks
    filter_query = {"_id": task_id} if is_admin(token) else {"_id": task_id, "created_by": username}
    result = tasks_collection.update_one(filter_query, {"$set": task.model_dump()})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated successfully"}

# Delete task endpoint
@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, token: str = Depends(OAuth2PasswordBearer(tokenUrl='login'))):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    
    # Admin users can delete any task, others can only delete their own tasks
    filter_query = {"_id": task_id} if is_admin(token) else {"_id": task_id, "created_by": username}
    result = tasks_collection.delete_one(filter_query)
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=2060, log_level="debug")