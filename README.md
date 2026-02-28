# User Management System

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/django%20rest%20framework-%23A30000.svg?style=for-the-badge&logo=django&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Vercel](https://img.shields.io/badge/deployed%20on-vercel-black?style=for-the-badge&logo=vercel)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

A full-stack authentication and account management platform built with Django REST Framework and React.
It combines secure JWT-based access, role-aware flows, profile controls, and account activity tracking.

## Live Demo

- **Main Demo:** https://user-management-site.vercel.app/
- **API:** https://user-management-api-theta.vercel.app/api/
- **Repository:** https://github.com/GugaValenca/user_management_system

## Overview

User Management System is a job-ready portfolio project designed to simulate practical account lifecycle management:

- A React + TypeScript frontend with protected routes and role-aware navigation
- A Django REST API with JWT authentication and access control rules
- Production deployment on Vercel for frontend and backend
- Docker-based local setup for backend and PostgreSQL

The public demo is focused on the main user workflow. Administrative tools are reserved for internal management and development use.

## Features

- JWT authentication (register, login, logout with token blacklist)
- Custom user model with email-based authentication
- Role-based access control (`user`, `moderator`, `admin`)
- Profile editing and secure password change flow
- Activity logging for key account security events
- Admin-only endpoints for user listing and high-level stats
- Frontend route guards for authenticated and admin-only screens
- Production-ready API integration with Axios and typed request/response models

## Screenshots

### Login
![User Management System - Login](https://via.placeholder.com/1400x800/F5F7FA/1F2937?text=Login+Screenshot)

### Dashboard
![User Management System - Dashboard](https://via.placeholder.com/1400x800/F5F7FA/1F2937?text=Dashboard+Screenshot)

### Profile
![User Management System - Profile](https://via.placeholder.com/1400x800/F5F7FA/1F2937?text=Profile+Screenshot)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/GugaValenca/user_management_system.git
cd user_management_system
```

2. Backend setup:

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Frontend setup:

```bash
cd ../frontend
npm install
```

## Usage

### Public Demo Flow

1. Open the main demo URL
2. Register a new account
3. Access Dashboard, Profile, and Activity Logs
4. Validate protected routes by signing out and revisiting private pages

### Demo Access

If demo access is required and no public credentials are documented, use placeholders:

- Email: `[DEMO_EMAIL]`
- Password: `[DEMO_PASSWORD]`

### Local Development

Option A: Docker backend + PostgreSQL

```bash
docker compose up --build
```

Option B: run backend and frontend separately

Backend:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm start
```

## Project Structure

```bash
user_management_system/
|-- backend/
|   |-- accounts/
|   |   |-- admin.py
|   |   |-- models.py
|   |   |-- serializers.py
|   |   |-- views.py
|   |   `-- urls.py
|   |-- api/
|   |   `-- index.py
|   |-- user_management/
|   |   |-- settings.py
|   |   `-- urls.py
|   |-- requirements.txt
|   |-- vercel.json
|   `-- Dockerfile
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |-- pages/
|   |   |-- services/api.ts
|   |   |-- types/
|   |   `-- utils/
|   |-- package.json
|   `-- vercel.json
|-- docker-compose.yml
|-- README.md
`-- LICENSE
```

## Key Technical Highlights / What I Learned

- Implementing end-to-end JWT auth with token blacklisting on logout
- Designing role-aware backend permissions and matching frontend route protection
- Building a reusable typed API client layer in React + TypeScript
- Tracking account-level activity data to support security and observability
- Structuring deployment as separate frontend/backend Vercel projects with rewrite rules

## Technologies Used

- **Frontend:** React 19, TypeScript, React Router, Axios, React Bootstrap
- **Backend:** Python 3.12, Django 4.2, Django REST Framework, SimpleJWT, django-cors-headers, WhiteNoise
- **Database:** PostgreSQL (production/Docker), SQLite (local fallback)
- **Testing:** React Testing Library setup, Django test framework setup
- **Deployment:** Vercel
- **Containerization:** Docker, Docker Compose
- **Package Managers:** npm (frontend), pip (backend)

## Future Improvements

- Add automated backend tests for auth and role-based endpoints
- Implement silent refresh flow on the frontend
- Add search and pagination controls for admin user management
- Improve observability with structured logging and error tracking
- Add CI checks for linting and automated tests

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m "Add some AmazingFeature"`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Contact

**Gustavo Valenca**

[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com/GugaValenca)
[![LinkedIn](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/gugavalenca/)
[![Instagram](https://img.shields.io/badge/Instagram-%23E4405F.svg?style=for-the-badge&logo=Instagram&logoColor=white)](https://www.instagram.com/gugatampa)
[![Twitch](https://img.shields.io/badge/Twitch-%239146FF.svg?style=for-the-badge&logo=Twitch&logoColor=white)](https://www.twitch.tv/gugatampa)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/3QQyR5whBZ)

---

If you found this project helpful, please give it a star.
