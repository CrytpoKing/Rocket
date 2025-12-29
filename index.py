from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

app = Flask(__name__)

class LeadEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_leads(self, product, location):
        leads = []
        # Target specific directories via search footprints
        search_queries = [
            f'site:yellowpages.com "{product}" "{location}" email',
            f'site:thomasnet.com "{product}" "{location}"',
            f'site:linkedin.com/company "{product}" "{location}" email',
            f'"{product}" "{location}" "contact us" email'
        ]

        for query in search_queries:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num=30"
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Look for emails and phone numbers in every result block
                    for g in soup.find_all('div', class_='g'):
                        text = g.get_text()
                        
                        # Extract Emails
                        found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
                        # Extract Phone Numbers (International formats)
                        found_phones = re.findall(r'\+?\d[\d\-\s\(\)]{8,}\d', text)

                        if found_emails:
                            for email in set(found_emails):
                                # Clean junk
                                if not any(x in email.lower() for x in ['png', 'jpg', 'sentry', 'wix']):
                                    leads.append({
                                        "Source": "Directory/Search",
                                        "Email": email,
                                        "Phone": found_phones[0] if found_phones else "Check Site"
                                    })
            except:
                continue
        
        # Remove duplicates based on email
        unique_leads = {v['Email']: v for v in leads}.values()
        return list(unique_leads)

# --- UI TEMPLATE (UPGRADED) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Global Lead Engine</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #eee; margin-bottom: 25px; padding-bottom: 10px; }
        .search-area { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }
        button { background: #1a73e8; color: #fff; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; background: #f8f9fa; padding: 12px; border-bottom: 2px solid #dee2e6; }
        td { padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; }
        .badge { background: #e7f4ff; color: #007bff; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h2>🌍 Global Institutional Lead Extractor</h2></div>
        <form class="search-area" action="/search" method="get">
            <input type="text" name="product" placeholder="Product/Dealer (e.g. Caterpillar)" required>
            <input type="text" name="location" placeholder="Location (e.g. Ghana)" required>
            <button type="submit">Extract Leads</button>
        </form>
        {% if results %}
        <table>
            <thead><tr><th>Source</th><th>Email Address</th><th>Phone / Contact</th></tr></thead>
            <tbody>
                {% for item in results %}
                <tr>
                    <td>{{ item.Source }}</td>
                    <td><span class="badge">{{ item.Email }}</span></td>
                    <td>{{ item.Phone }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="color: #666;">No leads found yet. Try broader terms like 'Equipment' instead of specific models.</p>
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
    engine = LeadEngine()
    data = engine.get_leads(p, l)
    return render_template_string(HTML_TEMPLATE, results=data)
