import os


def is_windows() -> bool:
    """
    States if running on Windows

    :return: True if running on Windows, False otherwise
    """
    return "nt" in os.name
