# AuraLearn – Complete Setup Guide 🚀

---

## 📁 Folder Structure

```
auralearn/
│
├── app.py                          # Main Flask app
├── requirements.txt
├── database.sql                    # Run this first
│
├── static/
│   ├── css/
│   │   ├── style.css               # Global styles
│   │   └── dashboard.css           # Dashboard styles
│   ├── js/
│   │   ├── main.js                 # Animations, Three.js, GSAP
│   │   └── dashboard.js            # Chart.js, dashboard logic
│   └── uploads/                    # Auto-created by Flask
│
└── templates/
    ├── base.html                   # Shared layout (nav, footer)
    ├── index.html                  # Landing page
    ├── courses.html                # All courses listing
    │
    ├── auth/
    │   ├── login.html
    │   └── register.html
    │
    ├── student/
    │   ├── dashboard.html          # Student home
    │   ├── course_detail.html      # Course view + enroll
    │   ├── module.html             # Video + PDF viewer
    │   ├── quiz.html               # MCQ quiz with timer
    │   └── quiz_result.html        # Score + explanations
    │
    └── admin/
        ├── dashboard.html          # Admin home + charts
        ├── courses.html            # CRUD courses
        ├── modules.html            # CRUD modules
        ├── users.html              # CRUD users
        ├── questions.html          # CRUD questions
        └── zoom.html               # CRUD zoom classes
```

---

## 📦 requirements.txt

```
Flask==3.0.3
Flask-MySQLdb==1.0.1
Werkzeug==3.0.3
reportlab==4.2.2
mysqlclient==2.2.4
```

---

## ⚙️ Step-by-Step Setup

### Step 1 – Install Python & MySQL
- Python 3.10+ from python.org
- XAMPP or MySQL Server

### Step 2 – Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### Step 3 – Setup Database
```bash
# Open phpMyAdmin or MySQL CLI
mysql -u root -p
```
Then paste the entire `database.sql` file and run it.

### Step 4 – Configure app.py
Edit these lines in `app.py`:
```python
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # your MySQL password
app.config['MYSQL_DB'] = 'auralearn'
```

### Step 5 – Create Admin User
In MySQL run:
```sql
USE auralearn;
INSERT INTO User (full_name, email, password, role_id)
VALUES ('Admin', 'admin@auralearn.com',
'$2b$12$...', 1);
```
Or use Python to generate hash:
```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('admin123'))
```
Then paste that hash in the SQL above.

### Step 6 – Run the App
```bash
python app.py
```
Open: **http://localhost:5000**

---

## 🔑 Default Login

| Role  | Email                  | Password  |
|-------|------------------------|-----------|
| Admin | admin@auralearn.com    | admin123  |

---

## 🌐 Key Routes

| Route                    | Description              |
|--------------------------|--------------------------|
| `/`                      | Landing page             |
| `/register`              | Register                 |
| `/login`                 | Login                    |
| `/dashboard`             | Student dashboard        |
| `/course/<id>`           | Course detail            |
| `/quiz/<test_id>`        | Take quiz                |
| `/certificate/download/<id>` | Download PDF cert   |
| `/admin`                 | Admin dashboard          |
| `/admin/courses`         | Manage courses           |
| `/admin/users`           | Manage users             |
| `/admin/questions`       | Manage quiz questions    |
| `/admin/zoom`            | Manage Zoom classes      |
| `/admin/api/stats`       | JSON analytics API       |

---

## ✅ Features Implemented

- [x] All 14 database entities with FK constraints
- [x] Student registration & login (bcrypt)
- [x] Role-based access (admin/student)
- [x] Course enrollment system
- [x] Module viewer (video + PDF)
- [x] MCQ quiz with timer & auto-grading
- [x] Attempt tracking per question
- [x] PDF certificate generation (ReportLab)
- [x] Admin CRUD: Courses, Modules, Users, Questions, Zoom
- [x] Order/payment tracking
- [x] Feedback & ratings system
- [x] Analytics API for Chart.js
- [x] File uploads (videos, PDFs, thumbnails)

---

## 💡 Tips for Final Project

1. **Add `.env` file** for secret keys before submission
2. **Use Bootstrap 5** in all templates for responsiveness
3. **Add Chart.js** in admin dashboard using `/admin/api/stats`
4. **Test with 3 roles**: admin, student, and instructor
5. **Record a demo video** showing all features working

Good luck! 🔥
