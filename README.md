# User Management System

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-20232a?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9-3178c6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql&logoColor=white)](https://neon.tech/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Full-stack authentication and profile management system with JWT, role-based access, activity logs, admin panel, and production deployment on Vercel + Neon PostgreSQL.

---

## Live Demo

- Site (public): `https://user-management-site.vercel.app`
- Backend API: `https://user-management-api-theta.vercel.app/api`
- Django Admin: `https://user-management-api-theta.vercel.app/admin/`

### Production Architecture (Vercel)

- `user-management-site` (frontend React)
- `user-management-api` (backend Django)
- Public access uses one main URL (`user-management-site.vercel.app`)
- Frontend proxies `/api/*` requests to the backend via `frontend/vercel.json`

---

## Features

- JWT authentication (register, login, logout)
- User profile management (profile info + password change)
- Role-based access control (`user`, `moderator`, `admin`)
- Activity logging (login, logout, profile updates, password changes)
- Admin dashboard with user stats and user list
- Protected frontend routes
- Production-ready environment configuration

---

## Tech Stack

### Backend

- Python 3.12
- Django 4.2
- Django REST Framework
- SimpleJWT
- PostgreSQL (Neon)
- `python-decouple`

### Frontend

- React + TypeScript
- React Router
- Axios
- React Bootstrap + Bootstrap
- React Icons

### Deployment

- Vercel (frontend + backend/serverless)
- Neon PostgreSQL

---

## Project Structure

```bash
user_management_system/
|-- backend/
|   |-- accounts/                # Models, serializers, views, urls
|   |-- api/index.py             # Vercel Python entrypoint (WSGI)
|   |-- user_management/         # Django settings / URLs
|   |-- manage.py
|   |-- requirements.txt
|   `-- vercel.json
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- components/
|   |   |-- pages/
|   |   |-- services/api.ts
|   |   |-- types/
|   |   `-- utils/AuthContext.tsx
|   |-- package.json
|   `-- vercel.json
`-- README.md
```

---

## Main API Endpoints

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/profile/`
- `PATCH /api/auth/profile/`
- `POST /api/auth/change-password/`
- `GET /api/auth/activity-logs/`
- `GET /api/auth/stats/` (admin)
- `GET /api/auth/users/` (admin)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/GugaValenca/user_management_system.git
cd user_management_system
```

### 2. Backend setup (Django)

```bash
cd backend
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env` (example):

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True

# Option A (recommended): full connection string (Neon/Postgres)
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require

# Local frontend
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Run migrations and start server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`

### 3. Frontend setup (React)

```bash
cd ../frontend
npm install
```

Create `frontend/.env`:

```env
REACT_APP_API_BASE_URL=http://localhost:8000/api
```

Start frontend:

```bash
npm start
```

Frontend runs at `http://localhost:3000`

---

## Production Deployment (Vercel + Neon)

### Backend (Vercel project: `user-management-api`)

Required environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DATABASE_URL` (Neon PostgreSQL)
- `DJANGO_ALLOWED_HOSTS=.vercel.app,localhost,127.0.0.1`
- `CORS_ALLOWED_ORIGINS=https://user-management-site.vercel.app,http://localhost:3000`
- `CSRF_TRUSTED_ORIGINS=https://user-management-site.vercel.app,http://localhost:3000`

Deploy:

```bash
cd backend
npx vercel --prod
```

### Frontend (Vercel project: `user-management-site`)

The project is configured to use a single public URL. In production, `/api/*` is proxied to the backend through `frontend/vercel.json`.

Deploy:

```bash
cd frontend
npx vercel --prod
```

---

## Notes

- The backend supports `DATABASE_URL` (PostgreSQL/Neon) and fallback local configuration.
- JWT logout uses token blacklist (`rest_framework_simplejwt.token_blacklist`).
- In production, the frontend can call `/api/*` (single public URL) because Vercel rewrites proxy requests to the backend project.

---

## Author

**Gustavo Valenca**

- GitHub: [@GugaValenca](https://github.com/GugaValenca)
- LinkedIn: [@GugaValenca](https://linkedin.com/in/gugavalenca)
- Email: `gustavo_valenca@hotmail.com`

---

## License

This project is licensed under the MIT License.
