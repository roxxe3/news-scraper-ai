import hrequests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, quote, unquote
import json
from helpers import process_article_dates

class LesEchosScraper:
    """
    Class to scrape articles from LesEchos website
    """
    def __init__(self, base_url='https://www.lesechos.fr'):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }

    def get_articles_urls(self):
        """
        Get non-premium article URLs from the main page
        """
        response = hrequests.get(self.base_url, headers=self.headers)
        items = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')  # Find all articles on the page
            for article in articles:
                title_tag = article.find('h3')
                if title_tag and not title_tag.find('span'):  # Skip if <h3> contains a <span>
                    item = {
                        "title": title_tag.get_text().replace('\xa0', ' ').strip(),
                        "link": self.base_url + article.find('a')['href'] if article.find('a') else ""
                    }
                    items.append(item)
            print(f"Total non-premium articles found: {len(items)}")
            return items
        else:
            print(f"Failed to retrieve articles. Status code: {response.status_code}")
            return []

    def fetch_articles(self):
        """
        Fetch all articles and extract dates
        """
        articles = self.get_articles_urls()
        updated_articles = []
        if articles:
            for article in articles:
                response = hrequests.get(article['link'])
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    content = soup.find('div', class_='sc-1h4katp-1')
                    if content:
                        dates_result = process_article_dates(content.get_text())
                        article["published_date"] = dates_result[0]
                        article["updated_date"] = dates_result[1]
                updated_articles.append(article)
            
            return updated_articles
        else:
            return []

    def fetch_first_article(self):
        """
        Fetch only the first article for testing
        """
        articles = self.get_articles_urls()
        if articles:
            article = articles[0]  # Process only the first article
            response = hrequests.get(article['link'])
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                dates = soup.find('div', class_='sc-1h4katp-1')

                if dates:
                    dates_result = process_article_dates(dates.get_text())
                    article["published_date"] = dates_result[0]
                    article["updated_date"] = dates_result[1]
                else:
                    print("Content not found for article:", article['title'])
                
            else:
                print("Failed to retrieve article:", article['link'])
            print(article)
            return article
        else:
            print("No articles found.")
            return None
            
    def scrape_article_content(self, articles, email, password):
        """
        Scrape full article content for all articles using login credentials
        
        Args:
            articles (list): List of dictionaries, each containing a 'link' key for the article URL.
            email (str): Email for login.
            password (str): Password for login.
        """
        if not articles:
            print("No articles provided to scrape content")
            return []
            
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
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

            for article in articles:
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
                    print(f"Article '{article.get('title', 'Untitled')}' content scraped")
                except Exception as e:
                    print(f"Failed to scrape {decoded_url}: {e}")

            page.close()
            browser.close()
        return articles


    def save_articles_to_json(self, articles, filename='articles.json'):
        """
        Save articles to a JSON file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(articles)} articles to {filename}")