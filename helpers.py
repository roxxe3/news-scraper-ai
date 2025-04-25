from datetime import datetime
from urllib.parse import unquote
import os
import logging
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('news_scraper')

def process_article_dates(dates_text):
    """
    Process and extract dates from article text
    Returns a list of [published_date, updated_date] in ISO format
    """
    if not dates_text:
        return [None, None]

    try:
        date_parts = []
        if "Mis à jour le" in dates_text:
            split_parts = dates_text.split("Mis à jour le")
            published_text = split_parts[0].strip()
            updated_text = "Mis à jour le " + split_parts[1].strip()
            date_parts = [published_text, updated_text]
        else:
            date_parts = [dates_text.strip(), None]

        result_dates = []
        for date_text in date_parts:
            if not date_text:
                result_dates.append(None)
                continue

            if date_text.startswith("Publié le"):
                date_text = " ".join(date_text.split()[2:])
            elif date_text.startswith("Mis à jour le"):
                date_text = " ".join(date_text.split()[4:])

            parts = date_text.split()
            if len(parts) < 5:
                result_dates.append(None)
                continue

            day = int(parts[0])
            month_abbr_fr = parts[1]
            year = int(parts[2])
            time_str = parts[4]
            hour, minute = map(int, time_str.split(':'))

            month_dict_fr = {
                'janv.': 1, 'févr.': 2, 'mars': 3, 'avr.': 4, 'mai': 5, 'juin': 6,
                'juil.': 7, 'août': 8, 'sept.': 9, 'oct.': 10, 'nov.': 11, 'déc.': 12
            }

            month = month_dict_fr.get(month_abbr_fr.lower())
            if not month:
                result_dates.append(None)
                continue

            dt_object = datetime(year, month, day, hour, minute)
            result_dates.append(dt_object.isoformat())

        while len(result_dates) < 2:
            result_dates.append(None)

        return result_dates[:2]

    except Exception as e:
        logger.error(f"Error processing dates: {e}")
        return [None, None]

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