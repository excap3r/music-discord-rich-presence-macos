"""
Helper utilities for Deezer RPC
"""
import time
import platform


def get_os_name():
    """Get the current operating system name

    Returns:
        str: The operating system name (Windows, macOS, Linux)
    """
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    return system


def format_time(seconds):
    """Format seconds as mm:ss

    Args:
        seconds (int): Number of seconds

    Returns:
        str: Formatted time string (mm:ss)
    """
    if seconds < 0:
        return "0:00"
    
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


def throttle(interval):
    """Function decorator to throttle function calls

    Args:
        interval (float): Minimum seconds between calls

    Returns:
        function: Decorated function
    """
    def decorator(func):
        last_called = [0.0]
        
        def wrapper(*args, **kwargs):
            current_time = time.time()
            elapsed = current_time - last_called[0]
            
            if elapsed >= interval:
                last_called[0] = current_time
                return func(*args, **kwargs)
            return None
            
        return wrapper
    return decorator 