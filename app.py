from flask import Flask, request, jsonify
import requests
import urllib.parse
from flask_cors import CORS
from bs4 import BeautifulSoup
import random
import re
from datetime import datetime
import time
import json
import os

app = Flask(__name__)
CORS(app)

SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=firefox&q="
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

KEYWORD_CATEGORIES = {
    "technology": {"min_volume": 1000, "max_volume": 50000, "cpc_range": (1.5, 10.0)},
    "health": {"min_volume": 5000, "max_volume": 100000, "cpc_range": (2.0, 15.0)},
    "business": {"min_volume": 2000, "max_volume": 30000, "cpc_range": (1.0, 8.0)},
    "education": {"min_volume": 1000, "max_volume": 20000, "cpc_range": (0.5, 5.0)},
    "shopping": {"min_volume": 3000, "max_volume": 80000, "cpc_range": (0.8, 12.0)}
}

TREND_PATTERNS = {
    "how to": "Rising",
    "best": "Stable",
    "buy": "Seasonal",
    str(datetime.now().year): "Declining",
    "near me": "Rising",
    "review": "Stable",
    "vs": "Stable",
    "alternatives": "Rising"
}

TRUST_DOMAINS = [".gov", ".edu", ".org", ".com", ".net"]
TOP_REFERENCE_SITES = ["wikipedia.org", "webmd.com", "forbes.com", "nytimes.com", "techcrunch.com"]

CACHE_FILE = "seo_cache.json"
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)

def detect_category(keyword):
    keyword = keyword.lower()
    if any(x in keyword for x in ["how to", "tutorial", "learn", "guide"]):
        return "education"
    elif any(x in keyword for x in ["buy", "price", "shop", "deal", "discount"]):
        return "shopping"
    elif any(x in keyword for x in ["disease", "symptoms", "doctor", "medical", "health"]):
        return "health"
    elif any(x in keyword for x in ["business", "startup", "marketing", "entrepreneur"]):
        return "business"
    else:
        return "technology"

def detect_tail_length(keyword):
    count = len(keyword.strip().split())
    if count == 1: return "Short-tail"
    elif 2 <= count <= 3: return "Mid-tail"
    else: return "Long-tail"

def analyze_serp(keyword):
    try:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&gl=us&hl=en"
        response = requests.get(search_url, headers=HEADERS, timeout=10)

        if "detected unusual traffic" in response.text:
            return {
                "error": "Google detected automated requests. Please try again later.",
                "status": "blocked"
            }

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select("div.g")[:10]
        competitors = len(results)
        title_match_count = 0
        domains = set()
        meta_descriptions = []
        h_tags = {"h1": [], "h2": [], "h3": [], "h4": []}

        for r in results:
            title_tag = r.find("h3")
            if title_tag and keyword.lower() in title_tag.text.lower():
                title_match_count += 1
            cite = r.find("cite")
            if cite:
                domain = cite.text.split("/")[0].replace("www.", "")
                domains.add(domain)
            desc = r.select_one("div[data-sncf]") or r.find("span")
            if desc:
                meta_descriptions.append(desc.text.strip())

        for tag in h_tags:
            for h in soup.find_all(tag):
                h_tags[tag].append(h.text.strip())

        trust_score = sum([1 for d in domains if any(t in d for t in TRUST_DOMAINS)])

        return {
            "competitors": competitors,
            "title_match_count": title_match_count,
            "top_domains": list(domains)[:5],
            "trust_score": trust_score,
            "meta_data": {
                "meta_description": meta_descriptions[:3],
                **{t: h_tags[t][:3] for t in h_tags}
            }
        }
    except Exception as e:
        return {
            "competitors": 0,
            "title_match_count": 0,
            "top_domains": [],
            "trust_score": 0,
            "meta_data": {"meta_description": [], "h1": [], "h2": [], "h3": [], "h4": []},
            "error": str(e)
        }

def generate_realistic_seo_data(keyword):
    if keyword in cache:
        return cache[keyword]

    random.seed(keyword)
    category = detect_category(keyword)
    category_data = KEYWORD_CATEGORIES[category]

    trend = "Stable"
    for pattern, val in TREND_PATTERNS.items():
        if pattern in keyword.lower():
            trend = val
            break

    word_count = len(keyword.split())
    base_volume = category_data["min_volume"] + (category_data["max_volume"] - category_data["min_volume"]) // max(1, int(word_count * 0.8))
    search_volume = int(base_volume * 0.9)

    cpc = round(sum(bytearray(keyword.encode())) % 100 / 10, 2)
    difficulty = int(20 + (search_volume / 2000) + (sum(bytearray(keyword.encode())) % 30))
    opportunity_score = max(10, 100 - difficulty + (search_volume // 1000))

    serp = analyze_serp(keyword)

    data = {
        'keyword': keyword,
        'search_volume': search_volume,
        'competition': random.choices(['Low', 'Medium', 'High'], weights=[0.3, 0.5, 0.2])[0],
        'competition_index': int(search_volume / 1000 + random.randint(10, 40)),
        'cpc': cpc,
        'trend': trend,
        'difficulty': difficulty,
        'potential_traffic': int(search_volume * 0.2),
        'parent_topic': keyword.split()[0] if ' ' in keyword else '',
        'category': category,
        'opportunity_score': opportunity_score,
        'tail_type': detect_tail_length(keyword),
        'serp_analysis': serp
    }

    cache[keyword] = data
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    return data

def generate_related_keywords(keyword):
    words = keyword.split()
    if len(words) > 1:
        base = words[0]
        return [f"{base} best", f"{base} how to", f"{base} review"]
    return []

@app.route('/seo', methods=['GET'])
def get_keywords():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        response = requests.get(SUGGEST_URL + urllib.parse.quote(query))
        suggestions = response.json()[1][:10]

        primary_data = []
        for kw in suggestions:
            data = generate_realistic_seo_data(kw)
            primary_data.append(data)
            time.sleep(0.5)

        total_volume = sum(d['search_volume'] for d in primary_data)
        avg_difficulty = sum(d['difficulty'] for d in primary_data) / len(primary_data)

        return jsonify({
            "query": query,
            "primary_keywords": primary_data,
            "related_keywords": [],
            "summary": {
                "total_keywords": len(primary_data),
                "average_search_volume": int(total_volume / len(primary_data)),
                "average_difficulty": round(avg_difficulty, 1),
                "recommendation": "Good opportunity" if avg_difficulty < 50 else "Competitive",
                "best_keyword": max(primary_data, key=lambda x: x['opportunity_score'])
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
