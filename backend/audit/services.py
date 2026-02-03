from .models import AuditLog
from typing import Literal
from .middleware import get_request_context
import traceback

AuditLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class AuditService:
    @staticmethod
    def log(
        app_name: str,
        event_type: str,
        message: str,
        level: str = AuditLog.Level.INFO,
        detail: str | None = None,
        triggered_by: str = "system",
    ) -> AuditLog:
        """
        Creates an audit log entry

        Args:
            app_name: Django app generating log
            event_type: Type of event
            message: Short, readable message
            level: Severity level (defaults to info)
            detail: Details
            triggered_by: What triggered the event (ex. 'cron', 'api', 'manual')
        """

        context = get_request_context()

        return AuditLog.objects.create(
            app_name=app_name,
            event_type=event_type,
            level=level,
            message=message,
            detail=detail,
            triggered_by=triggered_by,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
        )

    @staticmethod
    def log_error(
        app_name: str,
        event_type: str,
        message: str,
        exception: BaseException | None = None,
        triggered_by: str = "system",
        detail: str | None = None,
    ) -> AuditLog:
        """
        Create an audit log entry with exception details

        Args:
            app_name: Django app generating log
            event_type: Type of event
            message: Short, readable message
            exception: exception raised
            kwargs: Optional fields (triggered_by)
        """

        error_detail = detail or ""

        if exception:
            error_detail += (
                f"\n\nException: {type(exception).__name__}: {str(exception)}\n"
            )
            error_detail += f"Traceback:\n{traceback.format_exc()}"

        # call itself
        return AuditService.log(
            app_name=app_name,
            event_type=event_type,
            message=message,
            level=AuditLog.Level.ERROR,
            detail=error_detail,
            triggered_by=triggered_by,
        )
