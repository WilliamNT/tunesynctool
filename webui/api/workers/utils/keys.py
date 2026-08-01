from typing import Tuple
from api.models.task import TaskKind

def make_task_key(kind: str | TaskKind, user_id: int, task_id: str) -> str:
    """
    Generate a Redis key for a task.
    
    Format: user_tasks:{kind}:{user_id}:{task_id}
    
    :param kind: Task type (e.g., TaskKind.USER_INITIATED_PLAYLIST_TRANSFER)
    :param user_id: User's database ID
    :param task_id: UUID of the task
    :return: Redis key string
    """

    return f"user_tasks:{kind}:{user_id}:{task_id}"

def parse_task_key(key: str) -> Tuple[str, int, str]:
    """
    Parse a Redis task key into its components.
    
    :param key: Redis key in format user_tasks:{kind}:{user_id}:{task_id}
    :return: Tuple of (kind, user_id, task_id)
    :raises ValueError: If key format is invalid
    """

    parts = key.split(":")
    
    if len(parts) != 4 or parts[0] != "user_tasks":
        raise ValueError(f"Invalid task key format: {key}")
    
    _, kind, user_id, task_id = parts
    return kind, int(user_id), task_id

def make_task_queue_name() -> str:
    """Get the name of the task queue in Redis."""

    return "user_tasks_queue"

def make_user_tasks_pattern(user_id: int) -> str:
    """
    Generate a Redis SCAN pattern for all tasks belonging to a user.
    
    :param user_id: User's database ID
    :return: Pattern string for SCAN operation
    """

    return f"user_tasks:*:{user_id}:*"

def make_running_tasks_pattern() -> str:
    """
    Generate a Redis SCAN pattern for finding potentially stale running tasks.
    
    :return: Pattern string for SCAN operation
    """

    return "user_tasks:*:*:*"

def make_kind_agnostic_user_task_pattern(user_id: int, task_id: str) -> str:
    return make_task_key(
        kind="*",
        user_id=user_id,
        task_id=task_id
    )