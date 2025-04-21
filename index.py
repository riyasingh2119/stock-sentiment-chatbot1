from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import re
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from flask_cors import CORS
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
import yfinance.utils
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


yfinance.utils._requests_kwargs = {'verify': False}

load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)



NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def extract_stock_name(query):
    """
    Extract stock names from different query formats and ensures correct capitalization 
    based on Yahoo Finance data.
    """
    query = query.strip()

    patterns = [
        r'^sentiment\s+analysis\s+of\s+([\w\s&]+)\??$',    
        r'^analyze\s+sentiment\s+for\s+([\w\s&]+)\??$',    
        r'^what\s+is\s+the\s+sentiment\s+of\s+([\w\s&]+)\??$',  
        r'^sentiment\s+check\s+for\s+([\w\s&]+)\??$',      
        r'^([\w\s&]+)\s+sentiment\??$',                   
        r'^([\w\s&]+)\s+sentiment\s+analysis\??$',        
        r'^what\s+is\s+([\w\s&]+)\s+sentiment\??$',       
        r'^find\s+the\s+sentiment\s+for\s+([\w\s&]+)\??$', 
        r'^how\s+is\s+the\s+sentiment\s+of\s+([\w\s&]+)\??$',  
        r'^([\w\s&]+):\s+what\'?s?\s+the\s+sentiment\??$',  
        r'^can\s+you\s+analyze\s+sentiment\s+for\s+([\w\s&]+)\??$',
        r'^analyse\s+([\w\s&]+)\??$',
        r'^give\s+me\s+the\s+sentiment\s+for\s+([\w\s&]+)\??$',  
        r'^([\w\s&]+)\s+stock\s+sentiment\??$',                 
        r'^tell\s+me\s+the\s+sentiment\s+of\s+([\w\s&]+)\??$',  
        r'^([\w\s&]+)\s+sentiment\s+check\??$',                 
        r'^i\s+want\s+to\s+know\s+([\w\s&]+)\s+sentiment\??$',  
        r'^how\s+positive\s+is\s+([\w\s&]+)\s+right\s+now\??$', 
        r'^([\w\s&]+)\s+news\s+sentiment\??$',                  
        r'^([\w\s&]+)\s+twitter\s+sentiment\??$',               
        r'^analyze\s+([\w\s&]+)\s+news\??$',                    
        r'^check\s+([\w\s&]+)\s+sentiment\??$',
        r'^can\s+you\s+check\s+the\s+sentiment\s+of\s+([\w\s&]+)\??$',
        r'^check\s+the\s+sentiment\s+for\s+([\w\s&]+)\??$',
        r'^([\w\s&]+)\s+market\s+sentiment\??$',
        r'^([\w\s&]+)\s+public\s+opinion\??$',
        r'^([\w\s&]+)\s+analysis\??$',  
        r'^what\'?s?\s+the\s+current\s+sentiment\s+on\s+([\w\s&]+)\??$',
        r'^current\s+sentiment\s+of\s+([\w\s&]+)\??$',
        r'^how\s+are\s+people\s+feeling\s+about\s+([\w\s&]+)\??$',
        r'^do\s+you\s+have\s+sentiment\s+data\s+for\s+([\w\s&]+)\??$',
        r'^give\s+me\s+a\s+sentiment\s+report\s+on\s+([\w\s&]+)\??$',
        r'^([\w\s&]+)\s+investor\s+sentiment\??$',
        r'^([\w\s&]+)\s+community\s+sentiment\??$',
        r'^news\s+about\s+([\w\s&]+)\s+sentiment\??$',
        r'^([\w\s&]+)\s+discussion\s+sentiment\??$',
        r'^analyze\s+([\w\s&]+)\s+emotion\??$',
        r'^([\w\s&]+)\s+current\s+vibe\??$',  
        r'^social\s+media\s+sentiment\s+for\s+([\w\s&]+)\??$',
        r'^public\s+reaction\s+to\s+([\w\s&]+)\??$',
        r'^what\s+do\s+the\s+headlines\s+say\s+about\s+([\w\s&]+)\??$',
        r'^can\s+you\s+tell\s+me\s+how\s+([\w\s&]+)\s+is\s+doing\??$',
        r'^sentiment\s+([\w\s&]+)\??$'
          
    ]

    for pattern in patterns:
        match = re.match(pattern, query, re.IGNORECASE)
        if match:
            stock_name = match.group(1).strip()
            return stock_name 

    return None

def fetch_finanicial_info(query):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def get_ticker_from_company_name(company_name):
    query = company_name.replace(" ", "+")
    data = fetch_finanicial_info(query)
    if "quotes" in data and data["quotes"]:
        return data["quotes"][0].get("symbol")
    return None

def get_exact_name_from_company_name(company_name):
    query = company_name.replace(" ", "+")
    data = fetch_finanicial_info(query)
    if "quotes" in data and data["quotes"]:
        return data["quotes"][0].get("shortname")
    return company_name.title()

def fetch_stock_news(stock_name):
    """Fetch top 5 news headlines related to the stock."""
    url = f"https://newsapi.org/v2/everything?q={stock_name}&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url).json()
    articles = response.get("articles", [])[:5]
    return [article["title"] for article in articles]

def fetch_reddit_posts(stock_name):
    """Fetch top 5 Reddit posts related to the stock using Reddit's public JSON endpoint."""
    url = f"https://www.reddit.com/search.json?q={stock_name}&limit=5"
    headers = {'User-agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers,verify=False).json()
    posts = []
    for child in response.get("data", {}).get("children", []):
        data = child.get("data", {})
        title = data.get("title", "")
        selftext = data.get("selftext", "")
        posts.append(title + " " + selftext)
    return posts

def analyze_sentiment(text_list):
    """Analyze sentiment for a list of texts using VADER."""
    analyzer = SentimentIntensityAnalyzer()
    sentiments = [analyzer.polarity_scores(text)["compound"] for text in text_list if text]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    if avg_sentiment > 0.05:
        return "Positive 😊"
    elif avg_sentiment < -0.05:
        return "Negative 😞"
    else:
        return "Neutral 😐"

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'chatbotUI.html')


@app.route("/chatbot", methods=["GET"])
def chatbot_response():
    query = request.args.get("query", "").strip().lower()
    extracted = extract_stock_name(query)
    if not extracted:
        return jsonify({"reply": "I can analyze stock sentiment from news and social media. Try asking: 'What is the sentiment of TCS?'"})
    ticker = get_ticker_from_company_name(extracted)
    display_stock = get_exact_name_from_company_name(extracted)
    if not ticker:
        return jsonify({"reply": f"Sorry, I couldn't find valid stock data for **{display_stock}**."})
    
    
    
    y_ticker = yf.Ticker(ticker)
    currency = y_ticker.info.get('currency')
    amount = y_ticker.info['regularMarketPrice']


    news_list = fetch_stock_news(ticker)
    reddit_posts = fetch_reddit_posts(ticker)
    combined_texts = news_list + reddit_posts
    sentiment = analyze_sentiment(combined_texts)

    return jsonify({"reply": f"The overall sentiment for {display_stock} is {sentiment}.Current Stock Price : {currency} {amount}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


# curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36" "https://query1.finance.yahoo.com/v1/finance/search?q=tata+motor"

# Add this line for Vercel to use the app
def handler(environ, start_response):
    return app(environ, start_response)





