# 📬 OCIMAIL

OCIMAIL is a CLI-based Mail Automation System inspired by enterprise office automation platforms and internal organizational correspondence systems.

Built with Python, PostgreSQL, Docker, and psycopg, OCIMAIL provides a secure role-based environment for managing communications between Employees, Managers, and CEOs.

The project focuses on software architecture, database design, role-based access control, and building scalable terminal applications.

---

## ✨ Features

- 🔐 Session-Based Authentication
- 👤 Role-Based Access Control (RBAC)
- 📧 Create Mail
- 📥 Interactive Inbox
- 📤 Sent Mails
- ↩️ Reply to Mails
- 🔁 Forward Mails
- 🗑️ Soft Delete Support
- 📚 Mail Threading (`reply_to`)
- 📌 Mail Status Lifecycle
    - UNSEEN
    - SEEN
    - REPLIED
- 📄 Organizational Hierarchy Enforcement
- ⚡ Pagination (10 mails per page)
- 🧪 Unit Testing with pytest
- 🐳 PostgreSQL inside Docker
- 🖥️ Interactive CLI Experience

---

## 🏢 Organization Hierarchy

OCIMAIL follows a strict organizational structure.

```text
          CEO
           ↑↓
        MANAGER
       ↗       ↖
EMPLOYEE     EMPLOYEE
```

Managers act as intermediaries between Employees and the CEO.

---

## 📜 Communication Rules

### Allowed

| Sender | Receiver |
|-------|--------|
| EMPLOYEE | MANAGER |
| MANAGER | EMPLOYEE |
| MANAGER | MANAGER |
| MANAGER | CEO |
| CEO | MANAGER |

---

### Forbidden

- EMPLOYEE → EMPLOYEE
- EMPLOYEE → CEO
- CEO → EMPLOYEE
- CEO → CEO
- Sending a mail to yourself
- Forwarding a mail to yourself
- Forwarding a mail back to its original sender
- Sending mails to users that do not exist

---

## ✨ Business Rules

The system enforces the following rules:

1. Receiver Email cannot be empty.
2. Subject cannot be empty.
3. Body cannot be empty.
4. Reply body cannot be empty.
5. Receiver must exist in the database.
6. Users cannot send mails to themselves.
7. Users cannot forward mails to themselves.
8. Users cannot communicate outside their role permissions.
9. Forwarding follows organizational hierarchy.
10. Users cannot forward a mail to the user who originally sent it.
11. Deleted mails remain in the database for consistency.
12. Inbox and Sent Mails are paginated.

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|----------|
| Python 3 | Core Programming Language |
| PostgreSQL | Database |
| Docker | Containerization |
| psycopg | PostgreSQL Driver |
| pytest | Testing Framework |

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Null-bash/Mail-Automation-System.git

cd backend
```

---

### 2. Create a virtual environment

```bash
python -m venv venv
```

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

### 3. Install dependencies

---

## ⚠️ Database Password Configuration

Before running OCIMAIL, you must export your PostgreSQL password as an environment variable.

The application reads the database password from:

```python
os.environ["DB_PASSWORD"]
```

If this variable is missing, the application will fail with:

```text
KeyError: 'DB_PASSWORD'
```

### Linux / macOS

Run the following command in your terminal:

```bash
export DB_PASSWORD="20031382Ss@"
```

Verify that it has been configured correctly:

```bash
echo $DB_PASSWORD
```

---

### Optional Database Environment Variables

OCIMAIL also supports additional database environment variables:

```bash
export DB_HOST="localhost"

export DB_PORT=5431

export DB_NAME="Mail Automation System"

export DB_USER="postgres"

export DB_PASSWORD="20031382Ss@"
```

The application uses the following defaults if these values are not provided:

| Variable | Default |
|---------|---------|
| DB_HOST | localhost |
| DB_PORT | 5431 |
| DB_NAME | Mail Automation System |
| DB_USER | postgres |
| DB_PASSWORD | Required |

> **Note**
>
> `DB_PASSWORD` is the only required environment variable.

---

## 🐳 Running PostgreSQL

Start PostgreSQL using Docker:

```bash
docker run \
--name ocimail-postgres \
-e POSTGRES_PASSWORD=20031382Ss@ \
-p 5431:5432 \
-d postgres
```

Verify that the container is running:

```bash
docker ps
```

---

## ▶️ Recommended Setup Order

```text
Clone Repository
        ↓
Create Virtual Environment
        ↓
Install Dependencies
        ↓
Export DB_PASSWORD
        ↓
Run PostgreSQL Container
        ↓
python main.py
```

Example:

```bash
git clone https://github.com/Null-bash/Mail-Automation-System.git

cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

export DB_PASSWORD="20031382Ss@"

docker run --name postgres \
-e POSTGRES_PASSWORD=20031382Ss@ \
-p 5431:5432 \
-d postgres

python main.py
```

---


## 🗄 Database Schema

### users

```text
user_id
name
email
password_hash
role
created_at
```

### Roles

- EMPLOYEE
- MANAGER
- CEO

---

### mails

```text
mail_id
sender_id
receiver_id
subject
body
created_date
reacted_date
reply_to
status
sender_deleted
receiver_deleted
```

### Mail Status

- UNSEEN
- SEEN
- REPLIED

---

### forwards

```text
forward_id
sender_id
receiver_id
forward_note
created_date
mail_id
sender_deleted
receiver_deleted
```

---

## 📬 Mail Lifecycle

```text
Create Mail
    ↓
UNSEEN
    ↓
Open Mail
    ↓
SEEN
    ↓
Reply
    ↓
REPLIED
```

Example:

```text
09:00 Mail Created
09:12 Mail Opened
09:20 Mail Replied
```

---

## 🗑 Soft Delete

OCIMAIL uses soft deletion.

Instead of:

```sql
DELETE FROM mails;
```

the application uses:

```sql
sender_deleted = TRUE
receiver_deleted = TRUE
```

This guarantees:

- Mail history remains intact.
- Replies remain valid.
- Forward history remains valid.
- Mail threads remain consistent.

This approach is similar to modern mail systems such as Outlook and Gmail.

---

## 📁 Project Structure

```text
backend/

├── main.py
├── requirements.txt
├── pytest.ini
│
├── core/
│   ├── db.py
│   │
│   ├── auth/
│   │   ├── login.py
│   │   └── logout.py
│   │
│   ├── crud/
│   │   ├── create.py
│   │   ├── read.py
│   │   ├── update.py
│   │   └── delete.py
│   │
│   ├── menus/
│   │   └── user_menu.py
│   │
│   └── permissions/
│       └── roles.py
│
└── test/
    ├── auth/
    ├── crud/
    ├── menus/
    ├── permissions/
    ├── test_db.py
    └── test_main.py
```

---

## ▶️ Running the Project

Run the application:

```bash
python main.py
```

---

### Main Menu

```text
=================================
         OCIMAIL
=================================

1. Login
2. Exit
```

---

### User Menu

```text
=================================
Welcome Amir
Role: EMPLOYEE
=================================

1. Create Mail
2. Inbox
3. Sent Mails
4. Logout
```

---

## 📥 Inbox

Inbox displays mails in pages of 10.

Example:

```text
========== INBOX ==========

1. Weekly Meeting
   From   : sara@company.com
   Status : UNSEEN
   Date   : 25 Jul 2026 | 08:30

2. Budget Report
   From   : reza@company.com
   Status : REPLIED
   Date   : 24 Jul 2026 | 14:15

P. Previous
N. Next
0. Back
```

---

## 📬 Open Mail

Selecting a mail opens:

```text
FROM:
sara@company.com

TO:
amir@company.com

SUBJECT:
Weekly Meeting

BODY:
Please attend tomorrow's meeting.

STATUS:
SEEN

DATE:
25 Jul 2026 | 08:30
```

---

### Available Actions

#### Employee

```text
1. Reply
0. Back
```

#### Manager / CEO

```text
1. Reply
2. Forward
0. Back
```

---

## 🔐 Authentication

OCIMAIL uses a lightweight Session-Based Authentication mechanism.

After a successful login, the authenticated user is stored inside a session object:

```python
session = {
    "user": user
}
```

The session is used throughout the application's lifecycle to determine:

- Current User
- Current Role
- Permissions

This approach keeps the CLI application lightweight while maintaining a clean separation between authentication and authorization.

---

## 🧪 Running Tests

Run all tests:

```bash
pytest
```

Run a specific test:

```bash
pytest test/auth/test_login.py
```

Examples:

```bash
pytest test/auth/test_logout.py

pytest test/crud/test_create.py

pytest test/crud/test_read.py

pytest test/crud/test_update.py

pytest test/crud/test_delete.py

pytest test/menus/test_user_menu.py

pytest test/permissions/test_roles.py
```

---

## 🎯 Learning Objectives

OCIMAIL was built to practice and demonstrate:

- Database Design
- PostgreSQL
- Docker
- Session Management
- Role-Based Access Control (RBAC)
- CRUD Operations
- Python Project Architecture
- Terminal Application Design
- Software Testing with pytest
- Software Design Principles

---

## 🚀 Future Improvements

- Flet Frontend
- Search Mails
- Attachments
- Notifications
- Docker Compose
- Mail Categories
- Audit Logs
- Admin Dashboard
- REST API
- Real-Time Messaging

---

## 📄 License

This project is intended for educational, learning, and personal use.

OCIMAIL was developed to simulate a real-world enterprise mail automation system while emphasizing clean architecture, maintainability, and scalability.

Feel free to fork, modify, and expand the project according to your needs.