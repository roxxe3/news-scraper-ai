import os
import json
from openai import OpenAI
import re
import argparse
import time
from helpers import logger, log_to_streamlit

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

openai_client = OpenAI(api_key=openai_api_key)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def filter_articles(articles, topic="Artificial Intelligence", batch_size=5, model="gpt-4.1-mini", verbose=False, streamlit_mode=False):
    filtered = []
    
    message = f"Starting to filter {len(articles)} articles for topic: '{topic}'"
    if streamlit_mode:
        log_to_streamlit(message)
    else:
        logger.info(message)
    
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        batch_message = f"Processing batch {i//batch_size + 1}/{(len(articles)-1)//batch_size + 1} ({len(batch)} articles)"
        
        if streamlit_mode:
            log_to_streamlit(batch_message)
        elif verbose:
            logger.info(batch_message)

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
                model=model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": batch_content}
                ]
            )
            replies = response.choices[0].message.content.strip().lower()
            matches = re.findall(r"\d+\s*[:.]\s*(yes|no)", replies)
            
            if verbose or streamlit_mode:
                response_message = f"AI responses for batch: {matches}"
                if streamlit_mode:
                    log_to_streamlit(response_message)
                else:
                    logger.debug(response_message)

            for idx, (article, decision) in enumerate(zip(batch, matches)):
                if decision == "yes":
                    article_message = f"Article accepted: {article.get('title', '')[:40]}..."
                    if streamlit_mode:
                        log_to_streamlit(article_message)
                    elif verbose:
                        logger.info(article_message)
                    filtered.append(article)
                elif verbose or streamlit_mode:
                    article_message = f"Article rejected: {article.get('title', '')[:40]}..."
                    if streamlit_mode:
                        log_to_streamlit(article_message)
                    else:
                        logger.debug(article_message)

        except Exception as e:
            error_message = f"Error during batch processing: {e}"
            if streamlit_mode:
                log_to_streamlit(error_message)
            else:
                logger.error(error_message)

        # Wait 21 seconds to stay under 3 requests per minute
        if i + batch_size < len(articles):
            wait_message = f"Waiting 21 seconds for API rate limit..."
            if streamlit_mode:
                log_to_streamlit(wait_message)
            elif verbose:
                logger.info(wait_message)
            time.sleep(21)

    summary_message = f"Filtering complete: {len(filtered)}/{len(articles)} articles match the topic '{topic}'"
    if streamlit_mode:
        log_to_streamlit(summary_message)
    else:
        logger.info(summary_message)
        
    return filtered

def main():
    parser = argparse.ArgumentParser(description="Filter articles by topic using OpenAI")
    parser.add_argument('topic', type=str, help='Topic to filter for')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    input_file = "output/articles.json"
    output_file = "output/filtered_articles.json"

    articles = load_json(input_file)
    logger.info(f"Loaded {len(articles)} articles from {input_file}")

    filtered = filter_articles(articles, topic=args.topic, verbose=args.verbose)

    logger.info(f"Found {len(filtered)} articles related to '{args.topic}'")
    save_json(filtered, output_file)
    logger.info(f"Filtered articles saved to {output_file}")

if __name__ == "__main__":
    main()
