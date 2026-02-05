"""
IntelliSearch Chat Frontend - Flask Application
A comprehensive chat interface with desktop/mobile views and admin management.
"""

import os
import uuid
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    Response,
    flash,
    g,
)
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "intellisearch-secret-key-2024")

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
DATABASE = os.path.join(os.path.dirname(__file__), "intellisearch.db")


# ============================================================================
# Database Setup
# ============================================================================


def get_db():
    """Get database connection."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema."""
    with app.app_context():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                avatar_color TEXT DEFAULT '#6366f1',
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                total_tokens INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                tool_calls TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            );
            
            CREATE INDEX IF NOT EXISTS idx_chat_logs_user ON chat_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id);
            CREATE INDEX IF NOT EXISTS idx_token_usage_date ON token_usage(date);
        """
        )

        # Create default admin user if not exists
        cursor = db.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            db.execute(
                """
                INSERT INTO users (username, email, password_hash, display_name, is_admin, avatar_color)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    "admin",
                    "admin@intellisearch.local",
                    generate_password_hash("admin123"),
                    "Administrator",
                    1,
                    "#dc2626",
                ),
            )
            db.commit()
        db.commit()


# ============================================================================
# Authentication Helpers
# ============================================================================


def login_required(f):
    """Decorator to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin access."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("admin_login"))
        db = get_db()
        user = db.execute(
            "SELECT is_admin FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        if not user or not user["is_admin"]:
            flash("Admin access required", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """Get current logged in user."""
    if "user_id" not in session:
        return None
    db = get_db()
    return db.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()


# ============================================================================
# Chat Logging Helpers
# ============================================================================


def log_chat_message(user_id, session_id, role, content, tokens=0, tool_calls=None):
    """Log a chat message to database."""
    with app.app_context():
        db = get_db()
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        db.execute(
            """
            INSERT INTO chat_logs (user_id, session_id, role, content, tokens_used, tool_calls)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, session_id, role, content, tokens, tool_calls_json),
        )

        # Update user stats
        db.execute(
            """
            UPDATE users SET total_messages = total_messages + 1,
                            total_tokens = total_tokens + ?,
                            last_active = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (tokens, user_id),
        )

        db.commit()


def update_token_usage(user_id, tokens):
    """Update daily token usage."""
    with app.app_context():
        db = get_db()
        today = datetime.now().strftime("%Y-%m-%d")
        db.execute(
            """
            INSERT INTO token_usage (user_id, date, total_tokens)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
            total_tokens = total_tokens + ?
        """,
            (user_id, today, tokens, tokens),
        )
        db.commit()


# ============================================================================
# Public Routes
# ============================================================================


@app.route("/")
def index():
    """Landing page - redirect based on device."""
    user_agent = request.headers.get("User-Agent", "").lower()
    is_mobile = any(
        device in user_agent for device in ["mobile", "android", "iphone", "ipad"]
    )

    if "user_id" in session:
        if is_mobile:
            return redirect(url_for("mobile_chat"))
        return redirect(url_for("desktop_chat"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["display_name"] = user["display_name"] or user["username"]
            session["is_admin"] = bool(user["is_admin"])
            session["chat_session_id"] = str(uuid.uuid4())

            # Update last active
            db.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],),
            )
            db.commit()

            flash("Welcome back!", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip() or username

        if len(username) < 3:
            flash("Username must be at least 3 characters", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")

        # Generate random avatar color
        colors = [
            "#6366f1",
            "#8b5cf6",
            "#ec4899",
            "#f43f5e",
            "#f97316",
            "#eab308",
            "#22c55e",
            "#14b8a6",
            "#06b6d4",
            "#3b82f6",
        ]
        avatar_color = colors[hash(username) % len(colors)]

        db = get_db()
        try:
            db.execute(
                """
                INSERT INTO users (username, email, password_hash, display_name, avatar_color)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    username,
                    email or None,
                    generate_password_hash(password),
                    display_name,
                    avatar_color,
                ),
            )
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists", "error")

    return render_template("register.html")


@app.route("/logout")
def logout():
    """Logout user."""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


# ============================================================================
# Desktop Chat Routes
# ============================================================================


@app.route("/chat")
@login_required
def desktop_chat():
    """Desktop chat interface."""
    user = get_current_user()
    if not session.get("chat_session_id"):
        session["chat_session_id"] = str(uuid.uuid4())
    return render_template("desktop_chat.html", user=user)


@app.route("/chat/new")
@login_required
def new_chat():
    """Start a new chat session."""
    session["chat_session_id"] = str(uuid.uuid4())
    return redirect(url_for("desktop_chat"))


# ============================================================================
# Mobile Chat Routes
# ============================================================================


@app.route("/mobile")
@login_required
def mobile_chat():
    """Mobile chat interface."""
    user = get_current_user()
    if not session.get("chat_session_id"):
        session["chat_session_id"] = str(uuid.uuid4())
    return render_template("mobile_chat.html", user=user)


@app.route("/mobile/new")
@login_required
def mobile_new_chat():
    """Start a new mobile chat session."""
    session["chat_session_id"] = str(uuid.uuid4())
    return redirect(url_for("mobile_chat"))


# ============================================================================
# API Proxy Routes (for streaming)
# ============================================================================


@app.route("/api/chat/stream", methods=["POST"])
@login_required
def proxy_chat_stream():
    """Proxy streaming chat request to backend."""
    user_id = session["user_id"]
    session_id = session.get("chat_session_id", str(uuid.uuid4()))

    data = request.get_json()
    message = data.get("message", "")
    use_tools = data.get("use_tools", True)

    # Log user message
    log_chat_message(user_id, session_id, "user", message)

    def generate():
        """Generate SSE response from backend."""
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/chat/stream",
                json={
                    "message": message,
                    "session_id": session_id,
                    "use_tools": use_tools,
                },
                stream=True,
                timeout=120,
            )

            assistant_content = ""
            estimated_tokens = 0

            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    yield decoded + "\n\n"

                    # Parse content for logging
                    if decoded.startswith("data: ") and decoded != "data: [DONE]":
                        try:
                            event_data = json.loads(decoded[6:])
                            if event_data.get("type") == "content":
                                assistant_content += event_data.get("content", "")
                                estimated_tokens += 1  # Rough estimate
                        except json.JSONDecodeError:
                            pass

            # Log assistant response
            if assistant_content:
                log_chat_message(
                    user_id,
                    session_id,
                    "assistant",
                    assistant_content,
                    estimated_tokens,
                )
                update_token_usage(user_id, estimated_tokens)

        except requests.RequestException as e:
            error_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
            yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/tools")
@login_required
def get_tools():
    """Get available tools from backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/chat/tools", timeout=10)
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/user/history")
@login_required
def get_user_history():
    """Get current user's chat history."""
    db = get_db()
    logs = db.execute(
        """
        SELECT * FROM chat_logs 
        WHERE user_id = ? AND session_id = ?
        ORDER BY created_at ASC
    """,
        (session["user_id"], session.get("chat_session_id", "")),
    ).fetchall()

    return jsonify([dict(log) for log in logs])


# ============================================================================
# Admin Routes
# ============================================================================


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND is_admin = 1 AND is_active = 1",
            (username,),
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["display_name"] = user["display_name"] or user["username"]
            session["is_admin"] = True
            flash("Welcome, Admin!", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials", "error")

    return render_template("admin/login.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    db = get_db()

    # Get statistics
    stats = {
        "total_users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "active_users": db.execute(
            "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')"
        ).fetchone()[0],
        "total_messages": db.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0],
        "total_tokens": db.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM users"
        ).fetchone()[0],
    }

    # Get recent activity
    recent_logs = db.execute(
        """
        SELECT cl.*, u.username, u.display_name, u.avatar_color
        FROM chat_logs cl
        JOIN users u ON cl.user_id = u.id
        ORDER BY cl.created_at DESC
        LIMIT 20
    """
    ).fetchall()

    # Get daily token usage (last 7 days)
    token_stats = db.execute(
        """
        SELECT date, SUM(total_tokens) as tokens
        FROM token_usage
        WHERE date >= date('now', '-7 days')
        GROUP BY date
        ORDER BY date
    """
    ).fetchall()

    # Get top users by tokens
    top_users = db.execute(
        """
        SELECT username, display_name, avatar_color, total_tokens, total_messages
        FROM users
        ORDER BY total_tokens DESC
        LIMIT 10
    """
    ).fetchall()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_logs=recent_logs,
        token_stats=token_stats,
        top_users=top_users,
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    """User management page."""
    db = get_db()
    users = db.execute(
        """
        SELECT *, 
               (SELECT COUNT(*) FROM chat_logs WHERE user_id = users.id) as message_count
        FROM users
        ORDER BY created_at DESC
    """
    ).fetchall()

    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    """Toggle user active status."""
    db = get_db()
    db.execute("UPDATE users SET is_active = NOT is_active WHERE id = ?", (user_id,))
    db.commit()
    flash("User status updated", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Delete a user."""
    db = get_db()
    # Prevent deleting yourself
    if user_id == session["user_id"]:
        flash("Cannot delete yourself", "error")
        return redirect(url_for("admin_users"))

    db.execute("DELETE FROM chat_logs WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM token_usage WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User deleted successfully", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def promote_user(user_id):
    """Promote user to admin."""
    db = get_db()
    db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    db.commit()
    flash("User promoted to admin", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/chats")
@admin_required
def admin_chats():
    """View all chat logs."""
    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]

    logs = db.execute(
        """
        SELECT cl.*, u.username, u.display_name, u.avatar_color
        FROM chat_logs cl
        JOIN users u ON cl.user_id = u.id
        ORDER BY cl.created_at DESC
        LIMIT ? OFFSET ?
    """,
        (per_page, offset),
    ).fetchall()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "admin/chats.html", logs=logs, page=page, total_pages=total_pages
    )


@app.route("/admin/tokens")
@admin_required
def admin_tokens():
    """Token usage analytics."""
    db = get_db()

    # Daily usage for last 30 days
    daily_usage = db.execute(
        """
        SELECT date, SUM(total_tokens) as tokens
        FROM token_usage
        WHERE date >= date('now', '-30 days')
        GROUP BY date
        ORDER BY date
    """
    ).fetchall()

    # User token rankings
    user_tokens = db.execute(
        """
        SELECT u.username, u.display_name, u.avatar_color,
               u.total_tokens, u.total_messages,
               COALESCE(tu.today_tokens, 0) as today_tokens
        FROM users u
        LEFT JOIN (
            SELECT user_id, SUM(total_tokens) as today_tokens
            FROM token_usage
            WHERE date = date('now')
            GROUP BY user_id
        ) tu ON u.id = tu.user_id
        ORDER BY u.total_tokens DESC
    """
    ).fetchall()

    return render_template(
        "admin/tokens.html", daily_usage=daily_usage, user_tokens=user_tokens
    )


# ============================================================================
# Error Handlers
# ============================================================================


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error="Page not found", code=404), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="Server error", code=500), 500


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=50001, debug=True)
