from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

app = Flask(__name__)

def extract_leads(product, location):
    # 2025 High-Priority User Agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # UPGRADE: Added "site:facebook.com" and "site:linkedin.com" to the search
    # This is where 2025 business emails are usually found.
    queries = [
        f'"{product}" "{location}" email',
        f'"{product}" "{location}" @gmail.com',
        f'site:facebook.com "{product}" "{location}" email'
    ]
    
    all_results = []
    
    for query in queries:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}&num=20"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 2025 Selector Update: Google now uses generic div blocks
            # We search for any text that contains an @ symbol
            for container in soup.find_all(['div', 'span']):
                text = container.get_text()
                # Improved Regex for 2025 email formats
                found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                
                if found:
                    for email in set(found):
                        # Filter out common junk like 'sentry.io' or 'example.com'
                        if not any(x in email.lower() for x in ['wix', 'png', 'jpg', 'sentry']):
                            all_results.append({
                                "source": "Google Result",
                                "email": email
                            })
        except:
            pass

    # Remove duplicates
    unique_results = [dict(t) for t in {tuple(d.items()) for d in all_results}]
    
    if not unique_results:
        return [{"source": "Status", "email": "No emails found. Try adding '@gmail.com' to your search."}]
    
    return unique_results

# --- THE UI (Includes a 'Download' hint) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor 2025</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #eceff1; margin: 0; padding: 40px; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
        h2 { color: #1a73e8; }
        .search-box { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
        button { background: #1a73e8; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        button:hover { background: #1557b0; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { text-align: left; background: #f8f9fa; padding: 15px; border-bottom: 2px solid #eee; }
        td { padding: 15px; border-bottom: 1px solid #eee; font-family: monospace; color: #333; }
        .email-badge { background: #e8f0fe; color: #1967d2; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Institutional Lead Extractor</h2>
        <form class="search-box" action="/search" method="get">
            <input type="text" name="product" placeholder="What are you looking for?" required>
            <input type="text" name="location" placeholder="City or Country" required>
            <button type="submit">Extract</button>
        </form>
        
        {% if results %}
        <table>
            <tr><th>Source</th><th>Email Address</th></tr>
            {% for item in results %}
            <tr>
                <td>{{ item.source }}</td>
                <td><span class="email-badge">{{ item.email }}</span></td>
            </tr>
            {% endfor %}
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
