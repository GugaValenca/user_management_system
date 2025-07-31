# User Management System

A comprehensive user authentication and profile management system built with Django REST Framework and React TypeScript.

## 🚀 Features

- **Complete Authentication System**: JWT-based login, registration, and logout
- **User Profile Management**: Editable profiles with personal information
- **Role-Based Access Control**: Admin, Moderator, and User roles
- **Activity Logging**: Detailed user activity tracking with IP addresses
- **Admin Dashboard**: System statistics and user management panel
- **Responsive Design**: Modern UI with Bootstrap and React Bootstrap
- **Secure Password Management**: Password change functionality with validation
- **Real-time Data**: Live updates and seamless user experience

## 🛠️ Tech Stack

### Backend

- **Django 5.2.4** - Python web framework
- **Django REST Framework** - API development
- **JWT Authentication** - Secure token-based authentication
- **MySQL 8.0** - Database management
- **Python 3.8+** - Programming language

### Frontend

- **React 18** - User interface library
- **TypeScript** - Type-safe JavaScript
- **React Bootstrap** - UI components
- **Axios** - HTTP client
- **React Router** - Navigation
- **React Icons 4.12.0** - Icon library

## 📋 Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 16+** - [Download Node.js](https://nodejs.org/)
- **MySQL 8.0+** - [Download MySQL](https://dev.mysql.com/downloads/)
- **Git** - [Download Git](https://git-scm.com/)

## 🔧 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/GugaValenca/user_management_system.git
cd user_management_system
```

### 2. Backend Setup (Django)

#### Create Virtual Environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### MySQL Setup

**Option 1: MySQL Workbench**

1. Open MySQL Workbench
2. Connect to localhost:3306
3. Execute: `CREATE DATABASE user_management_db;`

**Option 2: Command Line**

```bash
mysql -u root -p
CREATE DATABASE user_management_db;
SHOW DATABASES;
exit;
```

#### Configure Database

1. Open `backend/user_management/settings.py`
2. Update the DATABASES section:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'user_management_db',
        'USER': 'root',                    # Your MySQL username
        'PASSWORD': 'your_mysql_password', # Your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

#### Install MySQL Client

```bash
pip install mysqlclient
```

#### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Create Superuser

```bash
python manage.py createsuperuser
```

_Follow prompts to create admin account_

### 3. Frontend Setup (React)

```bash
cd ../frontend
npm install
```

#### Fix React Icons Compatibility

```bash
npm uninstall react-icons
npm install react-icons@4.12.0
```

## 🚀 Running the Application

### Start Backend Server

```bash
cd backend
# Activate virtual environment first
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

python manage.py runserver
```

**Backend will run on:** http://127.0.0.1:8000/

### Start Frontend Server (New Terminal)

```bash
cd frontend
npm start
```

**Frontend will run on:** http://localhost:3000/

## 🧪 Testing the Application

### Demo Accounts

- **Admin Account**: Use the superuser you created
- **Test User**: Register a new account via the signup page

### Available Pages

- **Login/Register**: http://localhost:3000/login
- **Dashboard**: http://localhost:3000/dashboard
- **Profile Settings**: http://localhost:3000/profile
- **Activity Logs**: http://localhost:3000/activity
- **Admin Panel**: http://localhost:3000/admin (Admin only)

### Test Scenarios

1. **User Registration**: Create a new account
2. **User Login**: Login with created credentials
3. **Profile Update**: Edit user information
4. **Password Change**: Update password securely
5. **Activity Tracking**: View login/logout logs
6. **Admin Functions**: Manage users (if admin)

## 🔐 API Endpoints

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/profile/` - Get user profile
- `PATCH /api/auth/profile/` - Update user profile
- `POST /api/auth/change-password/` - Change password

### Admin Endpoints

- `GET /api/auth/users/` - List all users (Admin only)
- `GET /api/auth/stats/` - System statistics (Admin only)
- `GET /api/auth/activity-logs/` - User activity logs

## 🏗️ Project Structure

```
user_management_system/
├── backend/
│   ├── user_management/          # Django project settings
│   │   ├── settings.py          # Database and app configuration
│   │   └── urls.py              # Main URL routing
│   ├── accounts/                # User authentication app
│   │   ├── models.py            # User and ActivityLog models
│   │   ├── serializers.py       # API serializers
│   │   ├── views.py             # API views and logic
│   │   ├── urls.py              # App URL routing
│   │   └── admin.py             # Django admin configuration
│   ├── requirements.txt         # Python dependencies
│   └── manage.py               # Django management script
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable React components
│   │   │   ├── Navbar.tsx       # Navigation component
│   │   │   └── ProtectedRoute.tsx # Route protection
│   │   ├── pages/               # Application pages
│   │   │   ├── Login.tsx        # Login page
│   │   │   ├── Register.tsx     # Registration page
│   │   │   ├── Dashboard.tsx    # Main dashboard
│   │   │   ├── Profile.tsx      # Profile management
│   │   │   ├── ActivityLogs.tsx # Activity tracking
│   │   │   └── AdminPanel.tsx   # Admin interface
│   │   ├── services/            # API integration
│   │   │   └── api.ts           # HTTP client setup
│   │   ├── utils/               # Utility functions
│   │   │   └── AuthContext.tsx  # Authentication context
│   │   ├── types/               # TypeScript definitions
│   │   │   └── index.ts         # Type definitions
│   │   └── App.tsx              # Main application component
│   ├── package.json             # Node.js dependencies
│   └── public/                  # Static assets
└── README.md                    # Project documentation
```

## 🛠️ Troubleshooting

### Common Issues

#### MySQL Connection Error

**Problem**: `django.db.utils.OperationalError`
**Solution**:

1. Verify MySQL is running: `mysql --version`
2. Check credentials in `settings.py`
3. Ensure database exists: `SHOW DATABASES;`

#### React Icons Error

**Problem**: TypeScript errors with icons
**Solution**:

```bash
npm uninstall react-icons
npm install react-icons@4.12.0
```

#### Virtual Environment Issues

**Problem**: `pip` commands not working
**Solution**:

```bash
# Ensure virtual environment is activated
cd backend
venv\Scripts\activate  # Windows
```

#### Port Already in Use

**Problem**: Port 3000 or 8000 already in use
**Solution**:

```bash
# Kill processes using the port
npx kill-port 3000
npx kill-port 8000
```

### Development Tips

- Always activate virtual environment before running Django commands
- Keep both servers running in separate terminals
- Check browser console for JavaScript errors
- Use Django admin at http://127.0.0.1:8000/admin/ for backend management

## 🔒 Security Features

- **JWT Token Authentication**: Stateless and secure
- **Password Validation**: Django's built-in validators
- **Activity Logging**: Track user actions with IP addresses
- **Role-based Access**: Different permission levels
- **CORS Configuration**: Secure cross-origin requests
- **Input Validation**: Comprehensive form validation

## 🌟 Key Features for Portfolio

### Technical Skills Demonstrated

- **Full-Stack Development**: Complete frontend and backend integration
- **RESTful API Design**: Professional API architecture
- **Database Design**: Efficient relational data modeling
- **Authentication & Authorization**: Secure user management
- **Modern Frontend**: React with TypeScript and responsive design
- **Professional Standards**: Clean code, documentation, and Git practices

### Business Logic Implementation

- User registration and authentication flows
- Profile management with data validation
- Administrative functions and user oversight
- Security logging and audit trails
- Responsive design for multiple devices

## 🚀 Deployment Ready

This application is production-ready with:

- Environment-based configuration
- Database migrations
- Static file handling
- Security middleware
- Error handling
- Logging configuration

## 📈 Future Enhancements

- [ ] Email verification system
- [ ] Password reset via email
- [ ] File upload for profile pictures
- [ ] Real-time notifications
- [ ] Advanced user search and filtering
- [ ] Two-factor authentication
- [ ] API rate limiting
- [ ] Comprehensive testing suite
- [ ] Docker containerization
- [ ] CI/CD pipeline integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Gustavo Valenca**
- GitHub: [@GugaTampa](https://github.com/gugatampa)
- LinkedIn: [@GugaValenca](https://linkedin.com/in/gugavalenca)
- Email: gustavo_valenca@hotmail.com

## 🙏 Acknowledgments

- Django REST Framework documentation
- React and TypeScript communities
- Bootstrap team for UI components
- MySQL team for database management

---

## 💻 Quick Start Commands

```bash
# Backend
cd backend
venv\Scripts\activate
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm start

# Access application
# Frontend: http://localhost:3000
# Backend API: http://127.0.0.1:8000
# Admin Panel: http://127.0.0.1:8000/admin
```

⭐ **Star this repository if you found it helpful!**
