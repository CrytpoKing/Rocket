from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# --- THE SCRAPER LOGIC ---
def extract_leads(product, location):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    search_url = f"https://www.google.com/search?q={product}+{location}+dealers+email"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Simple extraction of snippets and links
        for g in soup.find_all('div', class_='g'):
            link = g.find('a')['href'] if g.find('a') else "No Link"
            text = g.get_text()
            
            # Find emails in the text snippet
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            
            results.append({
                "url": link,
                "email": emails[0] if emails else "Contact via site"
            })
        return results
    except Exception as e:
        return [{"url": "Error", "email": str(e)}]

# --- THE DASHBOARD (HTML) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor Pro</title>
    <style>
        body { font-family: sans-serif; padding: 50px; background: #f4f4f9; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        input { padding: 10px; margin: 5px; width: 200px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        table { width: 100%; margin-top: 20px; border-collapse: collapse; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 Lead Extractor</h2>
        <form action="/search" method="get">
            <input type="text" name="product" placeholder="Product (e.g. BMW)" required>
            <input type="text" name="location" placeholder="Location (e.g. Accra)" required>
            <button type="submit">Extract Leads</button>
        </form>
        {% if results %}
        <table>
            <tr><th>Company / URL</th><th>Email Address</th></tr>
            {% for item in results %}
            <tr><td>{{ item.url }}</td><td>{{ item.email }}</td></tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    p = request.args.get('product')
    l = request.args.get('location')
    data = extract_leads(p, l)
    return render_template_string(HTML_TEMPLATE, results=data)

# Required for Vercel
def handler(event, context):
    return app(event, context)
