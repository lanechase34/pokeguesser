import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

from django.test import TestCase, TransactionTestCase

from audit.models import AuditLog
from audit.services import AuditService


def wait_for_logs(expected_count: int, timeout: float = 2.0) -> bool:
    """
    Wait for logs to be created in background threads.

    Args:
        expected_count: Number of logs expected
        timeout: Maximum time to wait in seconds

    Returns:
        bool: True if expected count reached, False if timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        if AuditLog.objects.count() >= expected_count:
            return True
        time.sleep(0.05)
    return False


class AuditServiceBasicTest(TestCase):
    """Test basic async logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        AuditLog.objects.all().delete()

    def tearDown(self):
        """Clean up after tests."""
        AuditLog.objects.all().delete()

    @patch("audit.services.get_request_context")
    def test_log_creates_entry_async(self, mock_context: MagicMock):
        """Test that logging creates entry in background thread."""
        mock_context.return_value = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0",
        }

        # Call log (returns None immediately)
        result = AuditService.log(
            app_name="guesser",
            event_type="POKEMON_VIEWED",
            message="User viewed Pikachu",
        )

        # Should return None (fire-and-forget)
        self.assertIsNone(result)

        # Wait for background thread
        self.assertTrue(wait_for_logs(1))

        # Verify log was created
        log = AuditLog.objects.get(event_type="POKEMON_VIEWED")
        self.assertEqual(log.app_name, "guesser")
        self.assertEqual(log.message, "User viewed Pikachu")
        self.assertEqual(log.level, AuditLog.Level.INFO)
        self.assertEqual(log.ip_address, "192.168.1.100")
        self.assertEqual(log.user_agent, "Mozilla/5.0")

    @patch("audit.services.get_request_context")
    def test_log_with_all_parameters(self, mock_context: MagicMock):
        """Test logging with all parameters."""
        mock_context.return_value = {
            "ip_address": "10.0.0.1",
            "user_agent": "Chrome/99.0",
        }

        AuditService.log(
            app_name="guesser",
            event_type="GUESS_SUBMITTED",
            message="User guessed Pikachu",
            level=AuditLog.Level.WARNING,
            detail="Attempt 2/3, Time: 45s",
            triggered_by="api",
        )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="GUESS_SUBMITTED")
        self.assertEqual(log.level, AuditLog.Level.WARNING)
        self.assertEqual(log.detail, "Attempt 2/3, Time: 45s")
        self.assertEqual(log.triggered_by, "api")

    @patch("audit.services.get_request_context")
    def test_log_with_different_levels(self, mock_context: MagicMock):
        """Test logging at different severity levels."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        levels = [
            AuditLog.Level.DEBUG,
            AuditLog.Level.INFO,
            AuditLog.Level.WARNING,
            AuditLog.Level.ERROR,
            AuditLog.Level.CRITICAL,
        ]

        for level in levels:
            AuditService.log(
                app_name="test",
                event_type=f"LEVEL_{level}",
                message=f"Testing {level}",
                level=level,
            )

        self.assertTrue(wait_for_logs(5))

        for level in levels:
            log = AuditLog.objects.get(event_type=f"LEVEL_{level}")
            self.assertEqual(log.level, level)

    @patch("audit.services.get_request_context")
    def test_log_with_null_context(self, mock_context: MagicMock):
        """Test logging when context has null values."""
        mock_context.return_value = {"ip_address": None, "user_agent": None}

        AuditService.log(
            app_name="background",
            event_type="TASK_COMPLETED",
            message="Background task finished",
        )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="TASK_COMPLETED")
        self.assertIsNone(log.ip_address)
        self.assertIsNone(log.user_agent)

    @patch("audit.services.get_request_context")
    def test_multiple_logs_all_created(self, mock_context: MagicMock):
        """Test that multiple logs are all created."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        # Create 20 logs
        for i in range(20):
            AuditService.log(
                app_name="multi", event_type=f"EVENT_{i}", message=f"Message {i}"
            )

        # Wait for all threads
        self.assertTrue(wait_for_logs(20))

        # Verify all created
        self.assertEqual(AuditLog.objects.filter(app_name="multi").count(), 20)


class AuditServiceErrorLoggingTest(TestCase):
    """Test error logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        AuditLog.objects.all().delete()

    def tearDown(self):
        """Clean up after tests."""
        AuditLog.objects.all().delete()

    @patch("audit.services.get_request_context")
    def test_log_error_with_exception(self, mock_context: MagicMock):
        """Test logging an error with exception details."""
        mock_context.return_value = {
            "ip_address": "192.168.1.1",
            "user_agent": "Error Test",
        }

        try:
            _result = 1 / 0
        except ZeroDivisionError as e:
            AuditService.log_error(
                app_name="guesser",
                event_type="CALCULATION_ERROR",
                message="Division by zero occurred",
                exception=e,
            )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="CALCULATION_ERROR")
        self.assertEqual(log.level, AuditLog.Level.ERROR)
        self.assertIn("ZeroDivisionError", log.detail)
        self.assertIn("division by zero", log.detail)
        self.assertIn("Traceback:", log.detail)

    @patch("audit.services.get_request_context")
    def test_log_error_without_exception(self, mock_context: MagicMock):
        """Test logging an error without exception."""
        mock_context.return_value = {"ip_address": "10.0.0.1", "user_agent": "Test"}

        AuditService.log_error(
            app_name="guesser",
            event_type="VALIDATION_FAILED",
            message="Pokemon not found",
        )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="VALIDATION_FAILED")
        self.assertEqual(log.level, AuditLog.Level.ERROR)
        self.assertEqual(log.message, "Pokemon not found")

    @patch("audit.services.get_request_context")
    def test_log_error_with_custom_detail(self, mock_context: MagicMock):
        """Test logging error with custom detail and exception."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        custom_detail = "User tried to guess 'InvalidPokemon'"

        try:
            raise ValueError("Invalid Pokemon name")
        except ValueError as e:
            AuditService.log_error(
                app_name="guesser",
                event_type="INVALID_GUESS",
                message="Invalid guess submitted",
                exception=e,
                detail=custom_detail,
            )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="INVALID_GUESS")
        self.assertIn(custom_detail, log.detail)
        self.assertIn("ValueError", log.detail)
        self.assertIn("Invalid Pokemon name", log.detail)

    @patch("audit.services.get_request_context")
    def test_log_error_preserves_traceback(self, mock_context: MagicMock):
        """Test that full traceback is preserved."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        def inner_function():
            raise KeyError("Missing key")

        def outer_function():
            inner_function()

        try:
            outer_function()
        except KeyError as e:
            AuditService.log_error(
                app_name="test",
                event_type="KEY_ERROR",
                message="Key not found",
                exception=e,
            )

        self.assertTrue(wait_for_logs(1))

        log = AuditLog.objects.get(event_type="KEY_ERROR")
        self.assertIn("inner_function", log.detail)
        self.assertIn("outer_function", log.detail)
        self.assertIn("KeyError", log.detail)


class AuditServicePerformanceTest(TestCase):
    """Test performance characteristics."""

    def setUp(self):
        """Set up test fixtures."""
        AuditLog.objects.all().delete()

    def tearDown(self):
        """Clean up after tests."""
        AuditLog.objects.all().delete()

    @patch("audit.services.get_request_context")
    def test_logging_is_non_blocking(self, mock_context: MagicMock):
        """Test that logging doesn't block."""
        mock_context.return_value = {
            "ip_address": "127.0.0.1",
            "user_agent": "Performance Test",
        }

        # Time 100 log calls
        start = time.time()
        for i in range(100):
            AuditService.log(
                app_name="perf", event_type=f"EVENT_{i}", message=f"Message {i}"
            )
        duration = time.time() - start

        # Should complete almost instantly (< 2 seconds)
        self.assertLess(duration, 2)

        # Wait for all threads to complete
        self.assertTrue(wait_for_logs(100))

        # Verify all created
        self.assertEqual(AuditLog.objects.filter(app_name="perf").count(), 100)

    @patch("audit.services.get_request_context")
    def test_bulk_logging(self, mock_context: MagicMock):
        """Test creating many logs rapidly."""
        mock_context.return_value = {
            "ip_address": "127.0.0.1",
            "user_agent": "Bulk Test",
        }

        # Create 500 logs
        for i in range(500):
            AuditService.log(
                app_name="bulk", event_type="BULK_EVENT", message=f"Bulk message {i}"
            )

        # Wait for all
        self.assertTrue(wait_for_logs(500, timeout=5.0))

        # Verify count
        self.assertEqual(AuditLog.objects.filter(app_name="bulk").count(), 500)


class AuditServiceConcurrencyTest(TransactionTestCase):
    """Test concurrent logging."""

    def setUp(self):
        """Set up test fixtures."""
        AuditLog.objects.all().delete()

    def tearDown(self):
        """Clean up after tests."""
        AuditLog.objects.all().delete()

    @patch("audit.services.get_request_context")
    def test_concurrent_logging_from_multiple_threads(self, mock_context: MagicMock):
        """Test that concurrent logging works correctly."""
        mock_context.return_value = {
            "ip_address": "127.0.0.1",
            "user_agent": "Concurrent Test",
        }

        def create_log(index: int):
            AuditService.log(
                app_name="concurrent",
                event_type=f"CONCURRENT_{index}",
                message=f"Concurrent message {index}",
            )

        # Create 50 logs from 10 different threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_log, i) for i in range(50)]
            for future in futures:
                future.result()

        # Wait for all background threads
        self.assertTrue(wait_for_logs(50))

        # Verify all created
        self.assertEqual(AuditLog.objects.filter(app_name="concurrent").count(), 50)


class AuditServiceQueryTest(TestCase):
    """Test querying audit logs."""

    def setUp(self):
        """Set up test fixtures."""
        AuditLog.objects.all().delete()

    def tearDown(self):
        """Clean up after tests."""
        AuditLog.objects.all().delete()

    @patch("audit.services.get_request_context")
    def test_query_by_app_name(self, mock_context: MagicMock):
        """Test filtering logs by app_name."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        AuditService.log("guesser", "EVENT1", "Message 1")
        AuditService.log("guesser", "EVENT2", "Message 2")
        AuditService.log("scheduler", "EVENT3", "Message 3")

        self.assertTrue(wait_for_logs(3))

        guesser_logs = AuditLog.objects.filter(app_name="guesser")
        scheduler_logs = AuditLog.objects.filter(app_name="scheduler")

        self.assertEqual(guesser_logs.count(), 2)
        self.assertEqual(scheduler_logs.count(), 1)

    @patch("audit.services.get_request_context")
    def test_query_by_level(self, mock_context: MagicMock):
        """Test filtering logs by severity level."""
        mock_context.return_value = {"ip_address": "127.0.0.1", "user_agent": "Test"}

        AuditService.log("app", "E1", "Msg", level=AuditLog.Level.INFO)
        AuditService.log("app", "E2", "Msg", level=AuditLog.Level.WARNING)
        AuditService.log_error("app", "E3", "Msg")

        self.assertTrue(wait_for_logs(3))

        info_logs = AuditLog.objects.filter(level=AuditLog.Level.INFO)
        error_logs = AuditLog.objects.filter(level=AuditLog.Level.ERROR)

        self.assertEqual(info_logs.count(), 1)
        self.assertEqual(error_logs.count(), 1)
