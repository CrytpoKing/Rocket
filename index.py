import os
import requests
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Your Serper API Key
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

def serper_lead_engine(product, location):
    url = "https://google.serper.dev/search"
    
    # UPGRADED FOOTPRINT: Forces Google to find emails on major directories
    # Targets: YellowPages, Thomasnet, LinkedIn, and Facebook
    query = f'"{product}" "{location}" (site:yellowpages.com OR site:thomasnet.com OR site:facebook.com) "email" OR "contact"'
    
    payload = {
        "q": query,
        "num": 30, # Increased results to 30 for better depth
        "autocorrect": True
    }
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        
        leads = []
        # Parse organic results
        for item in data.get('organic', []):
            title = item.get('title', 'Business Name')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            
            # Extract emails using 2025 refined Regex
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
            
            if emails:
                for email in set(emails):
                    # Filter out non-business patterns
                    if not any(x in email.lower() for x in ['example.com', 'sentry', 'wix']):
                        leads.append({
                            "Company": title,
                            "Email": email,
                            "Link": link
                        })
        
        # Sort and remove duplicates
        unique_leads = {v['Email']: v for v in leads}.values()
        return list(unique_leads)
    except Exception as e:
        return [{"Company": "Error", "Email": str(e), "Link": "#"}]

# --- PROFESSIONAL UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Institutional Lead Engine Pro</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 30px; }
        .app-container { max-width: 1000px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #f0f2f5; padding-bottom: 20px; }
        .search-form { display: flex; gap: 15px; margin-bottom: 30px; }
        input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; transition: 0.3s; }
        input:focus { border-color: #007bff; outline: none; box-shadow: 0 0 8px rgba(0,123,255,0.2); }
        button { background: #007bff; color: white; border: none; padding: 15px 30px; border-radius: 10px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #0056b3; transform: translateY(-2px); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { text-align: left; background: #f8f9fa; padding: 15px; color: #555; }
        td { padding: 15px; border-bottom: 1px solid #eee; }
        .email-badge { background: #e7f3ff; color: #007bff; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-family: monospace; }
        .no-data { text-align: center; padding: 40px; color: #777; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1>🚀 Institutional Lead Extractor</h1>
            <p>Scanning Google, YellowPages, and ThomasNet Profiles</p>
        </div>
        
        <form class="search-form" action="/search" method="get">
            <input type="text" name="product" placeholder="Product/Service (e.g. Caterpillar Dealers)" required>
            <input type="text" name="location" placeholder="Location (e.g. Ghana)" required>
            <button type="submit">Start Extraction</button>
        </form>

        {% if results %}
        <table>
            <thead>
                <tr>
                    <th>Company/Source</th>
                    <th>Email Found</th>
                </tr>
            </thead>
            <tbody>
                {% for item in results %}
                <tr>
                    <td><a href="{{ item.Link }}" target="_blank" style="text-decoration:none; color:#333; font-weight:500;">{{ item.Company[:60] }}...</a></td>
                    <td><span class="email-badge">{{ item.Email }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% elif searched %}
        <div class="no-data">
            <p>No contact details found in snippets. Try a broader search term (e.g. "Equipment" instead of "Model 300").</p>
        </div>
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
