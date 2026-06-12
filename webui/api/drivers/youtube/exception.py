from tunesynctool.exceptions import ServiceDriverException

class PrivateResourceException(ServiceDriverException):
    """
    Thrown when an endpoint reports that the requested data requires further privileges (e.g. authentication).
    """

    def __init__(self, message="You do not have access to the requested content."):
        super().__init__(message)