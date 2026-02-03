from django.db import models


class AuditLog(models.Model):
    """
    Generic audit log table
    """

    class Level(models.TextChoices):
        DEBUG = "DEBUG", "Debug"
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"
        CRITICAL = "CRITICAL", "Critical"

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    app_name = models.CharField(max_length=100, db_index=True)  # ex: 'guesser'
    event_type = models.CharField(
        max_length=100, db_index=True
    )  # ex: 'POKEMON_CREATED', 'JOB_RAN'
    level = models.CharField(
        max_length=20, choices=Level.choices, default="INFO", db_index=True
    )
    message = models.TextField()
    detail = models.TextField(null=True, blank=True)
    triggered_by = models.CharField(
        max_length=100, null=True, blank=True
    )  # ex: 'cron', 'api', 'manual'
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["app_name", "event_type"]),
            models.Index(fields=["timestamp", "level"]),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.app_name}.{self.event_type} - {self.level}"
