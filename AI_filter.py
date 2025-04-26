import os
import json
from openai import OpenAI
import re
import argparse

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

def filter_articles(articles, topic="Artificial Intelligence", batch_size=5, model="gpt-4.1-mini"):
    filtered = []
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]

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

            for article, decision in zip(batch, matches):
                if decision == "yes":
                    filtered.append(article)

        except Exception as e:
            print(f"Error during batch processing: {e}")

    return filtered

def main():
    parser = argparse.ArgumentParser(description="Filter articles by topic using OpenAI")
    parser.add_argument('topic', type=str, help='Topic to filter for')
    args = parser.parse_args()

    input_file = "output/articles.json"
    output_file = f"filtered_{args.topic.replace(' ', '_').lower()}.json"

    articles = load_json(input_file)
    print(f"Loaded {len(articles)} articles")

    filtered = filter_articles(articles, topic=args.topic)

    print(f"Found {len(filtered)} articles related to '{args.topic}'")
    save_json(filtered, output_file)
    print(f"Filtered articles saved to {output_file}")

if __name__ == "__main__":
    main()
