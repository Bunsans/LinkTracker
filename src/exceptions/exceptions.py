class LinkTrackerApiError(Exception):
    """base exception class."""

    def __init__(
        self,
        message: str = "Service is unavailable",
        name: str = "LinkTrackerApi",
    ) -> None:
        self.message = message
        self.name = name
        super().__init__(self.message, self.name)


class NotRegistratedChatError(LinkTrackerApiError):
    """Chat is not registrated."""


class ServiceError(LinkTrackerApiError):
    """failures in external services or APIs, like a database or a third-party service."""


class EntityAlreadyExistsError(LinkTrackerApiError):
    """conflict detected, like trying to create a resource that already exists."""


class LinkNotFoundError(LinkTrackerApiError):
    """link not found in the database."""
