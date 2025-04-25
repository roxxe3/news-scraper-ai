import hrequests
from bs4 import BeautifulSoup
from pprint import pprint
from helpers import process_article_dates

url = 'https://www.lesechos.fr'

#this function scrap the free and premium articles (to use later)
# def get_articles_urls():
#     url = 'https://www.lesechos.fr'
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
#     }
#     response = hrequests.get(url, headers=headers)
#     items = []
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.content, 'html.parser')
        

        
#         articles = soup.find_all('article')  # Find all articles on the page
#         for article in articles:
#             title = article.find('h3')  # Example of title extraction
#             if title:
#                 item = {
#                     "title": title.get_text(),
#                     "link": url + article.find('a')['href'] if article.find('a') else ""
#                 }
#             items.append(item)
#         print(f"Total articles found: {len(articles)}")

#         return items
#     else:
#         print(f"Failed to retrieve articles. Status code: {response.status_code}")
#         return []

def get_articles_urls():
    url = 'https://www.lesechos.fr'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }
    response = hrequests.get(url, headers=headers)
    items = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        articles = soup.find_all('article')  # Find all articles on the page
        for article in articles:
            title_tag = article.find('h3')
            if title_tag and not title_tag.find('span'):  # Skip if <h3> contains a <span>
                item = {
                    "title": title_tag.get_text().replace('\xa0', ' ').strip(),
                    "link": url + article.find('a')['href'] if article.find('a') else ""
                }
                items.append(item)
        print(f"Total non-premium articles found: {len(items)}")

        return items
    else:
        print(f"Failed to retrieve articles. Status code: {response.status_code}")
        return []

def save_html_to_file(html_content, filename="output.html"):
    """
    Save the given HTML content to a file for easier inspection.
    """
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"HTML content saved to '{filename}'. Open it in a browser to inspect.")



# Original version (commented out)
def fetch_articles():
    articles = get_articles_urls()
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
            print(article)
        
        return updated_articles
    else:
        return []


def fetch_first_article():
    articles = get_articles_urls()
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
    else:
        print("No articles found.")
        
fetch_articles()


