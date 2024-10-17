# Task Management Software

A web application built with FastAPI to manage tasks efficiently. It includes user registration, authentication, and CRUD operations for tasks.

## Features
- User registration and login
- Create, update, delete, and retrieve tasks
- Admin privileges for managing tasks

## Technologies Used
- FastAPI
- MongoDB
- JWT for authentication
- Bcrypt for password hashing

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd task_management


Create a virtual environment and activate it.

## Install required packages
pip install fastapi[all] pymongo bcrypt python-dotenv


## API Endpoints
Register: POST /register
Login: POST /login
Create Task: POST /tasks
Get Task: GET /tasks/{task_id}
Update Task: PUT /tasks/{task_id}
Delete Task: DELETE /tasks/{task_id}


## Testing
pytest test_tasks.py