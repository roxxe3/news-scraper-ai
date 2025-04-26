from datetime import datetime
from urllib.parse import unquote
import os
import logging
import sys
import dotenv
import streamlit as st

# Configure logging
def configure_logging(level=logging.INFO, to_console=True):
    """
    Configure the logging system with customizable options
    
    Args:
        level: The logging level (default: INFO)
        to_console: Whether to output logs to console (default: True)
    """
    logger = logging.getLogger('news_scraper')
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Always log to file for debugging
    file_handler = logging.FileHandler('news_scraper.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Optionally log to console
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Initialize default logger
logger = configure_logging()

# Helper function to temporarily suppress console output
def set_console_logging(enabled=True):
    """Enable or disable console logging without affecting file logging"""
    logger = logging.getLogger('news_scraper')
    
    # Remove any existing console handlers
    for handler in list(logger.handlers):
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            logger.removeHandler(handler)
    
    # Add console handler if enabled
    if enabled:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

# Stream for showing feedback in the Streamlit UI
class StreamlitLogHandler:
    """Handler that displays logs in the Streamlit UI"""
    def __init__(self):
        self.st_container = None
        self.logs = []  # Store log history
    
    def set_container(self, container):
        """Set the Streamlit container to write logs to"""
        self.st_container = container
        
    def log(self, message):
        """Log a message to the Streamlit UI if a container is set"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_msg = f"{timestamp} - {message}"
        self.logs.append(formatted_msg)  # Add to history
        
        if self.st_container:
            # Display all logs as a continuous stream
            log_text = "\n".join(self.logs)
            self.st_container.text_area("Log Stream", log_text, height=300, disabled=True)

# Create a singleton instance of the StreamlitLogHandler
streamlit_handler = StreamlitLogHandler()

class StreamlitLoggingHandler(logging.Handler):
    """A custom logging handler that sends logs to the Streamlit UI"""
    
    def __init__(self, streamlit_handler):
        super().__init__()
        self.streamlit_handler = streamlit_handler
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        self.setFormatter(formatter)
    
    def emit(self, record):
        try:
            message = self.format(record)
            self.streamlit_handler.log(message)
        except Exception:
            self.handleError(record)

# Function to add Streamlit logging handler to logger
def enable_streamlit_logging(streamlit_container):
    """
    Configure logging to output to a Streamlit container
    
    Args:
        streamlit_container: Streamlit container to write logs to
    """
    logger = logging.getLogger('news_scraper')
    
    # Set the container for our singleton handler
    streamlit_handler.set_container(streamlit_container)
    
    # Add a StreamlitLoggingHandler to the logger
    st_logging_handler = StreamlitLoggingHandler(streamlit_handler)
    logger.addHandler(st_logging_handler)
    
    # Return the handler in case it needs to be removed later
    return st_logging_handler

def log_to_streamlit(message):
    """Utility function to log message to both logger and Streamlit UI"""
    logger.info(message)
    streamlit_handler.log(message)

def save_html_to_file(html_content, filename="output.html"):
    """
    Save the given HTML content to a file for easier inspection.
    """
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)
    logger.info(f"HTML content saved to '{filename}'. Open it in a browser to inspect.")

def create_output_directory(directory_name="output"):
    """
    Create a directory to store scraping results if it doesn't exist
    """
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        logger.info(f"Created directory: {directory_name}")
    return directory_name

def get_credentials():
    """
    Get credentials from environment variables or user input
    First checks for .env file, then falls back to user input
    """
    # Try to load .env file
    dotenv.load_dotenv()
    
    # Check for environment variables
    email = os.environ.get("LESECHOS_EMAIL")
    password = os.environ.get("LESECHOS_PASSWORD")
    
    # If either is missing, prompt the user
    if not email:
        email = input("Enter your email for Les Echos: ")
    if not password:
        password = input("Enter your password: ")
    
    return email, password