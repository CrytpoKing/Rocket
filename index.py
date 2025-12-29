import os
import requests
import re
import time
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Your Serper API Key
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

def serper_volume_engine(product, location):
    url = "https://google.serper.dev/search"
    all_leads = []
    
    # We vary the search terms to find DIFFERENT results in each loop
    # This helps bypass Google's limit on a single query
    search_variations = [
        f'"{product}" "{location}" email',
        f'"{product}" "{location}" contact @gmail.com',
        f'"{product}" "{location}" sales @outlook.com',
        f'site:yellowpages.com "{product}" "{location}"',
        f'site:facebook.com "{product}" "{location}" "about"',
        f'site:linkedin.com/company "{product}" "{location}"'
    ]
    
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    # Loop through variations and pages to hit the 200 goal
    for query in search_variations:
        # Check 3 pages for each variation (total ~60 results per variation)
        for page in range(1, 4): 
            payload = {
                "q": query,
                "num": 20,
                "page": page
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                data = response.json()
                
                for item in data.get('organic', []):
                    snippet = item.get('snippet', '')
                    title = item.get('title', 'Business')
                    link = item.get('link', '#')
                    
                    # Search snippet for emails
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                    
                    if emails:
                        for email in set(emails):
                            if not any(x in email.lower() for x in ['png', 'jpg', 'wix', 'sentry']):
                                all_leads.append({
                                    "Company": title,
                                    "Email": email.lower(),
                                    "Link": link
                                })
                
                # If we already have enough, we can stop early to save API credits
                if len(all_leads) >= 250:
                    break
            except:
                continue
    
    # Final cleanup: Remove duplicates based on the Email address
    unique_leads = {}
    for lead in all_leads:
        unique_leads[lead['Email']] = lead
        
    return list(unique_leads.values())

# --- UI WITH RESULT COUNT ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor Ultra</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f8f9fa; padding: 20px; }
        .container { max-width: 1100px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .stats-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 10px; background: #eef2f7; border-radius: 8px; }
        .search-form { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        button { background: #1a73e8; color: white; border: none; padding: 15px 30px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; }
        .count-badge { background: #28a745; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9em; }
        .email-link { color: #1a73e8; font-weight: 600; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Institutional Lead Extractor <small>(High Volume)</small></h2>
        
        <form class="search-form" action="/search" method="get">
            <input type="text" name="product" placeholder="Product/Brand" required>
            <input type="text" name="location" placeholder="City/Country" required>
            <button type="submit">Extract 200+ Leads</button>
        </form>

        {% if results %}
        <div class="stats-bar">
            <span><strong>Results for:</strong> {{ query_info }}</span>
            <span class="count-badge">Found {{ results|length }} Unique Leads</span>
        </div>
        
        <table>
            <thead>
                <tr><th>Business Name</th><th>Email</th><th>Source</th></tr>
            </thead>
            <tbody>
                {% for item in results %}
                <tr>
                    <td>{{ item.Company[:50] }}</td>
                    <td><a href="mailto:{{ item.Email }}" class="email-link">{{ item.Email }}</a></td>
                    <td><a href="{{ item.Link }}" target="_blank" style="font-size: 0.8em; color: #999;">View Source</a></td>
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
    data = serper_volume_engine(p, l)
    return render_template_string(HTML_TEMPLATE, results=data, query_info=f"{p} in {l}")
