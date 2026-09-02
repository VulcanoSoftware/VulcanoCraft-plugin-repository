# VulcanoCraft Plugin Repository - Update Log

## Version 2.0 - Major Updates

### 🔐 Authentication System
- **User Registration & Login**: Complete authentication system with username/email login
- **Session Management**: Persistent login sessions with proper logout functionality
- **Password Security**: Argon2 password hashing (OWASP-recommended) with automatic migration of legacy SHA-256 hashes

### 👑 Admin Panel
- **Standalone Admin System**: Separate admin panel with independent login (`/admin`)
- **User Management**: Grid-based user display with plugin counts per user
- **Registration Toggle**: Admin can enable/disable new user registrations
- **Admin Credentials**: Username: `admin`, Password: `admin123`

### 🎨 UI/UX Improvements
- **Logout Button Centering**: Fixed positioning issues in header
- **Registration Disabled Message**: Eye-catching card notification when registration is off
- **Grid Layout**: Users displayed in responsive card grid instead of table
- **Plugin Count Display**: Shows number of plugins added by each user

### 📁 Project Structure Reorganization
```
components/
├── admin/
│   └── admin.html     # Admin panel interface
└── user/
    └── login.html     # User login/registration page
```

### 🔧 Technical Improvements
- **User-Specific Plugins**: Each user only sees and manages their own plugins
- **Session Persistence**: Admin panel maintains login state on refresh
- **Error Handling**: Fixed encoding issues in error messages
- **Path Updates**: All file paths updated for new component structure

### 🚫 Removed Features
- **Email Verification**: Removed SMTP email verification system for simplicity
- **Admin Access on Main Site**: Admin functionality isolated to separate panel

### 🛠️ Bug Fixes
- Fixed 500 error when adding plugins due to encoding issues
- Resolved logout button positioning problems
- Fixed admin session persistence on page refresh

### 📋 Current Features (samenvatting)
1. **User System**: Registration, login, logout with secure sessions
2. **Plugin Management**: Add, view, delete plugins per user
3. **Admin Panel**: User management, registration control, plugin statistics
4. **Responsive Design**: Mobile-friendly interface with animations
5. **Search & Filter**: Plugin filtering by version, platform, and search terms

### 🔮 Future Considerations
- Email verification system (if needed)
- User profile management
- Plugin categories and tags
- Advanced admin analytics
