import json
from kafka import KafkaProducer
import requests
import time

# News API key
news_api_key = "b2e62f4d3bb24b2fb5bf6d4cceecf71b"

# Kafka broker configuration
bootstrap_servers = 'localhost:9092'

# Function to fetch news articles from News API
def fetch_news(api_key):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('articles', [])
    else:
        print("Failure in fetching news:", response.text)
        return []

def main():
    # Initializing kafka producer
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    while True:
        # Fetching news articles
        news_articles = fetch_news(news_api_key)

        # Pushing news articles to the Kafka topic1
        for article in news_articles:
            print(article)
            producer.send("topic1", json.dumps(article).encode('utf-8'))

        # Keeping time gap of 300 secs before fetching new article
        time.sleep(300)

if __name__ == "__main__":
    main()

