class LinkTrackerApiError(Exception):
    """base exception class"""

    def __init__(self, message: str = "Service is unavailable", name: str = "LinkTrackerApi"):
        self.message = message
        self.name = name
        super().__init__(self.message, self.name)


class NotRegistratedChat(LinkTrackerApiError):
    """Chat is not registrated"""

    pass


class ServiceError(LinkTrackerApiError):
    """failures in external services or APIs, like a database or a third-party service"""

    pass


class EntityAlreadyExistsError(LinkTrackerApiError):
    """conflict detected, like trying to create a resource that already exists"""

    pass


class LinkNotFoundError(LinkTrackerApiError):
    """link not found in the database"""

    pass
