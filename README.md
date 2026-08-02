# 📬 OCIMAIL

OCIMAIL is a CLI-based Mail Automation System inspired by enterprise office automation platforms and internal organizational correspondence systems.

Built with Python, PostgreSQL, Docker, and psycopg, OCIMAIL provides a secure role-based environment for managing communications between Employees, Managers, and CEOs — with an Admin role to manage user accounts.

The project focuses on software architecture, database design, role-based access control, and building scalable terminal applications.

---

## ✨ Features

- 🔐 Session-Based Authentication with bcrypt-hashed passwords
- 👤 Role-Based Access Control (RBAC)
- 🛡️ Admin Role & User Management (create, list, deactivate users)
- 📧 Create Mail
- 📥 Interactive Inbox
- 📤 Sent Mails
- ↩️ Reply to Mails and Forwards
- 🔁 Forward Mails (including multi-hop forwarding)
- 🗑️ Soft Delete Support (for mails, forwards, and users)
- 📚 Mail Threading (`reply_to`)
- 📌 Mail & Forward Status Lifecycle
    - UNSEEN
    - SEEN
    - REPLIED
- 📄 Organizational Hierarchy Enforcement
- ⚡ Pagination (10 items per page)
- 🧪 Unit Testing with pytest
- 🐳 PostgreSQL inside Docker
- 🖥️ Interactive CLI Experience

---

## 🏢 Organization Hierarchy

OCIMAIL follows a strict organizational structure for mail communication.

```text
          CEO
           ↑↓
        MANAGER
       ↗       ↖
EMPLOYEE     EMPLOYEE
```

Managers act as intermediaries between Employees and the CEO.

> **Note**
>
> The `ADMIN` role sits outside this hierarchy. Admins don't send, receive,
> or forward mail — they exist solely to create, list, and deactivate user
> accounts. See [Admin Role](#-admin-role) below.

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
- Admins sending/forwarding mail (they have no `can_mail` permissions)

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
11. Deleted mails, forwards, and users remain in the database for consistency (soft delete only).
12. Inbox and Sent Mails are paginated.
13. A user can hold exactly one role — `role` is a single column, and account creation validates the given role against the recognized set (`EMPLOYEE`, `MANAGER`, `CEO`, `ADMIN`).
14. An admin cannot create a user with an email that already exists.
15. Deactivated (soft-deleted) users cannot log in.
16. Passwords are never stored in plaintext — only bcrypt hashes are persisted.

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|----------|
| Python 3 | Core Programming Language |
| PostgreSQL | Database |
| Docker | Containerization |
| psycopg | PostgreSQL Driver |
| bcrypt | Password Hashing |
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

```bash
pip install -r requirements.txt
```

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

Run the following command in your terminal, replacing the placeholder with your own password:

```bash
export DB_PASSWORD="your_secure_password_here"
```

Verify that it has been configured correctly:

```bash
echo $DB_PASSWORD
```

> **⚠️ Security Note**
>
> Never commit a real database password into this README, `.env` files, or
> any tracked file in a public repository. Use a placeholder in documentation
> and keep real credentials in an untracked `.env` file or your shell
> environment only.

---

### Optional Database Environment Variables

OCIMAIL also supports additional database environment variables:

```bash
export DB_HOST="localhost"

export DB_PORT=5431

export DB_NAME="Mail Automation System"

export DB_USER="postgres"

export DB_PASSWORD="your_secure_password_here"
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
-e POSTGRES_PASSWORD=your_secure_password_here \
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
Apply Database Schema & Migrations
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

export DB_PASSWORD="your_secure_password_here"

docker run --name postgres \
-e POSTGRES_PASSWORD=your_secure_password_here \
-p 5431:5432 \
-d postgres

python main.py
```

---

## 🗄 Database Schema

### users

```text
user_id           uuid, primary key
name              varchar
email             varchar, unique
password_hash     varchar (bcrypt hash)
role              user_role (enum)
is_active         boolean, default TRUE
created_at        timestamp
```

### Roles

- EMPLOYEE
- MANAGER
- CEO
- ADMIN *(system role — manages users, not part of the mail hierarchy)*

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
mail_id
status
created_date
reacted_date
sender_deleted
receiver_deleted
```

`mail_id` always points to the **original** mail — even when a forward is
itself forwarded onward (see [Forwarding Chain](#-forwarding-chain) below).
Each hop in a forward chain gets its own row here.

### Forward Status

- UNSEEN
- SEEN
- REPLIED

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

The same lifecycle applies to **forwards**: each forward starts `UNSEEN`,
becomes `SEEN` when the recipient opens it, and `REPLIED` if they respond.
Opening/replying to a forward never changes the original mail's own status
or timestamps — each row tracks its own state independently.

---

## 🔁 Forwarding Chain

`FROM` always shows the **original creator** of the mail, no matter how many
times it's been forwarded. A `FORWARDED BY` line shows who forwarded it to
*you specifically* — the most recent hop.

Example chain:

```text
Reza (EMPLOYEE) creates a mail and sends it to Majid (MANAGER)
Majid forwards it to Mohsen (MANAGER)
Mohsen forwards it to Sara (MANAGER)
```

When Sara opens her inbox:

```text
FROM:
reza@company.com

FORWARDED BY:
mohsen@company.com
```

Each forward is its own independent row in the `forwards` table
(`mail_id` always referencing Reza's original mail), which is what makes
multi-hop forwarding work without any extra chain-tracking logic — the
immediate `sender_id` on the last row *is* the last forwarder.

---

## 🗑 Soft Delete

OCIMAIL uses soft deletion everywhere — for mails, forwards, and users.

Instead of:

```sql
DELETE FROM mails;
DELETE FROM forwards;
DELETE FROM users;
```

the application uses:

```sql
sender_deleted = TRUE      -- mails / forwards
receiver_deleted = TRUE    -- mails / forwards
is_active = FALSE          -- users
```

This guarantees:

- Mail history remains intact.
- Replies remain valid.
- Forward history remains valid.
- Mail threads remain consistent.
- Deactivated users' past mail history stays intact for everyone else.

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
│   ├── admin/
│   │   ├── create.py
│   │   ├── read.py
│   │   └── delete.py
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
│   │   ├── user_menu.py
│   │   └── admin_menu.py
│   │
│   └── permissions/
│       └── roles.py
│
└── test/
    ├── admin/
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

### Admin Menu

```text
========== ADMIN MENU ==========

1. Create User
2. List Users
3. Delete User
0. Logout
```

---

## 📥 Inbox

Inbox displays mails in pages of 10.

Example:

```text
========== INBOX ==========

1. Weekly Meeting
   Type   : MAIL
   From   : sara@company.com
   Status : UNSEEN
   Date   : 25 Jul 2026 | 08:30

2. Budget Report
   Type   : FORWARD
   From   : reza@company.com
   FORWARDED BY : sara@test.com
   Status : REPLIED
   Date   : 24 Jul 2026 | 14:15

P. Previous
N. Next
0. Back
```

---

## 📬 Open Mail

Opening a regular mail:

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

Opening a **forwarded** mail additionally includes a `FORWARD NOTE BY`
line, identifying whoever forwarded it to you and their role:

```text
FROM:
reza@company.com

TO:
sara@company.com

SUBJECT:
Weekly Meeting

BODY:
Please attend tomorrow's meeting.

FORWARD NOTE BY mohsen@company.com / MANAGER:
Take a look at this when you get a chance.

STATUS:
SEEN

DATE:
25 Jul 2026 | 08:30
```

---

### Available Actions

#### Mail — Employee

```text
1. Reply
2. Delete
0. Back
```

#### Mail — Manager / CEO

```text
1. Reply
2. Forward
3. Delete
0. Back
```

#### Forward — Employee

```text
1. Reply
2. Delete
0. Back
```

#### Forward — Manager / CEO

```text
1. Reply
2. Forward
3. Delete
0. Back
```

Replying to a forward addresses whoever forwarded it to you (the most
recent hop) — not the original creator of the mail. Forwarding a forward
creates a new row in `forwards` for that hop, enabling multi-hop chains.

---

## 🔐 Authentication

OCIMAIL uses a lightweight Session-Based Authentication mechanism.

On login, the entered password is verified against the bcrypt hash stored
in `password_hash` using `bcrypt.checkpw()` — plaintext passwords are never
compared or stored directly. Deactivated accounts (`is_active = FALSE`) are
rejected at login regardless of a correct password.

After a successful login, the authenticated user is stored inside a session
object:

```python
session = {
    "user": user
}
```

The session is used throughout the application's lifecycle to determine:

- Current User
- Current Role
- Permissions

Based on the account's role, `main.py` routes into the appropriate menu:
`admin_menu` for `ADMIN`, `user_menu` for everyone else.

This approach keeps the CLI application lightweight while maintaining a
clean separation between authentication and authorization.

---

## 🛡 Admin Role

Admins manage user accounts and don't participate in mail communication.

### Capabilities

- **Create User** — creates a new account with a name, email, password, and
  role. Refuses to create a user if the email already exists, and validates
  the role against the recognized set (`EMPLOYEE`, `MANAGER`, `CEO`, `ADMIN`).
- **List Users** — paginated view of all accounts, showing name, email,
  role, and active/deactivated status.
- **Delete User** — soft-deletes (deactivates) an account via `is_active`,
  preserving all of that user's mail history for everyone else involved.

### Rules

- A user can never have more than one role (enforced structurally — `role`
  is a single column, validated on creation).
- Emails must be unique across all users.
- Deactivating a user does not delete or alter any mail/forward rows they
  were involved in.

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
- Secure Password Hashing & Authentication (bcrypt)
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
- REST API

---

## 📄 License

This project is intended for educational, learning, and personal use.

OCIMAIL was developed to simulate a real-world enterprise mail automation system while emphasizing clean architecture, maintainability, and scalability.

Feel free to fork, modify, and expand the project according to your needs.