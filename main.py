#!/usr/bin/env python3
"""
News Scraper - A tool to scrape articles from Les Echos
"""
import argparse
import sys
import json
from scraper import LesEchosScraper
from helpers import get_credentials, create_output_directory, logger

def main():
    """
    Main entry point for the news scraper
    """
    parser = argparse.ArgumentParser(description='News Scraper for Les Echos')
    parser.add_argument('--free-only', action='store_true', help='Only scrape free articles (no login required)')
    parser.add_argument('--output', default='articles.json', help='Output file path (default: articles.json)')
    parser.add_argument('--sample', action='store_true', help='Run with only first article (for testing)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()
    
    # Create scraper instance
    scraper = LesEchosScraper()
    
    # Handle sample mode (only first article)
    if args.sample:
        article = scraper.fetch_first_article()
        if article:
            create_output_directory("output")
            with open(f"output/{args.output}", 'w', encoding='utf-8') as f:
                json.dump([article], f, indent=4, ensure_ascii=False)
            logger.info(f"Saved sample article to output/{args.output}")
        return
    
    # Get articles with basic info
    articles = scraper.fetch_articles()
    if not articles:
        logger.error("No articles found to process. Exiting.")
        sys.exit(1)
    
    logger.info(f"Found {len(articles)} articles")
    
    
    if not args.free_only:
        logger.info("Starting article content scraping (requires login)")
        
        # Get credentials from .env file or prompt user
        email, password = get_credentials()
            
        articles = scraper.scrape_article_content(articles, email, password)
    
    # Save results
    create_output_directory("output")
    scraper.save_articles_to_json(articles, f"output/{args.output}")

if __name__ == "__main__":
    main()