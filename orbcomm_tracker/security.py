"""
Security enhancements for ORBCOMM Service Tracker
Includes rate limiting, authentication, and security headers
"""

import hashlib
import os
from datetime import datetime
from functools import wraps

from flask import jsonify, request, session

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False

try:
    from flask_talisman import Talisman

    TALISMAN_AVAILABLE = True
except ImportError:
    TALISMAN_AVAILABLE = False


class RateLimiter:
    """Rate limiting for API endpoints"""

    @staticmethod
    def init_app(app):
        """Initialize rate limiter"""
        if not LIMITER_AVAILABLE:
            return None

        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[
                os.environ.get("RATELIMIT_DEFAULT", "100 per hour"),
                "20 per minute",
            ],
            storage_uri=os.environ.get("RATELIMIT_STORAGE_URL", "memory://"),
        )

        return limiter


class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def init_app(app):
        """Initialize security headers"""
        if not TALISMAN_AVAILABLE:
            # Manual security headers if Talisman not available
            @app.after_request
            def set_security_headers(response):
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "SAMEORIGIN"
                response.headers["X-XSS-Protection"] = "1; mode=block"
                response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

                if os.environ.get("FLASK_ENV") != "development":
                    response.headers[
                        "Strict-Transport-Security"
                    ] = "max-age=63072000; includeSubDomains"

                return response

        else:
            # Use Talisman for comprehensive security
            csp = {
                "default-src": ["'self'", "https:"],
                "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                "style-src": ["'self'", "'unsafe-inline'"],
                "img-src": ["'self'", "data:", "https:"],
            }

            force_https = os.environ.get("FLASK_ENV") != "development"

            Talisman(
                app,
                force_https=force_https,
                strict_transport_security=True,
                content_security_policy=csp,
                content_security_policy_nonce_in=["script-src"],
            )


class SimpleAuth:
    """Simple authentication for dashboard access"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize authentication"""
        self.username = os.environ.get("DASHBOARD_USERNAME")
        self.password_hash = os.environ.get("DASHBOARD_PASSWORD_HASH")

        # If no credentials set, disable auth
        if not self.username or not self.password_hash:
            app.config["AUTH_ENABLED"] = False
        else:
            app.config["AUTH_ENABLED"] = True

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, username: str, password: str) -> bool:
        """Verify username and password"""
        if not self.app.config.get("AUTH_ENABLED", False):
            return True

        password_hash = self.hash_password(password)
        return username == self.username and password_hash == self.password_hash

    def login_required(self, f):
        """Decorator to require login for routes"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.app.config.get("AUTH_ENABLED", False):
                return f(*args, **kwargs)

            if not session.get("logged_in"):
                return jsonify({"error": "Authentication required"}), 401

            return f(*args, **kwargs)

        return decorated_function


def register_auth_routes(app, auth):
    """Register authentication routes"""

    @app.route("/login", methods=["POST"])
    def login():
        """Login endpoint"""
        if not app.config.get("AUTH_ENABLED", False):
            return jsonify({"message": "Authentication disabled"}), 200

        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if auth.verify_password(username, password):
            session["logged_in"] = True
            session["username"] = username
            session.permanent = True
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    @app.route("/logout", methods=["POST"])
    def logout():
        """Logout endpoint"""
        session.pop("logged_in", None)
        session.pop("username", None)
        return jsonify({"message": "Logout successful"}), 200

    @app.route("/auth/status")
    def auth_status():
        """Check authentication status"""
        return (
            jsonify(
                {
                    "authenticated": session.get("logged_in", False),
                    "username": session.get("username"),
                    "auth_enabled": app.config.get("AUTH_ENABLED", False),
                }
            ),
            200,
        )


class InputValidator:
    """Input validation utilities"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate ISO date format"""
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def sanitize_string(s: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not s:
            return ""
        return s[:max_length].strip()

    @staticmethod
    def validate_pagination(page: int, per_page: int, max_per_page: int = 100) -> tuple:
        """Validate pagination parameters"""
        page = max(1, page)
        per_page = min(max_per_page, max(1, per_page))
        return page, per_page
