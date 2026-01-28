"""Terminal color utilities using colorama for theme compatibility."""

from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)


def colored(text, color_code):
    """Wrap text with color code."""
    return f"{color_code}{text}{Style.RESET_ALL}"


def header(text):
    """Format a section header."""
    return colored(f"=== {text} ===", Style.BRIGHT + Fore.CYAN)


def success(text):
    """Format a success message."""
    return colored(text, Fore.GREEN)


def error(text):
    """Format an error message."""
    return colored(text, Fore.RED)


def info(text):
    """Format an info message."""
    return colored(text, Fore.YELLOW)


def label(text):
    """Format a label."""
    return colored(text, Style.BRIGHT)


# Export color constants for direct use
class Colors:
    """Color constants for advanced usage."""
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT

    # Standard colors (theme-compatible)
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN

    # Bright variants (better theme contrast)
    BRIGHT_RED = Fore.LIGHTRED_EX
    BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    BRIGHT_YELLOW = Fore.LIGHTYELLOW_EX
    BRIGHT_BLUE = Fore.LIGHTBLUE_EX
    BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
    BRIGHT_CYAN = Fore.LIGHTCYAN_EX
