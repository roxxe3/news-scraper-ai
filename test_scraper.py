#!/usr/bin/env python3
import argparse
from scraper import LesEchosScraper
from helpers import get_credentials, logger
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Test the news scraper functionality")
    parser.add_argument("--articles", type=int, default=5, help="Number of articles to test with")
    parser.add_argument("--content", action="store_true", help="Test content scraping with login")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache before testing")
    parser.add_argument("--no-cache", action="store_true", help="Don't use cache for this test")
    parser.add_argument("--output-dir", default="output", help="Directory to save test results")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Initialize scraper
    scraper = LesEchosScraper(verbose=True)
    
    # Clear cache if requested
    if args.clear_cache:
        scraper.clear_cache()
        logger.info("Cache cleared")
    
    # First get articles with basic info and dates
    logger.info(f"Fetching {args.articles} articles with dates...")
    articles = scraper.test_mode(args.articles)
    
    if not articles:
        logger.error("No articles found to test")
        return
        
    # Save basic articles
    basic_output = os.path.join(args.output_dir, "test_articles.json")
    with open(basic_output, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
    logger.info(f"Saved {len(articles)} articles with dates to {basic_output}")
    
    # If content scraping is requested, do that as well
    if args.content:
        logger.info("Testing content scraping...")
        email, password = get_credentials()
        articles_with_content = scraper.scrape_article_content(articles, email, password)
        
        if articles_with_content:
            # Save articles with content
            content_output = os.path.join(args.output_dir, "test_articles_with_content.json")
            with open(content_output, "w", encoding="utf-8") as f:
                json.dump(articles_with_content, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved {len(articles_with_content)} articles with content to {content_output}")
        else:
            logger.error("Failed to scrape article content")
    
    logger.info("Testing completed successfully")

if __name__ == "__main__":
    main() 