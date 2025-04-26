import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Import your modules
from main import LesEchosScraper
from helpers import get_credentials, create_output_directory, logger, set_console_logging, streamlit_handler, log_to_streamlit
from AI_filter import filter_articles
from save_db import Article, Session

def is_yesterday(date_str):
    try:
        pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        return pub_date.date() == yesterday
    except Exception:
        return False

def load_yesterday_articles(json_path):
    if not os.path.exists(json_path):
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        articles = json.load(f)
    # Check if all articles are from yesterday
    if all("published_date" in a and is_yesterday(a["published_date"]) for a in articles):
        return articles
    return None

def run_pipeline(topic="Artificial Intelligence", output="filtered_articles.json", free_only=False, sample=False, verbose=False, streamlit_mode=False, streamlit_container=None):
    """
    Run the full pipeline: scrape, filter and save articles
    
    Args:
        topic (str): Topic to filter for
        output (str): Output filename
        free_only (bool): Only scrape free articles
        sample (bool): Only process first article
        verbose (bool): Enable verbose output
        streamlit_mode (bool): Whether running from Streamlit (controls console output)
        streamlit_container: Optional Streamlit container for showing real-time logs
    """
    # Set up Streamlit log handler if provided
    if streamlit_container:
        streamlit_handler.set_container(streamlit_container)
        
    # Control console logging based on streamlit_mode
    if streamlit_mode:
        # We want to see output in the Streamlit UI but not clutter the terminal
        set_console_logging(enabled=verbose)
    else:
        # In terminal mode, always show output
        set_console_logging(enabled=True)
    
    # 1. Try to load yesterday's articles from JSON
    create_output_directory("output")
    json_path = "output/articles.json"
    articles = load_yesterday_articles(json_path)

    if articles is not None:
        message = f"Loaded {len(articles)} articles from {json_path}"
        if streamlit_container:
            log_to_streamlit(message)
        else:
            logger.info(message)
    else:
        # Scrape articles if not available or outdated
        message = "Starting article scraping process..."
        if streamlit_container:
            log_to_streamlit(message)
        else:
            logger.info(message)
            
        # Create scraper with real-time feedback
        scraper = LesEchosScraper(verbose=streamlit_container is not None)
        if sample:
            article = scraper.fetch_first_article()
            articles = [article] if article else []
        else:
            articles = scraper.fetch_articles()
            if not articles:
                message = "No articles found to process. Exiting."
                if streamlit_container:
                    log_to_streamlit(message)
                else:
                    logger.error(message)
                sys.exit(1)
            if not free_only:
                email, password = get_credentials()
                articles = scraper.scrape_article_content(articles, email, password)
        
        # Save scraped articles for future use
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)
        
        message = f"Scraped and saved {len(articles)} articles to {json_path}"
        if streamlit_container:
            log_to_streamlit(message)
        else:
            logger.info(message)

    # 2. Filter articles using AI
    message = f"Starting filtering process for topic: '{topic}'..."
    if streamlit_container:
        log_to_streamlit(message)
    else:
        logger.info(message)
        
    # Generate dynamic output filename based on topic
    output = f"filtered_articles_{topic.lower().replace(' ', '_')}.json"
    
    filtered = filter_articles(
        articles, 
        topic=topic,
        verbose=streamlit_container is not None,
        streamlit_mode=streamlit_mode
    )
    
    message = f"Filtered down to {len(filtered)} articles related to '{topic}'."
    if streamlit_container:
        log_to_streamlit(message)
    else:
        logger.info(message)
    
    # Save filtered articles to JSON
    filtered_json_path = f"output/{output}"
    with open(filtered_json_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=4, ensure_ascii=False)
    
    message = f"Filtered articles saved to {filtered_json_path}"
    if streamlit_container:
        log_to_streamlit(message)
    else:
        logger.info(message)
    
    # 3. Save filtered articles to DB
    session = Session()
    for art in filtered:
        db_article = Article(
            title=art.get("title", ""),
            link=art.get("link", ""),
            category=art.get("category", ""),
            topic=topic,  # Add the topic column here
            published_date=art.get("published_date"),
            updated_date=art.get("updated_date"),
            content=art.get("content", "")
        )
        session.add(db_article)
    session.commit()
    session.close()
    
    message = f"Saved {len(filtered)} articles to the database with topic '{topic}'."
    if streamlit_container:
        log_to_streamlit(message)
    else:
        logger.info(message)
        
    return filtered

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Full pipeline: scrape, filter, save to DB")
    parser.add_argument('--topic', type=str, default="Artificial Intelligence", help='Topic to filter for')
    parser.add_argument('--free-only', action='store_true', help='Only scrape free articles')
    parser.add_argument('--sample', action='store_true', help='Run with only first article (for testing)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    run_pipeline(
        topic=args.topic,
        free_only=args.free_only,
        sample=args.sample,
        verbose=args.verbose
    )