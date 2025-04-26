import hrequests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, quote, unquote
import json
from helpers import logger  # Import the logger
import warnings

# Suppress the hrequests warning about the optional dependencies
warnings.filterwarnings("ignore", message="Please run pip install hrequests")

from datetime import datetime, timedelta, timezone

class LesEchosScraper:
    """
    Class to scrape articles from LesEchos website
    """
    def __init__(self, base_url='https://www.lesechos.fr', verbose=False):
        self.base_url = base_url
        self.verbose = verbose
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }
        # Get yesterday's date
        self.yesterday = (datetime.now() - timedelta(days=1)).date()
        # Add all category URLs
        self.category_urls = [
            'https://www.lesechos.fr',
            'https://www.lesechos.fr/idees-debats',
            'https://www.lesechos.fr/economie-france',
            'https://www.lesechos.fr/politique-societe',
            'https://www.lesechos.fr/industrie-services',
            'https://www.lesechos.fr/bourse',
            'https://www.lesechos.fr/monde',
            'https://www.lesechos.fr/tech-medias',
            'https://www.lesechos.fr/start-up',
            'https://www.lesechos.fr/pme-regions',
            'https://www.lesechos.fr/patrimoine',
            'https://www.lesechos.fr/travailler-mieux',
            'https://www.lesechos.fr/weekend'
        ]
    
    def get_articles_urls_from_page(self, url):
        """
        Get non-premium article URLs from a specific page
        
        Args:
            url (str): URL of the page to scrape
            
        Returns:
            list: List of article dictionaries with title and link
        """
        response = hrequests.get(url, headers=self.headers)
        items = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')
            for article in articles:
                title_tag = article.find('h3')
                if title_tag and not title_tag.find('span'):  # Skip if <h3> contains a <span> (premium)
                    link = article.find('a')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        # Ensure the link is absolute
                        if href.startswith('/'):
                            full_link = f"https://www.lesechos.fr{href}"
                        else:
                            full_link = href
                            
                        item = {
                            "title": title_tag.get_text().replace('\xa0', ' ').strip(),
                            "link": full_link,
                            "category": url.split('https://www.lesechos.fr/')[-1] or "homepage"
                        }
                        items.append(item)
            
            if self.verbose:
                logger.info(f"Found {len(items)} non-premium articles on {url}")
            return items
        else:
            logger.error(f"Failed to retrieve articles from {url}. Status code: {response.status_code}")
            return []
    
    def get_articles_urls(self):
        """
        Get non-premium article URLs from all category pages
        
        Returns:
            list: Combined list of article dictionaries from all pages
        """
        all_articles = []
        
        # Scrape articles from all category URLs
        for category_url in self.category_urls:
            if self.verbose:
                logger.info(f"Scraping category: {category_url}")
            category_articles = self.get_articles_urls_from_page(category_url)
            all_articles.extend(category_articles)
            
        # Remove duplicates based on article links
        unique_articles = []
        seen_links = set()
        
        for article in all_articles:
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                unique_articles.append(article)
                
        if self.verbose:
            logger.info(f"Total unique non-premium articles found: {len(unique_articles)}")
        return unique_articles

    def fetch_articles(self):
        """
        Fetch only articles published yesterday using meta tags.
        
        Returns:
            list: List of article dictionaries published yesterday.
        """
        articles = self.get_articles_urls()
        yesterday_articles = []

        # Define the start and end of yesterday as offset-aware datetimes
        now = datetime.now(timezone.utc)  # Current time in UTC
        yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        total = len(articles)
        if self.verbose:
            logger.info(f"Processing {total} articles to extract dates...")

        for i, article in enumerate(articles):
            if self.verbose:
                logger.debug(f"Processing article {i+1}/{total}: {article['title'][:30]}...")
            response = hrequests.get(article['link'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract publication time from meta tags
                published_time = soup.find('meta', property='article:published_time')
                modified_time = soup.find('meta', property='article:modified_time')

                if published_time:
                    article["published_date"] = published_time["content"]
                if modified_time:
                    article["updated_date"] = modified_time["content"]

                try:
                    # Parse the published_date as an offset-aware datetime
                    pub_date = datetime.fromisoformat(published_time["content"].replace("Z", "+00:00"))
                    if yesterday_start <= pub_date <= yesterday_end:
                        yesterday_articles.append(article)
                        if self.verbose:
                            logger.info(f"Found yesterday's article: {article['title'][:30]}")
                except ValueError as e:
                    logger.error(f"Error parsing date for article: {article['title'][:30]} - {e}")
            else:
                logger.error(f"Failed to retrieve article: {article['link']} (Status: {response.status_code})")

        logger.info(f"Found {len(yesterday_articles)} articles published yesterday.")
        return yesterday_articles
    
    def scrape_article_content(self, articles, email, password):
        """
        Scrape full article content for all articles using login credentials
        
        Args:
            articles (list): List of dictionaries, each containing a 'link' key for the article URL.
            email (str): Email for login.
            password (str): Password for login.
        """
        if not articles:
            logger.warning("No articles provided to scrape content")
            return []
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Modify the login URL: extract the path from the first article URL and encode it
            original_link = articles[0]['link']
            path = urlparse(original_link).path
            login_url = f"https://www.lesechos.fr/connexion?redirect={quote(path)}"

            page.goto(login_url)
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_selector('.post-paywall')

            total = len(articles)
            for i, article in enumerate(articles):
                if self.verbose:
                    logger.info(f"Scraping content for article {i+1}/{total}: {article.get('title', 'Untitled')[:30]}...")
                decoded_url = unquote(article['link'])
                page.goto(decoded_url)

                try:
                    page.wait_for_selector('.post-paywall', timeout=5000)
                    html = page.inner_html('.post-paywall')
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remove unwanted tags
                    for tag in soup(["script", "style"]):
                        tag.decompose()

                    # Remove unwanted divs
                    for div in soup.find_all('div', class_='sc-nlqesd-4'):
                        div.decompose()

                    # Extract article content
                    article_text = '\n\n'.join(
                        tag.get_text(separator=" ", strip=True) for tag in soup.find_all(['p', 'h3'])
                    )

                    article["content"] = article_text
                    if self.verbose:
                        logger.info(f"Article '{article.get('title', 'Untitled')[:30]}...' content scraped")
                except Exception as e:
                    logger.error(f"Failed to scrape {decoded_url}: {e}")

            page.close()
            browser.close()
        return articles

    def save_articles_to_json(self, articles, filename='articles.json'):
        """
        Save articles to a JSON file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(articles)} articles to {filename}")