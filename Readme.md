#  FastAPI Todo Application (Full Stack with Authentication)

A full-stack Todo application built using **FastAPI**, **PostgreSQL (Supabase)**, and **Jinja2 templates**, featuring authentication, CRUD operations, and testing.

This project demonstrates **real-world backend engineering concepts** including:
- JWT Authentication 
- Dependency Injection 
- Database Integration (Supabase PostgreSQL) 
- Role-Based Access Control (User & Admin)
- Modular FastAPI Architecture 
- Testing with Pytest 

---

## 🚀 Features

-  User Registration & Login  
-  Secure JWT-based Authentication  
-  Cookie-based Session Handling  
-  Full CRUD Operations (Todos)  
-  Protected Routes  
-  Supabase PostgreSQL Integration  
-  Modular Code Structure  
-  Unit & Integration Testing  

---

## 🛠️ Tech Stack

- **Backend:** FastAPI  
- **Database:** PostgreSQL (Supabase)  
- **ORM:** SQLAlchemy  
- **Authentication:** JWT (PyJWT)  
- **Frontend:** Jinja2 Templates (Server-Side Rendering)  
- **Testing:** Pytest  
- **Server:** Uvicorn  
- **Containerization:** Docker  
---

## 📸 Application Screenshots

### 🔐 Login Page
![Login](./assets/login.png)

### 📝 Register Page
![Register](./assets/register.png)

### 📋 Todo Dashboard
![Todos](./assets/todos.png)

### ✏️ Edit Todo
![Edit](./assets/edit.png)

### 🗄️ Database Schema
![Schema](./assets/schema.png)

### 📊 Tables View
![Tables](./assets/tables.png)

---


# 📂 Project Structure
```text
TodoApp/
│
├── Todoapp/
│ ├── routers/
│ │ ├── auth.py
│ │ ├── todos.py
│ │ ├── users.py
│ │ └── admin.py
│ │
│ ├── templates/
│ ├── static/
│ ├── database.py
│ ├── models.py
│ └── main.py
│
├── test/
├── .env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```
---

##  Authentication Flow (JWT)

```text
User Login
↓
FastAPI /token
↓
authenticate_user()
↓
create_access_token()
↓
JWT Token Generated
↓
Stored in Browser Cookie
↓
Sent with every request
↓
get_current_user()
↓
User Authenticated ✅
```
---

## Cookie Authentication Flow
```text
Login success
   ↓
Token stored in cookie
   ↓
Browser sends request
   ↓
Cookie auto-attached
   ↓
Backend verifies user
   ↓
Access granted ✅
```
---

## Setup Instructions

1️⃣ Clone Repository
```bash
git clone <your-repo-url>
cd todoapp

---

2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate


---
3️⃣ Install Dependencies
pip install -r requirements.txt


---
4️⃣ Setup Environment Variables

Create .env file:

DATABASE_URL=postgresql://username:password@host:port/database
SECRET_KEY=your_secret_key


---
5️⃣ Run Application
uvicorn Todoapp.main:app --reload

App runs on:

http://127.0.0.1:8000

```
---
## Key Learnings
- FastAPI Dependency Injection
- JWT Authentication
- PostgreSQL + Supabase Integration
- Clean Backend Architecture
- Testing with Pytest
- Cookie-based auth handling

---
## Future Improvements
- React Frontend Integration
- Pagination & Filtering

---
📌 Author

Namit Jain
Machine Learning & AI Engineer

---

