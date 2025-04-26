import os
import json
from openai import OpenAI
import re
import argparse
import time
from helpers import logger, log_to_streamlit
import streamlit as st

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

openai_client = OpenAI(api_key=openai_api_key)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_filtered_filename(topic):
    # Convert topic to a valid filename by replacing spaces and special chars
    safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().lower()
    safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
    return f"output/filtered_articles_{safe_topic}.json"

def filter_articles(articles, topic="Artificial Intelligence", streamlit_mode=False):
    """
    Filter articles based on a topic using OpenAI's API.
    
    Args:
        articles (list): List of article dictionaries with content
        topic (str): Topic to filter for, defaults to "Artificial Intelligence"
        streamlit_mode (bool): Whether to use streamlit progress bar
    
    Returns:
        list: Filtered list of articles related to the topic
    """
    # Validate topic
    if not topic or not isinstance(topic, str):
        topic = "Artificial Intelligence"  # Fallback to default
    topic = topic.strip()
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # Initialize progress tracking
    total_articles = len(articles)
    if streamlit_mode:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Process articles in batches to respect rate limits
    filtered_articles = []
    batch_size = 5
    for i in range(0, total_articles, batch_size):
        batch = articles[i:i+batch_size]
        
        # Update progress
        progress = (i + 1) / total_articles
        if streamlit_mode:
            progress_bar.progress(progress)
            status_text.text(f"Processing articles {i+1}-{min(i+batch_size, total_articles)} of {total_articles}")
        else:
            print(f"Processing articles {i+1}-{min(i+batch_size, total_articles)} of {total_articles}")
        
        prompt = f"""You are a professional news analyst.

                    You will receive a list of articles. For each article, answer ONLY "yes" if it is clearly related to the topic "{topic}", otherwise answer "no".

                    Follow this strict format:
                    1. yes/no
                    2. yes/no
                    3. yes/no
                    4. yes/no
                    5. yes/no

                    Important:
                    - Do not explain.
                    - Do not repeat the articles.
                    - Only output the numbered answers exactly as shown.
"""

        batch_content = "\n\n".join(
            f"Article {idx+1}:\nTitle: {a.get('title', '')}\nContent: {a.get('content', '')}" 
            for idx, a in enumerate(batch)
        )

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                temperature=0.2,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": batch_content}
                ]
            )
            
            replies = response.choices[0].message.content.strip().lower()
            matches = re.findall(r"\d+\s*[:.]\s*(yes|no)", replies)
            
            for idx, (article, decision) in enumerate(zip(batch, matches)):
                if decision == "yes":
                    article_message = f"Article accepted: {article.get('title', '')[:40]}..."
                    if streamlit_mode:
                        log_to_streamlit(article_message)
                    filtered_articles.append(article)
                elif streamlit_mode:
                    article_message = f"Article rejected: {article.get('title', '')[:40]}..."
                    log_to_streamlit(article_message)

        except Exception as e:
            error_message = f"Error during batch processing: {e}"
            if streamlit_mode:
                log_to_streamlit(error_message)
            else:
                logger.error(error_message)

    summary_message = f"Filtering complete: {len(filtered_articles)}/{total_articles} articles match the topic '{topic}'"
    if streamlit_mode:
        log_to_streamlit(summary_message)
    else:
        logger.info(summary_message)
        
    # Save filtered articles with dynamic filename
    output_file = get_filtered_filename(topic)
    save_json(filtered_articles, output_file)
    return filtered_articles

def main():
    parser = argparse.ArgumentParser(description="Filter articles by topic using OpenAI")
    parser.add_argument('topic', type=str, help='Topic to filter for')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    input_file = "output/articles.json"
    output_file = get_filtered_filename(args.topic)

    articles = load_json(input_file)
    logger.info(f"Loaded {len(articles)} articles from {input_file}")

    filtered = filter_articles(articles, topic=args.topic, streamlit_mode=True)

    logger.info(f"Found {len(filtered)} articles related to '{args.topic}'")
    logger.info(f"Filtered articles saved to {output_file}")

if __name__ == "__main__":
    main()
