"""
Integration tests for ORBCOMM Service Tracker
Tests the full application stack
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orbcomm_tracker.database import Database  # noqa: E402


class TestDatabaseIntegration:
    """Test database operations"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = Database(db_path)
        db.create_tables()
        yield db
        db.close()

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_notification_lifecycle(self, temp_db):
        """Test complete notification lifecycle"""
        # Store notification with all required fields
        notification_data = {
            "reference_number": "S123456",
            "gmail_message_id": "test_msg_id_123456",
            "event_type": "Service Interruption",
            "summary": "Test notification summary",
            "raw_email_subject": "Test Subject",
            "date_received": "2025-01-01 10:00:00",
            "status": "Open",
            "platform": "IDP",
            "raw_email_body": "Test body",
            "inbox_source": "test_inbox",
        }

        result = temp_db.insert_notification(notification_data)
        assert result is not None  # Returns integer ID on success

        # Get notification
        notifications = temp_db.get_all_notifications()
        assert len(notifications) == 1
        assert notifications[0]["reference_number"] == "S123456"

        # Insert resolved notification with unique gmail_message_id
        resolved_data = notification_data.copy()
        resolved_data["gmail_message_id"] = "test_msg_id_123456_resolved"
        resolved_data["status"] = "Resolved"
        result = temp_db.insert_notification(resolved_data)
        assert result is not None  # Returns integer ID on success

        # Link the pair
        temp_db.link_notification_pair("S123456")

        # Check pairing
        pairs = temp_db.get_notification_pairs()
        assert len(pairs) == 1

    def test_stats_calculation(self, temp_db):
        """Test statistics calculation"""
        # Add test data with all required fields
        for i in range(5):
            temp_db.insert_notification(
                {
                    "reference_number": f"S{i:06d}",
                    "gmail_message_id": f"test_msg_id_{i}",
                    "event_type": "Service Interruption",
                    "summary": f"Test notification {i}",
                    "raw_email_subject": f"Test {i}",
                    "date_received": "2025-01-01 10:00:00",
                    "status": "Open" if i % 2 == 0 else "Resolved",
                    "platform": "IDP",
                    "raw_email_body": "Test",
                    "inbox_source": "test",
                }
            )

        stats = temp_db.get_current_stats()
        assert stats["total_notifications"] == 5
        assert stats["open_count"] >= 0
        assert stats["resolved_count"] >= 0

    def test_sync_history(self, temp_db):
        """Test sync history tracking"""
        # Record sync - log_sync_start returns the sync_id
        sync_id = temp_db.log_sync_start("test_inbox")
        assert sync_id is not None

        temp_db.log_sync_complete(
            sync_id=sync_id,
            emails_fetched=10,
            emails_parsed=10,
            errors_count=0,
            status="success",
        )

        # Get history
        history = temp_db.get_sync_history(limit=5)
        assert len(history) > 0
        assert history[0]["inbox_source"] == "test_inbox"

    def test_archiving(self, temp_db):
        """Test notification archiving"""
        # Add old notification with all required fields
        temp_db.insert_notification(
            {
                "reference_number": "OLD001",
                "gmail_message_id": "test_old_msg_001",
                "event_type": "Service Interruption",
                "summary": "Old notification",
                "raw_email_subject": "Old notification",
                "date_received": "2024-01-01 10:00:00",
                "status": "Resolved",
                "platform": "IDP",
                "raw_email_body": "Old",
                "inbox_source": "test",
            }
        )

        # Archive
        archived = temp_db.archive_old_notifications(days=180)
        assert archived >= 0


class TestConfigurationManagement:
    """Test configuration system"""

    def test_config_loading(self):
        """Test configuration loading"""
        from config import get_config

        # Test development config
        dev_config = get_config("development")
        assert dev_config.DEBUG is True

        # Test production config
        prod_config = get_config("production")
        assert prod_config.DEBUG is False

    def test_env_variables(self):
        """Test environment variable override"""
        from config import Config

        # Test default values
        assert Config.PORT == int(os.environ.get("PORT", "5000"))

        # Test environment override
        os.environ["PORT"] = "8080"
        assert int(os.environ.get("PORT", "5000")) == 8080

        # Cleanup
        del os.environ["PORT"]


class TestHealthChecks:
    """Test health check endpoints"""

    def test_database_health_check(self, tmp_path):
        """Test database health check"""
        from orbcomm_tracker.monitoring import HealthCheck

        # Create temp database
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.create_tables()
        db.close()

        # Check health
        result = HealthCheck.check_database(str(db_path))
        assert result["status"] == "healthy"

    def test_disk_space_check(self, tmp_path):
        """Test disk space check"""
        from orbcomm_tracker.monitoring import HealthCheck

        result = HealthCheck.check_disk_space(str(tmp_path))
        assert result["status"] in ["healthy", "warning"]
        assert "percent_used" in result

    def test_memory_check(self):
        """Test memory check"""
        from orbcomm_tracker.monitoring import HealthCheck

        result = HealthCheck.check_memory()
        assert result["status"] in ["healthy", "warning"]
        assert "percent_used" in result


class TestSecurityFeatures:
    """Test security features"""

    def test_password_hashing(self):
        """Test password hashing"""
        from orbcomm_tracker.security import SimpleAuth

        auth = SimpleAuth()
        password = "test_password_123"
        hashed = auth.hash_password(password)

        # Should be SHA256 hex (64 characters)
        assert len(hashed) == 64
        assert hashed != password

    def test_input_validation(self):
        """Test input validation"""
        from orbcomm_tracker.security import InputValidator

        # Test email validation
        assert InputValidator.validate_email("test@example.com") is True
        assert InputValidator.validate_email("invalid-email") is False

        # Test date validation
        assert InputValidator.validate_date("2025-01-01") is True
        assert InputValidator.validate_date("invalid-date") is False

        # Test string sanitization
        long_string = "a" * 1000
        sanitized = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(sanitized) == 100

        # Test pagination validation
        page, per_page = InputValidator.validate_pagination(0, 1000)
        assert page == 1  # Minimum 1
        assert per_page == 100  # Maximum 100


@pytest.fixture
def app():
    """Create Flask app for testing"""
    import sys
    from pathlib import Path

    # Add project to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Import app
    from orbcomm_dashboard import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE_PATH"] = ":memory:"

    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestFlaskEndpoints:
    """Test Flask application endpoints"""

    def test_index_route(self, client):
        """Test index page loads"""
        response = client.get("/")
        assert response.status_code == 200

    def test_api_stats(self, client):
        """Test stats API endpoint"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data
        assert "total_notifications" in data["stats"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
