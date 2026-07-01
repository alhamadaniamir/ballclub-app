# 🏟️ MAB Sports Ballclub App

A professional ball court management system for organizing sessions, managing player queues, and handling member registrations.

## ✨ Features

- **Owner Authentication** - Secure login with bcrypt password hashing
- **Session Management** - Create, manage, and close playing sessions
- **Queue System** - Track players with queue numbers and payment status
- **Pending Requests** - Approve/decline join requests from players
- **Member Directory** - Maintain a list of members with contact information
- **Share Links** - Generate unique share codes for players to join sessions
- **Public Endpoints** - Allow players to check session status and join

## 🏗️ Project Structure

```
ballclub-app/
├── models/              # MongoDB schemas
│   ├── Member.js       # Member model with validation
│   └── Session.js      # Session model with players and pending requests
├── middleware/          # Express middleware
│   ├── auth.js         # JWT authentication
│   └── validation.js   # Input validation and error handling
├── routes/             # API endpoints
│   ├── auth.js         # Login endpoint
│   ├── sessions.js     # Session management endpoints
│   ├── members.js      # Member management endpoints
│   └── public.js       # Public endpoints (no auth required)
├── utils/
│   └── helpers.js      # Utility functions
├── public/             # Frontend assets
│   ├── index.html      # Main HTML structure
│   ├── styles.css      # Stylesheet
│   ├── script.js       # Frontend JavaScript
│   └── join.html       # Join page (optional)
└── server.js           # Express server setup
```

## 🔒 Security Improvements

✅ **Password Hashing** - Switched from plain text to bcrypt hashing
✅ **Input Validation** - All endpoints validate name, phone, and other inputs
✅ **Phone Validation** - Ensures phone numbers are 10-15 digits
✅ **Error Handling** - Global error handler prevents info leakage
✅ **Environment Variables** - All secrets in .env (never committed)
✅ **Separated Concerns** - Models, routes, and middleware cleanly organized

## 🚀 Getting Started

### Prerequisites
- Node.js v16+
- MongoDB cluster (Atlas or local)

### Installation

1. **Clone & Install**
   ```bash
   npm install
   ```

2. **Configure Environment**
   Edit `.env` with your credentials:
   ```env
   MONGO_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster0.g8zutzh.mongodb.net/ballclub?appName=Cluster0
   JWT_SECRET=your_secure_jwt_secret
   OWNER_USERNAME=admin
   OWNER_PASSWORD_HASH=$2b$10$... (bcrypt hash)
   PORT=3000
   ```

   **To generate a new password hash:**
   ```bash
   node -e "const bcrypt = require('bcrypt'); bcrypt.hash('yourpassword', 10, (err, hash) => { console.log(hash); });"
   ```

3. **Start Server**
   ```bash
   npm start
   ```

4. **Access Application**
   - Frontend: http://localhost:3000
   - Admin Login: admin / adminpass

## 📡 API Endpoints

### Authentication (Public)
- `POST /api/auth/login` - Owner login with username/password

### Sessions (Protected)
- `GET /api/sessions` - Get all sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/:id` - Get session details
- `PATCH /api/sessions/:id/close` - Close session
- `DELETE /api/sessions/:id` - Delete session
- `POST /api/sessions/:id/walkin` - Add walk-in player
- `PATCH /api/sessions/:id/players/:playerId` - Toggle payment status
- `DELETE /api/sessions/:id/players/:playerId` - Remove player
- `POST /api/sessions/:id/pending/:requestId/approve` - Approve join request
- `POST /api/sessions/:id/pending/:requestId/decline` - Decline join request

### Members (Protected)
- `GET /api/members` - Get all members
- `POST /api/members` - Create member
- `PATCH /api/members/:id` - Update member
- `DELETE /api/members/:id` - Delete member

### Public (No Auth)
- `GET /api/public/session/:shareCode` - Check session status
- `GET /api/public/lookup?phone=XXXX` - Look up member by phone
- `POST /api/public/session/:shareCode/join` - Join session as player

## 📊 Data Models

### Session
```javascript
{
  date: Date,
  status: 'open' | 'closed',
  shareCode: String (unique),
  queue: [Player],
  pending: [PendingRequest]
}
```

### Player
```javascript
{
  queueNumber: Number,
  name: String,
  phone: String,
  paid: Boolean,
  addedAt: Date
}
```

### Member
```javascript
{
  name: String,
  phone: String (10-15 digits),
  dateJoined: Date
}
```

## 🌐 Deployment Guide

### NOT Recommended: Vercel
❌ Vercel is for serverless/static sites, not persistent Node.js servers
❌ Cold starts would cause poor UX
❌ Requires complex refactoring to serverless functions

### ✅ Recommended Platforms

#### 1. **Railway.app** (Best for beginners)
- One-click MongoDB + Node.js deployment
- $5/month free tier
- [Deploy Guide](https://railway.app)

#### 2. **Render.com**
- Good free tier for 750 hours/month
- Built-in MongoDB integration
- Easy GitHub deployment

#### 3. **Heroku** (Classic)
- Established platform
- Good documentation
- [Deploy Guide](https://devcenter.heroku.com/articles/deploying-nodejs)

#### 4. **DigitalOcean App Platform**
- Fixed pricing ($12+/month)
- Good performance
- Full control

### Steps to Deploy (Example: Railway)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Refactor: reorganized code structure with security improvements"
   git push origin master
   ```

2. **Connect to Railway**
   - Go to Railway.app → New Project → GitHub Repo
   - Add MongoDB plugin
   - Set environment variables from `.env`

3. **Deploy**
   - Railway auto-deploys on push
   - Access via provided URL

## 📝 Environment Setup

The `.env` file should NEVER be committed. It's in `.gitignore`.

Required variables:
```env
MONGO_URI=                # Your MongoDB connection string
JWT_SECRET=               # Any random secure string (e.g., 32 chars)
OWNER_USERNAME=admin      # Choose your admin username
OWNER_PASSWORD_HASH=      # Bcrypt hash of your password
PORT=3000                 # Server port
```

## 🧪 Testing Endpoints

```bash
# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}'

# Create session (use token from login)
curl -X POST http://localhost:3000/api/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Public: Lookup member
curl http://localhost:3000/api/public/lookup?phone=5551234567
```

## 📚 Recent Improvements

### Version 2.0 - Code Reorganization & Security
- ✅ Organized code into models, routes, middleware
- ✅ Implemented bcrypt for password hashing
- ✅ Added comprehensive input validation
- ✅ Separated CSS and JavaScript into own files
- ✅ Added proper error handling middleware
- ✅ Implemented new CRUD endpoints (delete session, delete player, update member)
- ✅ Added phone number validation (10-15 digits)
- ✅ Better code reusability with helper functions

## 🐛 Known Issues / TODO

- [ ] Add rate limiting to prevent abuse
- [ ] Add email notifications for approvals
- [ ] Add session analytics/reports
- [ ] Implement logout functionality
- [ ] Add player removal confirmation dialog
- [ ] Add session history export (CSV)

## 🤝 Contributing

This is a personal project. Feel free to fork and modify.

## 📄 License

MIT
