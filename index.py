import os
import requests
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Your Serper API Key
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

def volume_extractor(product, location):
    url = "https://google.serper.dev/search"
    all_leads = []
    
    # Diverse search variations to hit different databases
    search_variations = [
        f'"{product}" "{location}" email OR "contact"',
        f'"{product}" "{location}" @gmail.com',
        f'site:yellowpages.com "{product}" "{location}"',
        f'site:thomasnet.com "{product}" "{location}"',
        f'site:facebook.com "{product}" "{location}" "contact"'
    ]
    
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    for query in search_variations:
        # Check multiple pages for each variation to build volume
        for page in range(1, 5): 
            payload = {"q": query, "num": 20, "page": page}
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                data = response.json()
                
                for item in data.get('organic', []):
                    snippet = item.get('snippet', '')
                    title = item.get('title', 'Business')
                    
                    # 1. Extract Emails
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                    
                    # 2. Extract Phone Numbers (Looking for common international/local patterns)
                    # This regex looks for +xxx, (xxx), or simple digit strings common in business
                    phones = re.findall(r'\+?\d[\d\-\s\(\)]{8,}\d', snippet)
                    
                    if emails:
                        for email in set(emails):
                            if not any(x in email.lower() for x in ['png', 'jpg', 'wix']):
                                all_leads.append({
                                    "Company": title,
                                    "Email": email.lower(),
                                    "Phone": phones[0] if phones else "Request on Site",
                                    "Link": item.get('link', '#')
                                })
                if len(all_leads) >= 300: break # Safety cap
            except:
                continue
                
    # Deduplicate by Email
    unique_leads = {v['Email']: v for v in all_leads}.values()
    return list(unique_leads)

# --- UI WITH PAGINATION & PHONE NUMBERS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Institutional Lead Engine 2025</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; padding: 30px; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .search-form { display: flex; gap: 10px; margin-bottom: 25px; }
        input { flex: 1; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
        button { background: #007bff; color: white; border: none; padding: 15px 30px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .stats { background: #eef2f7; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; }
        .badge-email { background: #e1f5fe; color: #0288d1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
        .badge-phone { background: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
        .pagination { margin-top: 20px; text-align: center; }
        .page-link { padding: 8px 16px; margin: 0 4px; border: 1px solid #007bff; color: #007bff; text-decoration: none; border-radius: 4px; }
        .page-link.active { background: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 High-Volume Lead Extractor</h2>
        <form class="search-form" action="/search" method="get">
            <input type="hidden" name="page" value="1">
            <input type="text" name="product" placeholder="Product/Service" required>
            <input type="text" name="location" placeholder="Location" required>
            <button type="submit">Extract Leads</button>
        </form>

        {% if results %}
        <div class="stats">
            <span><strong>Query:</strong> {{ query_info }}</span>
            <span><strong>Total Found:</strong> {{ total_count }} Leads</span>
        </div>
        
        <table>
            <thead>
                <tr><th>Business Name</th><th>Contact Email</th><th>Phone Number</th></tr>
            </thead>
            <tbody>
                {% for item in results %}
                <tr>
                    <td><a href="{{ item.Link }}" target="_blank" style="text-decoration:none; color:#333;">{{ item.Company[:45] }}</a></td>
                    <td><span class="badge-email">{{ item.Email }}</span></td>
                    <td><span class="badge-phone">{{ item.Phone }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="pagination">
            {% if current_page > 1 %}
            <a href="/search?product={{ p }}&location={{ l }}&page={{ current_page - 1 }}" class="page-link">Previous</a>
            {% endif %}
            <span class="page-link active">{{ current_page }}</span>
            <a href="/search?product={{ p }}&location={{ l }}&page={{ current_page + 1 }}" class="page-link">Next</a>
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
    
    # For high-volume, we fetch the large list once
    # In a production app, we would cache this, but for now, we re-run to get fresh 2025 data
    data = volume_extractor(p, l)
    
    # Simple Pagination: show 100 per page
    per_page = 100
    start = (page_num - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]

    return render_template_string(
        HTML_TEMPLATE, 
        results=paginated_data, 
        total_count=len(data),
        query_info=f"{p} in {l}",
        p=p, l=l,
        current_page=page_num
    )
