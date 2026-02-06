from .models import AuditLog
from typing import Optional
from config.middleware import get_request_context
import traceback
import threading
import logging

logger = logging.getLogger(__name__)


def _create_audit_log_in_thread(
    app_name: str,
    event_type: str,
    message: str,
    level: str,
    detail: Optional[str],
    triggered_by: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
) -> None:
    """
    Internal function to create audit log in a separate thread
    Runs in background thread. Exceptions are caught and logged
    """
    try:
        from django.db import connection

        AuditLog.objects.create(
            app_name=app_name,
            event_type=event_type,
            level=level,
            message=message,
            detail=detail,
            triggered_by=triggered_by,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Close connection to avoid leaks
        connection.close()

    except Exception as e:
        logger.error(
            f"Failed to create audit log: {e}",
            exc_info=True,
            extra={"app_name": app_name, "event_type": event_type, "message": message},
        )


class AuditService:
    """
    Asynchronous audit logging service
    All logging is fire-and-forget in background threads
    """

    @staticmethod
    def log(
        app_name: str,
        event_type: str,
        message: str,
        level: str = AuditLog.Level.INFO,
        detail: Optional[str] = None,
        triggered_by: str = "system",
    ) -> None:
        """
        Creates an audit log entry in a background thread

        Args:
            app_name: Django app generating log
            event_type: Type of event
            message: Short, readable message
            level: Severity level (defaults to INFO)
            detail: Additional details
            triggered_by: What triggered the event (ex. 'cron', 'api', 'manual')
        """
        context = get_request_context()

        thread = threading.Thread(
            target=_create_audit_log_in_thread,
            args=(
                app_name,
                event_type,
                message,
                level,
                detail,
                triggered_by,
                context["ip_address"],
                context["user_agent"],
            ),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def log_error(
        app_name: str,
        event_type: str,
        message: str,
        exception: Optional[BaseException] = None,
        triggered_by: str = "system",
        detail: Optional[str] = None,
    ) -> None:
        """
        Create an error audit log with exception details

        Args:
            app_name: Django app generating log
            event_type: Type of event
            message: Short, readable message
            exception: Exception raised
            triggered_by: What triggered the event
            detail: Additional context
        """
        error_detail = detail or ""

        if exception:
            error_detail += (
                f"\n\nException: {type(exception).__name__}: {str(exception)}\n"
            )
            error_detail += f"Traceback:\n{traceback.format_exc()}"

        AuditService.log(
            app_name=app_name,
            event_type=event_type,
            message=message,
            level=AuditLog.Level.ERROR,
            detail=error_detail,
            triggered_by=triggered_by,
        )
