import hrequests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, quote, unquote
import json
from helpers import logger
import warnings
import os
from datetime import datetime, timedelta, timezone
import time
from requests.exceptions import RequestException, ConnectionError, Timeout

warnings.filterwarnings("ignore", message="Please run pip install hrequests")

class LesEchosScraper:
    """
    Class to scrape articles from LesEchos website
    """
    def __init__(self, base_url='https://www.lesechos.fr', verbose=False, cache_dir='cache', log_callback=None, max_retries=3, retry_delay=5):
        self.base_url = base_url
        self.verbose = verbose
        self.cache_dir = cache_dir
        self.log_callback = log_callback
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }
        self.yesterday = (datetime.now() - timedelta(days=1)).date()

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # uncomment to scrap all categories
        self.category_urls = [
            'https://www.lesechos.fr',
            'https://www.lesechos.fr/monde',
            #'https://www.lesechos.fr/politique-societe',
            # 'https://www.lesechos.fr/industrie-services',
            #'https://www.lesechos.fr/bourse',
            #'https://www.lesechos.fr/tech-medias',
            # 'https://www.lesechos.fr/start-up',
            # 'https://www.lesechos.fr/pme-regions',
            # 'https://www.lesechos.fr/patrimoine',
            # 'https://www.lesechos.fr/travailler-mieux','
        ]
    
    def log_message(self, msg, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"{timestamp} - news_scraper - {level} - {msg}"
        
        if level == "INFO":
            logger.info(msg)
        elif level == "ERROR":
            logger.error(msg)
        elif level == "WARNING":
            logger.warning(msg)
            
        if self.log_callback:
            self.log_callback(formatted_msg)

    def make_request(self, url, method='get', data=None):
        for attempt in range(self.max_retries):
            try:
                if method.lower() == 'get':
                    response = hrequests.get(url, headers=self.headers)
                else:
                    response = hrequests.post(url, headers=self.headers, data=data)
                if response.status_code >= 400:
                    raise RequestException(f"HTTP {response.status_code}: {response.text}")
                return response
                
            except ConnectionError as e:
                self.log_message(f"Connection error on attempt {attempt + 1}/{self.max_retries}: {e}", "ERROR")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
            except Timeout as e:
                self.log_message(f"Timeout error on attempt {attempt + 1}/{self.max_retries}: {e}", "ERROR")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
                
            except RequestException as e:
                self.log_message(f"Request error on attempt {attempt + 1}/{self.max_retries}: {e}", "ERROR")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
            
            except Exception as e:
                self.log_message(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {e}", "ERROR")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception(f"Failed to make request to {url} after {self.max_retries} attempts")

    def get_articles_urls_from_page(self, url, use_cache=True):
        """
        Get non-premium article URLs from a specific page
        
        Args:
            url (str): URL of the page to scrape
            use_cache (bool): Whether to use cached results
            
        Returns:
            list: List of article dictionaries with title and link
        """
        cache_file = os.path.join(self.cache_dir, f"{url.replace('/', '_')}.json")
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_items = json.load(f)
                if self.verbose:
                    self.log_message(f"Using cached data for {url}")
                return cached_items
            except json.JSONDecodeError as e:
                self.log_message(f"Invalid JSON in cache file {cache_file}: {e}", "WARNING")
            except Exception as e:
                self.log_message(f"Failed to load cache for {url}: {e}", "WARNING")

        try:
            response = self.make_request(url)
            items = []
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article')
            if not articles:
                self.log_message(f"No articles found on {url}. Page structure may have changed.", "WARNING")
                return []
                
            for article in articles:
                try:
                    title_tag = article.find('h3')
                    if title_tag and not title_tag.find('span'):
                        link = article.find('a')
                        if link and 'href' in link.attrs:
                            href = link['href']
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
                except Exception as e:
                    self.log_message(f"Error processing article on {url}: {e}", "WARNING")
                    continue
            
            if self.verbose:
                self.log_message(f"Found {len(items)} non-premium articles on {url}")
            if use_cache and items:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(items, f, indent=4, ensure_ascii=False)
                except Exception as e:
                    self.log_message(f"Failed to cache results for {url}: {e}", "WARNING")
            return items
            
        except Exception as e:
            self.log_message(f"Failed to retrieve articles from {url}: {e}", "ERROR")
            return []
    
    def get_articles_urls(self):
        """
        Get non-premium article URLs from all category pages
        
        Returns:
            list: Combined list of article dictionaries from all pages
        """
        all_articles = []
        for category_url in self.category_urls:
            if self.verbose:
                self.log_message(f"Scraping category: {category_url}")
            category_articles = self.get_articles_urls_from_page(category_url)
            all_articles.extend(category_articles)
            
        unique_articles = []
        seen_links = set()
        
        for article in all_articles:
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                unique_articles.append(article)
                
        if self.verbose:
            self.log_message(f"Total unique non-premium articles found: {len(unique_articles)}")
        return unique_articles

    def fetch_articles(self):
        """
        Fetch only articles published yesterday using meta tags.
        
        Returns:
            list: List of article dictionaries published yesterday.
        """
        articles = self.get_articles_urls()
        yesterday_articles = []
        now = datetime.now(timezone.utc)
        yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        total = len(articles)
        if self.verbose:
            self.log_message(f"Processing {total} articles to extract dates...")

        for i, article in enumerate(articles):
            if self.verbose:
                self.log_message(f"Processing article {i+1}/{total}: {article['title'][:30]}...")
            response = hrequests.get(article['link'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                published_time = soup.find('meta', property='article:published_time')
                modified_time = soup.find('meta', property='article:modified_time')
                if published_time:
                    article["published_date"] = published_time["content"]
                if modified_time:
                    article["updated_date"] = modified_time["content"]

                try:
                    pub_date = datetime.fromisoformat(published_time["content"].replace("Z", "+00:00"))
                    if yesterday_start <= pub_date <= yesterday_end:
                        yesterday_articles.append(article)
                        if self.verbose:
                            self.log_message(f"Found yesterday's article: {article['title'][:30]}")
                except ValueError as e:
                    self.log_message(f"Error parsing date for article: {article['title'][:30]} - {e}", "ERROR")
            else:
                self.log_message(f"Failed to retrieve article: {article['link']} (Status: {response.status_code})", "ERROR")

        if self.verbose:
            self.log_message(f"Found {len(yesterday_articles)} articles published yesterday.")
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
            self.log_message("No articles provided to scrape content")
            return []
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            original_link = articles[0]['link']
            path = urlparse(original_link).path
            login_url = f"https://www.lesechos.fr/connexion?redirect={quote(path)}"
            if self.verbose:
                self.log_message("Navigating to login page...")
            page.goto(login_url)
            page.wait_for_selector('input[name="email"]', state='visible')
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            
            try:
                page.wait_for_selector('.post-paywall', timeout=10000)
                if self.verbose:
                    self.log_message("Successfully logged in")
            except Exception as e:
                self.log_message(f"Login failed: {e}", "ERROR")
                browser.close()
                return []

            total = len(articles)
            for i, article in enumerate(articles):
                if self.verbose:
                    self.log_message(f"Scraping content for article {i+1}/{total}: {article.get('title', 'Untitled')[:30]}...")
                decoded_url = unquote(article['link'])
                page.goto(decoded_url)
                try:
                    page.wait_for_load_state('networkidle')
                    page.wait_for_selector('.post-paywall', timeout=10000)
                    html = page.inner_html('.post-paywall')
                    soup = BeautifulSoup(html, 'html.parser')
                    for tag in soup(["script", "style"]):
                        tag.decompose()
                    for div in soup.find_all('div', class_='sc-nlqesd-4'):
                        div.decompose()
                    article_text = '\n\n'.join(
                        tag.get_text(separator=" ", strip=True) for tag in soup.find_all(['p', 'h3'])
                    )
                    article["content"] = article_text
                    if self.verbose:
                        self.log_message(f"Article '{article.get('title', 'Untitled')[:30]}...' content scraped")
                except Exception as e:
                    self.log_message(f"Failed to scrape {decoded_url}: {e}", "ERROR")
                    page.wait_for_timeout(1000)

            page.close()
            browser.close()
        return articles

    def save_articles_to_json(self, articles, filename='articles.json'):
        """
        Save articles to a JSON file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        self.log_message(f"Saved {len(articles)} articles to {filename}")

    def test_mode(self, num_articles=5):
        """
        Run scraper in test mode with a small sample of articles
        
        Args:
            num_articles (int): Number of articles to fetch
            
        Returns:
            list: Sample of articles for testing
        """
        self.log_message(f"Running in test mode with {num_articles} articles")
        test_url = self.category_urls[0]
        articles = self.get_articles_urls_from_page(test_url, use_cache=True)
        sample_articles = articles[:num_articles]
        for article in sample_articles:
            try:
                response = hrequests.get(article['link'], headers=self.headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    published_time = soup.find('meta', property='article:published_time')
                    modified_time = soup.find('meta', property='article:modified_time')
                    if published_time:
                        article["published_date"] = published_time["content"]
                    if modified_time:
                        article["updated_date"] = modified_time["content"]
                    if self.verbose:
                        self.log_message(f"Added dates for article: {article['title'][:30]}...")
                else:
                    self.log_message(f"Failed to get dates for article: {article['link']}", "ERROR")
            except Exception as e:
                self.log_message(f"Error getting dates for article {article['title'][:30]}: {e}", "ERROR")
        
        if self.verbose:
            self.log_message(f"Processed {len(sample_articles)} articles with dates")
        return sample_articles

    def test_content_scraping(self, email, password, num_articles=1):
        """
        Test content scraping with a small sample
        
        Args:
            email (str): Login email
            password (str): Login password
            num_articles (int): Number of articles to test with
            
        Returns:
            list: Articles with scraped content
        """
        test_articles = self.test_mode(num_articles)
        if not test_articles:
            self.log_message("No articles found for testing")
            return []
            
        self.log_message(f"Testing content scraping with {len(test_articles)} articles")
        return self.scrape_article_content(test_articles, email, password)

    def clear_cache(self):
        """
        Clear all cached data
        """
        if os.path.exists(self.cache_dir):
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir)
                self.log_message("Cache cleared successfully")
            except Exception as e:
                self.log_message(f"Failed to clear cache: {e}", "ERROR")
