"""
Monitoring and Health Check Module for ORBCOMM Service Tracker
Provides health checks, metrics, and monitoring endpoints
"""

import os
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import jsonify, Response

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class HealthCheck:
    """Health check utilities for the application"""

    @staticmethod
    def check_database(db_path: str) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notifications")
            count = cursor.fetchone()[0]
            conn.close()

            return {
                "status": "healthy",
                "message": f"Database accessible ({count} notifications)",
                "response_time_ms": 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}",
                "response_time_ms": 0
            }

    @staticmethod
    def check_disk_space(data_dir: str, threshold_percent: int = 90) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            usage = psutil.disk_usage(data_dir)
            is_healthy = usage.percent < threshold_percent

            return {
                "status": "healthy" if is_healthy else "warning",
                "message": f"Disk usage: {usage.percent}% ({usage.free / (1024**3):.2f} GB free)",
                "percent_used": usage.percent,
                "free_gb": usage.free / (1024**3)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Disk check error: {str(e)}",
                "percent_used": 0,
                "free_gb": 0
            }

    @staticmethod
    def check_memory(threshold_percent: int = 90) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            is_healthy = memory.percent < threshold_percent

            return {
                "status": "healthy" if is_healthy else "warning",
                "message": f"Memory usage: {memory.percent}% ({memory.available / (1024**3):.2f} GB available)",
                "percent_used": memory.percent,
                "available_gb": memory.available / (1024**3)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Memory check error: {str(e)}",
                "percent_used": 0,
                "available_gb": 0
            }

    @staticmethod
    def check_credentials(data_dir: str) -> Dict[str, Any]:
        """Check if Gmail credentials are present"""
        try:
            creds_path = Path(data_dir) / "credentials.json"
            token_path = Path(data_dir) / "token.json"

            has_creds = creds_path.exists()
            has_token = token_path.exists()

            if has_creds and has_token:
                status = "healthy"
                message = "Gmail credentials configured"
            elif has_creds:
                status = "warning"
                message = "Credentials present, but no token (needs authentication)"
            else:
                status = "warning"
                message = "No Gmail credentials configured"

            return {
                "status": status,
                "message": message,
                "credentials_exist": has_creds,
                "token_exists": has_token
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Credentials check error: {str(e)}",
                "credentials_exist": False,
                "token_exists": False
            }


class Metrics:
    """Prometheus metrics for monitoring"""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            return

        # Request metrics
        self.request_count = Counter(
            'orbcomm_requests_total',
            'Total request count',
            ['method', 'endpoint', 'status']
        )

        self.request_duration = Histogram(
            'orbcomm_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )

        # Email sync metrics
        self.emails_fetched = Counter(
            'orbcomm_emails_fetched_total',
            'Total emails fetched',
            ['inbox']
        )

        self.emails_parsed = Counter(
            'orbcomm_emails_parsed_total',
            'Total emails parsed',
            ['inbox', 'status']
        )

        # Database metrics
        self.db_query_duration = Histogram(
            'orbcomm_db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation']
        )

        self.notification_count = Gauge(
            'orbcomm_notifications_total',
            'Total number of notifications',
            ['status']
        )

        # System metrics
        self.memory_usage = Gauge(
            'orbcomm_memory_usage_bytes',
            'Memory usage in bytes'
        )

        self.disk_usage = Gauge(
            'orbcomm_disk_usage_percent',
            'Disk usage percentage'
        )

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_email_sync(self, inbox: str, fetched: int, parsed: int, success: bool):
        """Record email sync metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.emails_fetched.labels(inbox=inbox).inc(fetched)
        self.emails_parsed.labels(
            inbox=inbox,
            status='success' if success else 'failure'
        ).inc(parsed)

    def update_system_metrics(self):
        """Update system resource metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)

        disk = psutil.disk_usage('/')
        self.disk_usage.set(disk.percent)


# Global metrics instance
metrics = Metrics()


def register_health_routes(app, db_path: str, data_dir: str):
    """Register health check and monitoring routes to Flask app"""

    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ORBCOMM Service Tracker",
            "version": "1.1.0"
        }), 200

    @app.route('/health/detailed')
    def health_check_detailed():
        """Detailed health check with component status"""
        checks = {
            "database": HealthCheck.check_database(db_path),
            "disk": HealthCheck.check_disk_space(data_dir),
            "memory": HealthCheck.check_memory(),
            "credentials": HealthCheck.check_credentials(data_dir)
        }

        # Overall health is unhealthy if any component is unhealthy
        overall_healthy = all(
            check["status"] != "unhealthy" for check in checks.values()
        )

        return jsonify({
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "uptime_seconds": time.process_time()
        }), 200 if overall_healthy else 503

    @app.route('/health/ready')
    def readiness_check():
        """Kubernetes readiness probe"""
        try:
            # Check if database is accessible
            db_check = HealthCheck.check_database(db_path)
            is_ready = db_check["status"] == "healthy"

            return jsonify({
                "ready": is_ready,
                "timestamp": datetime.utcnow().isoformat()
            }), 200 if is_ready else 503
        except Exception as e:
            return jsonify({
                "ready": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), 503

    @app.route('/health/live')
    def liveness_check():
        """Kubernetes liveness probe"""
        return jsonify({
            "alive": True,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    @app.route('/metrics')
    def prometheus_metrics():
        """Prometheus metrics endpoint"""
        if not PROMETHEUS_AVAILABLE:
            return jsonify({
                "error": "Prometheus client not available",
                "message": "Install prometheus-client package"
            }), 501

        # Update system metrics before generating output
        metrics.update_system_metrics()

        return Response(
            generate_latest(),
            mimetype=CONTENT_TYPE_LATEST
        )

    @app.route('/info')
    def app_info():
        """Application information endpoint"""
        return jsonify({
            "name": "ORBCOMM Service Tracker",
            "version": "1.1.0",
            "description": "Email notification monitoring and analytics",
            "environment": os.environ.get("FLASK_ENV", "production"),
            "python_version": os.sys.version,
            "timestamp": datetime.utcnow().isoformat()
        }), 200


def setup_request_logging(app):
    """Setup request logging middleware"""

    @app.before_request
    def before_request():
        """Record request start time"""
        from flask import g
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Log request metrics"""
        from flask import g, request

        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            metrics.record_request(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code,
                duration=duration
            )

        return response

    return app
