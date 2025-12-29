import os
import requests
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Your Serper API Key
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

class DirectorScanner:
    def __init__(self, product, location):
        self.product = product
        self.location = location
        self.leads = []
        self.headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    def scan_source(self, platform_query, source_name):
        """Generic scanner for different platforms via Serper"""
        url = "https://google.serper.dev/search"
        # We go 5 pages deep for each specific platform
        for page in range(1, 6):
            payload = {"q": platform_query, "num": 20, "page": page}
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=15)
                data = response.json()
                for item in data.get('organic', []):
                    snippet = item.get('snippet', '')
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                    phones = re.findall(r'\+?\d[\d\-\s\(\)]{9,}\d', snippet)
                    
                    if emails:
                        for email in set(emails):
                            if not any(x in email.lower() for x in ['png', 'jpg', 'wix']):
                                self.leads.append({
                                    "Company": item.get('title', 'Business'),
                                    "Email": email.lower(),
                                    "Phone": phones[0] if phones else "N/A",
                                    "Source_URL": item.get('link', '#'),
                                    "Director": source_name
                                })
            except:
                break

    def run_full_scan(self):
        # 1. SCAN GOOGLE (General)
        self.scan_source(f'"{self.product}" "{self.location}" email', "Google Search")
        
        # 2. SCAN BING (Via Serper search footprint)
        self.scan_source(f'site:bing.com "{self.product}" "{self.location}" email', "Bing Indexed")
        
        # 3. SCAN YELLOW PAGES
        self.scan_source(f'site:yellowpages.com "{self.product}" "{self.location}"', "Yellow Pages")
        
        # 4. SCAN THOMASNET
        self.scan_source(f'site:thomasnet.com "{self.product}" "{self.location}"', "ThomasNet")
        
        # 5. SCAN FACEBOOK/LINKEDIN (Directories of businesses)
        self.scan_source(f'site:facebook.com "{self.product}" "{self.location}" email', "Facebook Business")
        self.scan_source(f'site:linkedin.com/company "{self.product}" "{self.location}"', "LinkedIn Directory")

        # Deduplicate
        unique = {v['Email']: v for v in self.leads}.values()
        return list(unique)

# --- UI WITH SOURCE TRACKING ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Director Lead Engine</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1400px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 5px 25px rgba(0,0,0,0.1); }
        .search-form { display: grid; grid-template-columns: 1fr 1fr auto; gap: 15px; margin-bottom: 30px; }
        input { padding: 15px; border: 1px solid #ccc; border-radius: 8px; }
        button { background: #1a73e8; color: white; border: none; padding: 15px 40px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .counter-badge { background: #34495e; color: white; padding: 8px 16px; border-radius: 5px; margin-bottom: 10px; display: inline-block; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { background: #f8f9fa; padding: 12px; border-bottom: 2px solid #dee2e6; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #eee; }
        .source-tag { background: #e8f5e9; color: #2e7d32; padding: 3px 7px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .pagination { margin-top: 20px; text-align: center; }
        .p-btn { padding: 10px 20px; border: 1px solid #1a73e8; color: #1a73e8; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🌍 Multi-Director Lead Engine <small>V2025.12</small></h2>
        <form class="search-form" action="/search" method="get">
            <input type="hidden" name="page" value="1">
            <input type="text" name="product" placeholder="Product/Service" required>
            <input type="text" name="location" placeholder="Location" required>
            <button type="submit">Scan All Directors</button>
        </form>

        {% if results %}
        <div class="counter-badge">Total Unique Leads Found: {{ total_count }}</div>
        <table>
            <thead>
                <tr>
                    <th>Business Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Director Source</th>
                    <th>Original URL</th>
                </tr>
            </thead>
            <tbody>
                {% for item in results %}
                <tr>
                    <td><strong>{{ item.Company[:50] }}</strong></td>
                    <td style="color:#d35400; font-weight:bold;">{{ item.Email }}</td>
                    <td>{{ item.Phone }}</td>
                    <td><span class="source-tag">{{ item.Director }}</span></td>
                    <td><a href="{{ item.Source_URL }}" target="_blank" style="color:#3498db; font-size:11px;">View Link</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="pagination">
            {% if current_page > 1 %}
            <a href="/search?product={{ p }}&location={{ l }}&page={{ current_page - 1 }}" class="p-btn">Prev Page</a>
            {% endif %}
            <a href="/search?product={{ p }}&location={{ l }}&page={{ current_page + 1 }}" class="p-btn">Next Page</a>
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
    page_num = int(request.args.get('page', 1))
    
    scanner = DirectorScanner(p, l)
    data = scanner.run_full_scan()
    
    # Paginate by 100
    per_page = 100
    start = (page_num - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]

    return render_template_string(
        HTML_TEMPLATE, 
        results=paginated_data, 
        total_count=len(data),
        p=p, l=l, current_page=page_num
    )
