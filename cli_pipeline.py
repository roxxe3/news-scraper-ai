#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime
from scraper import LesEchosScraper
from AI_filter import filter_articles
from save_db import Article, Session, init_db
from helpers import get_credentials, create_output_directory, logger

def save_to_database(articles, topic=None):
    """Save articles to the database with optional topic filtering"""
    session = Session()
    try:
        for art in articles:
            # Convert string dates to datetime objects
            published_date = None
            updated_date = None
            if art.get("published_date"):
                published_date = datetime.fromisoformat(art["published_date"].replace("Z", "+00:00"))
            if art.get("updated_date"):
                updated_date = datetime.fromisoformat(art["updated_date"].replace("Z", "+00:00"))
            
            db_article = Article(
                title=art.get("title", ""),
                link=art.get("link", ""),
                category=art.get("category", ""),
                topic=topic,
                published_date=published_date,
                updated_date=updated_date,
                content=art.get("content", "")
            )
            session.add(db_article)
        
        session.commit()
        logger.info(f"Successfully saved {len(articles)} articles to database")
        return True
    except Exception as e:
        logger.error(f"Failed to save articles to database: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def run_cli_pipeline(topic=None, output_dir="output", free_only=False, sample=False, verbose=False, log_callback=None):
    """
    Run the complete pipeline: scrape articles, filter by topic, and save to database
    
    Args:
        topic (str): Topic to filter articles by
        output_dir (str): Directory to save output files
        free_only (bool): Whether to only scrape free articles
        sample (bool): Whether to only process the first article (for testing)
        verbose (bool): Whether to show verbose logging
        log_callback (callable): Optional callback function for logging in Streamlit
    """
    try:
        # Initialize scraper with the log callback
        scraper = LesEchosScraper(verbose=True, log_callback=log_callback)
        
        def log_message(msg):
            """Helper to handle both console and Streamlit logging"""
            logger.info(msg)
            if log_callback:
                log_callback(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - news_scraper - INFO - {msg}")
        
        log_message("Starting article scraping pipeline...")
        
        # Get articles from yesterday
        log_message("Fetching articles from yesterday...")
        articles = scraper.fetch_articles()
        
        if not articles:
            log_message("No articles found for yesterday")
            return False
            
        log_message(f"Found {len(articles)} articles from yesterday")
        
        # Apply sample option if requested
        if sample and articles:
            articles = [articles[0]]
            log_message("Sample mode: Using only the first article for testing")
        
        # Get login credentials and scrape content
        log_message("Getting login credentials...")
        email, password = get_credentials()
        
        log_message("Scraping article content...")
        articles_with_content = scraper.scrape_article_content(
            articles, 
            email, 
            password
        )
        
        # If free_only is set, filter out premium articles
        if free_only:
            articles_with_content = [article for article in articles_with_content if not article.get('is_premium', False)]
            log_message(f"Filtered to {len(articles_with_content)} free articles")
        
        if not articles_with_content:
            log_message("Failed to scrape article content")
            return False
        
        # Filter out articles without content
        valid_articles = [article for article in articles_with_content if article.get('content')]
        
        if not valid_articles:
            log_message("No articles with valid content found")
            return False
            
        log_message(f"Successfully scraped content for {len(valid_articles)} articles")
            
        # Save only articles with content
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, "articles_with_content.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(valid_articles, f, indent=4, ensure_ascii=False)
        log_message(f"Saved {len(valid_articles)} articles with content to {output_file}")
        
        # Apply AI filtering if topic is provided
        if topic:
            log_message(f"Filtering articles by topic: {topic}...")
            filtered_articles = filter_articles(valid_articles, topic)
            
            if filtered_articles:
                # Save filtered articles
                filtered_filename = f"filtered_articles_{topic.lower().replace(' ', '_')}.json"
                filtered_path = os.path.join(output_dir, filtered_filename)
                with open(filtered_path, "w", encoding="utf-8") as f:
                    json.dump(filtered_articles, f, indent=4, ensure_ascii=False)
                log_message(f"Saved {len(filtered_articles)} filtered articles to {filtered_path}")
                
                # Save to database
                log_message("Saving filtered articles to database...")
                save_to_database(filtered_articles, topic)
            else:
                log_message(f"No articles matched the topic: {topic}")
        
        log_message("Pipeline completed successfully!")
        return True
        
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(error_msg)
        if log_callback:
            log_callback(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - news_scraper - ERROR - {error_msg}")
        return False

def main():
    parser = argparse.ArgumentParser(description="News Scraper CLI Pipeline")
    parser.add_argument("--topic", type=str, help="Topic to filter articles (optional)")
    parser.add_argument("--output-dir", default="output", help="Output directory for JSON files")
    parser.add_argument("--free-only", action="store_true", help="Only scrape free articles")
    parser.add_argument("--sample", action="store_true", help="Only process first article (for testing)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    success = run_cli_pipeline(
        topic=args.topic,
        output_dir=args.output_dir,
        free_only=args.free_only,
        sample=args.sample,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()