from enum import StrEnum

class Initiator(StrEnum):
    """
    Sets who or what initiated something (e.g. a task creation).
    """

    SYSTEM = "system"
    USER = "user"