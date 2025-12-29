from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def extract_leads(product, location):
    # UPGRADE: Real Browser Headers to avoid empty results
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    # We add 'num=20' to get more results at once
    query = f"{product} {location} dealers email"
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=20"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        # If Google blocks us, we will see it here
        if response.status_code != 200:
            return [{"url": f"Blocked by Google (Code {response.status_code})", "email": "Try again in 5 mins"}]
            
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # UPGRADE: Search in 'div.g' (Organic results) and 'div.VwiC3b' (Snippets)
        for g in soup.find_all('div', class_='g'):
            link_tag = g.find('a', href=True)
            url = link_tag['href'] if link_tag else "No Link"
            
            # Find emails anywhere in the text of this result block
            text_content = g.get_text()
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
            
            if emails:
                # We only add it if an email was actually found
                for email in set(emails):
                    results.append({"url": url, "email": email})
        
        if not results:
            return [{"url": "No emails found in snippets", "email": "Try a more specific product"}]
            
        return results
    except Exception as e:
        return [{"url": "System Error", "email": str(e)}]

# --- UI TEMPLATE (Unchanged) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor Pro</title>
    <style>
        body { font-family: sans-serif; padding: 50px; background: #f4f4f9; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }
        input { padding: 12px; margin: 5px; width: 250px; border: 1px solid #ddd; border-radius: 6px; }
        button { padding: 12px 25px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #218838; }
        table { width: 100%; margin-top: 30px; border-collapse: collapse; background: white; }
        th, td { padding: 15px; border-bottom: 1px solid #eee; text-align: left; }
        th { background: #f8f9fa; color: #333; }
        .status { color: #666; font-size: 0.9em; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔍 Institutional Lead Extractor</h2>
        <p class="status">Enter product and location to find public business emails.</p>
        <form action="/search" method="get">
            <input type="text" name="product" placeholder="e.g. Solar Panels" required>
            <input type="text" name="location" placeholder="e.g. Accra" required>
            <button type="submit">Extract Leads</button>
        </form>
        {% if results %}
        <table>
            <thead><tr><th>Website / Source</th><th>Email Found</th></tr></thead>
            <tbody>
            {% for item in results %}
            <tr>
                <td><small>{{ item.url[:60] }}...</small></td>
                <td><strong>{{ item.email }}</strong></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    p = request.args.get('product', '')
    l = request.args.get('location', '')
    data = extract_leads(p, l)
    return render_template_string(HTML_TEMPLATE, results=data)
