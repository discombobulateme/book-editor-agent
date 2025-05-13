#!/usr/bin/env python3
"""
Terminal Colors Utility
Provides colorful terminal output functions for book editor agents.
Can be imported by multiple scripts for consistent styling.
"""

import os
import sys
import time
import threading
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

# Loading spinner class for progress indication
class Spinner:
    """A spinner class that shows a spinning animation while a process is running"""
    
    def __init__(self, message="Processing...", spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", color=Fore.CYAN):
        self.message = message
        self.spinner_chars = spinner_chars
        self.color = color
        self.stop_event = threading.Event()
        self.spinner_thread = None
        self.start_time = None
        self.total_time = 0
    
    def spin(self):
        i = 0
        while not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            if should_use_colors():
                sys.stdout.write(f"\r{self.color}{self.spinner_chars[i % len(self.spinner_chars)]} {self.message} [{time_str}]{Style.RESET_ALL}")
            else:
                sys.stdout.write(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message} [{time_str}]")
                
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    
    def start(self, message=None):
        """Start the spinner with an optional new message"""
        if message:
            self.message = message
            
        self.start_time = time.time()
        self.stop_event.clear()
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
        return self
    
    def stop(self, message=None):
        """Stop the spinner and optionally show a completion message"""
        self.stop_event.set()
        if self.spinner_thread:
            self.spinner_thread.join()
        
        self.total_time = time.time() - self.start_time
        minutes, seconds = divmod(int(self.total_time), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")  # Clear the line
        
        if message:
            if should_use_colors():
                print(f"{Colors.SUCCESS}✅ {message} [{time_str}]{Style.RESET_ALL}")
            else:
                print(f"✅ {message} [{time_str}]")
        
        return self.total_time

class StatusUpdatingSpinner(Spinner):
    """A spinner that periodically updates its message to keep the user informed during long operations"""
    
    def __init__(self, message="Processing...", spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", color=Fore.CYAN, 
                 update_interval=30, updates=None):
        """
        Initialize a status updating spinner
        
        Args:
            message (str): Initial message to display
            spinner_chars (str): Characters to use for spinning animation
            color: Color to use for the spinner
            update_interval (int): Time in seconds between message updates
            updates (list): List of messages to cycle through
        """
        super().__init__(message, spinner_chars, color)
        self.update_interval = update_interval
        self.updates = updates or [
            "Still working...",
            "This may take a while...",
            "Processing your request...",
            "Please wait...",
            "Operation in progress..."
        ]
        self.last_update_time = 0
        self.update_index = 0
    
    def spin(self):
        """Override spin method to update message periodically"""
        i = 0
        self.last_update_time = time.time()
        
        while not self.stop_event.is_set():
            # Calculate elapsed time and format it
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # Check if it's time to update the message
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.update_index = (self.update_index + 1) % len(self.updates)
                self.message = self.updates[self.update_index]
                self.last_update_time = current_time
            
            # Display spinner with current message and elapsed time
            if should_use_colors():
                sys.stdout.write(f"\r{self.color}{self.spinner_chars[i % len(self.spinner_chars)]} {self.message} [{time_str}]{Style.RESET_ALL}")
            else:
                sys.stdout.write(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {self.message} [{time_str}]")
                
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

class ConnectionMonitoringSpinner(Spinner):
    """A spinner that actively monitors connection status during API calls"""
    
    def __init__(self, message="Processing...", spinner_chars="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", color=Fore.CYAN,
                 check_interval=5, connection_object=None, timeout=60):
        """
        Initialize a connection monitoring spinner
        
        Args:
            message (str): Initial message to display
            spinner_chars (str): Characters to use for spinning animation
            color: Color to use for the spinner
            check_interval (int): Time in seconds between connection checks
            connection_object: The connection object to monitor (e.g., httpx client, requests session)
            timeout (int): Maximum time in seconds to wait for a status check before assuming connection issues
        """
        super().__init__(message, spinner_chars, color)
        self.check_interval = check_interval
        self.connection_object = connection_object
        self.timeout = timeout
        self.last_check_time = 0
        self.connection_status = "Connected"
        self.last_activity_time = None
        self.request_in_progress = False
        self.stalled_threshold = 30  # Number of seconds after which to consider connection stalled
    
    def start_request(self):
        """Mark that a request has been started"""
        self.request_in_progress = True
        self.last_activity_time = time.time()
        
        # Make sure to start the spinner if it's not already started
        if self.start_time is None:
            self.start()
            
        return self
    
    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity_time = time.time()
        self.connection_status = "Active"
    
    def check_connection(self):
        """Check the connection status
        In a real implementation, this would ping the API or check socket status
        """
        # We can't directly check Claude API status in most cases,
        # but we can check for timeouts and report the last known activity time
        
        if not self.request_in_progress:
            return "Idle"
        
        current_time = time.time()
        
        if self.last_activity_time is None:
            return "Unknown"
            
        time_since_activity = current_time - self.last_activity_time
        
        if time_since_activity > self.timeout:
            return f"Connection may be lost (no activity for {int(time_since_activity)}s)"
        elif time_since_activity > self.stalled_threshold:
            return f"Waiting for response (inactive for {int(time_since_activity)}s)"
        else:
            return "Connected"
    
    def spin(self):
        """Override spin method to monitor connection status"""
        i = 0
        self.last_check_time = time.time()
        
        while not self.stop_event.is_set():
            # Calculate elapsed time and format it
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # Check connection status at regular intervals
            current_time = time.time()
            if current_time - self.last_check_time >= self.check_interval:
                self.connection_status = self.check_connection()
                self.last_check_time = current_time
            
            # Create status message that includes connection info
            status_message = self.message
            
            # For long-running operations, add connection status
            if elapsed > 10 and self.connection_status != "Connected":
                status_message = f"{self.message} - {self.connection_status}"
            
            # Display spinner with current message and elapsed time
            if should_use_colors():
                status_color = self.color
                if "lost" in self.connection_status.lower():
                    status_color = Fore.RED
                elif "waiting" in self.connection_status.lower():
                    status_color = Fore.YELLOW
                
                sys.stdout.write(f"\r{status_color}{self.spinner_chars[i % len(self.spinner_chars)]} {status_message} [{time_str}]{Style.RESET_ALL}")
            else:
                sys.stdout.write(f"\r{self.spinner_chars[i % len(self.spinner_chars)]} {status_message} [{time_str}]")
                
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
    
    def stop(self, message=None):
        """Stop the spinner and optionally show a completion message"""
        self.request_in_progress = False
        
        # Handle the case where start() was never called (start_time would be None)
        if self.start_time is None:
            self.start_time = time.time()  # Set it to now to avoid errors
            
        return super().stop(message)

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
    
    # Demonstrate the spinner
    print("\nSpinner Demo - Press Ctrl+C to stop")
    try:
        spinner = Spinner("Loading...").start()
        time.sleep(5)  # Simulate work for 5 seconds
        spinner.stop("Loading completed")
    except KeyboardInterrupt:
        print("\nSpinner demo stopped")
    
    # Demonstrate the status updating spinner
    print("\nConnection Monitoring Spinner Demo - Press Ctrl+C to stop")
    try:
        spinner = ConnectionMonitoringSpinner(
            message="Processing API request...",
            check_interval=2  # Check every 2 seconds for demo
        ).start_request()
        
        # Simulate activity and delays
        time.sleep(3)
        spinner.update_activity()
        time.sleep(3)
        spinner.update_activity()
        
        # Simulate a longer delay
        time.sleep(6)
        
        # Simulate activity again
        spinner.update_activity()
        time.sleep(2)
        
        spinner.stop("Operation completed successfully")
    except KeyboardInterrupt:
        print("\nMonitoring spinner demo stopped")
    
    print("\nSet DEBUG_COLORS=0 in environment to disable colored output") 