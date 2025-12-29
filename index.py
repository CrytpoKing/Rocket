import os
import requests
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Your Serper API Key
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

def serper_lead_engine(product, location):
    url = "https://google.serper.dev/search"
    
    # UPGRADE: We run TWO different searches to maximize results
    # 1. Broad directory search
    # 2. Direct @gmail/@outlook search (very common for local dealers)
    queries = [
        f'"{product}" "{location}" email',
        f'"{product}" "{location}" "@gmail.com" OR "@outlook.com"',
        f'site:facebook.com "{product}" "{location}" email'
    ]
    
    all_leads = []
    
    for q in queries:
        payload = {"q": q, "num": 20}
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()
            
            for item in data.get('organic', []):
                snippet = item.get('snippet', '')
                # Refined Regex to catch emails even with spaces or weird formatting
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                
                if emails:
                    for email in set(emails):
                        if not any(x in email.lower() for x in ['png', 'jpg', 'wix', 'sentry']):
                            all_leads.append({
                                "Company": item.get('title', 'Business'),
                                "Email": email,
                                "Link": item.get('link', '#')
                            })
        except:
            continue

    # Remove duplicates
    unique_leads = {v['Email'].lower(): v for v in all_leads}.values()
    return list(unique_leads)

# --- CLEAN UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor Pro</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; padding: 40px; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .search-row { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; border: none; padding: 12px 25px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 15px; border-bottom: 1px solid #eee; }
        .email { background: #e7f3ff; color: #007bff; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Institutional Lead Extractor</h2>
        <form class="search-row" action="/search" method="get">
            <input type="text" name="product" placeholder="Product (e.g. Generators)" required>
            <input type="text" name="location" placeholder="Location (e.g. Accra)" required>
            <button type="submit">Extract Leads</button>
        </form>
        {% if results %}
        <table>
            <tr><th>Company</th><th>Email Address</th></tr>
            {% for item in results %}
            <tr>
                <td><a href="{{ item.Link }}" target="_blank" style="text-decoration:none; color:inherit;">{{ item.Company[:50] }}</a></td>
                <td><span class="email">{{ item.Email }}</span></td>
            </tr>
            {% endfor %}
        </table>
        {% elif searched %}
        <p>Still no results? Try searching for just the product and city (e.g. "Solar Accra") without extra keywords.</p>
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
    data = serper_lead_engine(p, l)
    return render_template_string(HTML_TEMPLATE, results=data, searched=True)
