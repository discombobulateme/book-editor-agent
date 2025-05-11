#!/usr/bin/env python3
"""
Terminal Colors Utility
Provides colorful terminal output functions for book editor agents.
Can be imported by multiple scripts for consistent styling.
"""

import os
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Environment variable to control whether to use colors
# Set DEBUG_COLORS=0 to disable colored output
def should_use_colors():
    """Check if colors should be used based on environment variable"""
    return os.environ.get('DEBUG_COLORS', '1') == '1'

# Define color constants for better readability
class Colors:
    TITLE = Fore.CYAN + Style.BRIGHT
    SUBTITLE = Fore.BLUE + Style.BRIGHT
    SUCCESS = Fore.GREEN + Style.BRIGHT
    WARNING = Fore.YELLOW + Style.BRIGHT
    ERROR = Fore.RED + Style.BRIGHT
    INFO = Fore.WHITE + Style.BRIGHT
    STAT_LABEL = Fore.CYAN
    STAT_VALUE = Fore.GREEN
    HIGHLIGHT = Fore.MAGENTA + Style.BRIGHT
    FILE = Fore.BLUE
    PROMPT = Fore.YELLOW
    TIMER = Fore.GREEN
    HEADER = Fore.WHITE + Back.BLUE + Style.BRIGHT
    SEPARATOR = Fore.BLUE
    REVIEW_NOTES = Fore.GREEN + Style.BRIGHT

# Convenience functions for pretty terminal output
def print_header(text):
    """Print a formatted header"""
    if should_use_colors():
        print(f"\n{Colors.HEADER} {text} {Style.RESET_ALL}")
        print(f"{Colors.SEPARATOR}{'='*80}{Style.RESET_ALL}")
    else:
        print(f"\n{text}")
        print('='*80)

def print_subheader(text):
    """Print a formatted subheader"""
    if should_use_colors():
        print(f"\n{Colors.SUBTITLE}▶ {text}{Style.RESET_ALL}")
        print(f"{Colors.SEPARATOR}{'-'*50}{Style.RESET_ALL}")
    else:
        print(f"\n▶ {text}")
        print('-'*50)

def print_stats(label, value, original=None):
    """Print a statistic with optional comparison to original"""
    if should_use_colors():
        if original is not None:
            ratio = value / original * 100 if original > 0 else 0
            color = Fore.GREEN if 90 <= ratio <= 110 else Fore.YELLOW if 70 <= ratio < 90 or 110 < ratio <= 130 else Fore.RED
            print(f"  {Colors.STAT_LABEL}• {label}: {Colors.STAT_VALUE}{value}{Style.RESET_ALL} ({color}{ratio:.1f}%{Style.RESET_ALL} of original)")
        else:
            print(f"  {Colors.STAT_LABEL}• {label}: {Colors.STAT_VALUE}{value}{Style.RESET_ALL}")
    else:
        if original is not None:
            ratio = value / original * 100 if original > 0 else 0
            print(f"  • {label}: {value} ({ratio:.1f}% of original)")
        else:
            print(f"  • {label}: {value}")

def success(message):
    """Print a success message"""
    if should_use_colors():
        print(f"{Colors.SUCCESS}✅ {message}{Style.RESET_ALL}")
    else:
        print(f"SUCCESS: {message}")

def warning(message):
    """Print a warning message"""
    if should_use_colors():
        print(f"{Colors.WARNING}⚠️ {message}{Style.RESET_ALL}")
    else:
        print(f"WARNING: {message}")

def error(message):
    """Print an error message"""
    if should_use_colors():
        print(f"{Colors.ERROR}❌ {message}{Style.RESET_ALL}")
    else:
        print(f"ERROR: {message}")

def info(message):
    """Print an info message"""
    if should_use_colors():
        print(f"{Colors.INFO}📝 {message}{Style.RESET_ALL}")
    else:
        print(f"INFO: {message}")

def debug(message):
    """Print a debug message, but only if DEBUG_COLORS is enabled"""
    if should_use_colors():
        print(f"{Colors.HIGHLIGHT}🔍 DEBUG: {message}{Style.RESET_ALL}")

# Example usage when this module is run directly
if __name__ == "__main__":
    print_header("Terminal Colors Demo")
    print_subheader("Statistics Example")
    print_stats("Words", 500, 450)
    print_stats("Characters", 2500)
    
    success("Operation completed successfully")
    warning("Something might need attention")
    error("An error occurred")
    info("Just some information")
    debug("This is a debug message")
    
    print("\nSet DEBUG_COLORS=0 in environment to disable colored output") 