# IntelliSearch Flask Frontend

A comprehensive chat frontend for IntelliSearch with desktop/mobile interfaces and admin management.

## Features

### Chat Interfaces
- **Desktop Chat** (`/chat`) - Full-featured chat with sidebar navigation
- **Mobile Chat** (`/mobile`) - Touch-optimized mobile interface
- Streaming responses with real-time content display
- Markdown rendering with syntax highlighting
- LaTeX/KaTeX math equation support
- Tool usage indicators and process display

### Admin Dashboard
- **Dashboard** (`/admin`) - Overview with stats and charts
- **User Management** (`/admin/users`) - Create, edit, disable users
- **Chat Logs** (`/admin/chats`) - View all conversation history
- **Token Usage** (`/admin/tokens`) - Monitor token consumption

### User Management
- User registration and authentication
- Admin and regular user roles
- Session-based chat history
- Per-user token tracking

## Quick Start

### 1. Install Dependencies

```bash
cd frontend/flask
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Optional: Set custom backend URL
export BACKEND_URL=http://localhost:8001

# Optional: Set Flask secret key
export FLASK_SECRET_KEY=your-secret-key
```

### 3. Run the Server

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## Default Admin Credentials

- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Important:** Change the default admin password in production!

## Project Structure

```
frontend/flask/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── intellisearch.db       # SQLite database (created on first run)
├── templates/
│   ├── base.html          # Base template with CDN resources
│   ├── login.html         # User login page
│   ├── register.html      # User registration page
│   ├── desktop_chat.html  # Desktop chat interface
│   ├── mobile_chat.html   # Mobile chat interface
│   ├── error.html         # Error page template
│   └── admin/
│       ├── login.html     # Admin login page
│       ├── dashboard.html # Admin dashboard
│       ├── users.html     # User management
│       ├── chats.html     # Chat logs viewer
│       └── tokens.html    # Token usage analytics
└── static/
    └── css/
        ├── main.css       # Core styles and variables
        ├── desktop.css    # Desktop-specific styles
        ├── mobile.css     # Mobile-specific styles
        └── admin.css      # Admin panel styles
```

## API Endpoints

### Chat API (Proxied to Backend)
- `POST /api/chat/stream` - Streaming chat endpoint
- `GET /api/tools` - List available tools
- `GET /api/user/history` - Get current user's chat history

### Auth Routes
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - Logout

### Admin Routes (Admin Only)
- `GET /admin` - Dashboard
- `GET /admin/users` - User list
- `POST /admin/users/<id>/toggle` - Toggle user active status
- `POST /admin/users/<id>/delete` - Delete user
- `POST /admin/users/<id>/promote` - Promote to admin
- `GET /admin/chats` - Chat logs
- `GET /admin/tokens` - Token analytics

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Optional email
- `password_hash` - Hashed password
- `display_name` - Display name
- `avatar_color` - Avatar background color
- `is_admin` - Admin flag
- `is_active` - Active flag
- `total_tokens` - Cumulative token usage
- `total_messages` - Message count
- `created_at` - Creation timestamp
- `last_active` - Last activity timestamp

### Chat Logs Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `session_id` - Chat session ID
- `role` - Message role (user/assistant)
- `content` - Message content
- `tokens_used` - Estimated tokens
- `tool_calls` - JSON tool call data
- `created_at` - Timestamp

### Token Usage Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `date` - Usage date
- `total_tokens` - Daily token count

## Customization

### Changing Theme Colors

Edit CSS variables in `static/css/main.css`:

```css
:root {
    --accent-primary: #6366f1;
    --accent-secondary: #8b5cf6;
    --accent-gradient: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
}
```

### Adding New Pages

1. Create template in `templates/`
2. Add route in `app.py`
3. Link in sidebar navigation

## Production Deployment

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set strong `FLASK_SECRET_KEY`
3. Change default admin password
4. Consider PostgreSQL instead of SQLite
5. Enable HTTPS
6. Configure proper CORS headers

```bash
# Example with Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

MIT License - Part of the IntelliSearch project.

