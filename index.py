import os
import requests
import re
from flask import Flask, request, render_template_string

app = Flask(__name__)

# --- CONFIGURATION ---
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"
# Get a free key at resend.com to send thousands of emails instantly
RESEND_API_KEY = "re_your_free_key_here" 

# --- KEEPING YOUR EXTRACTION CODE EXACTLY AS IT IS ---
class DirectorScanner:
    def __init__(self, product, location):
        self.product = product
        self.location = location
        self.leads = []
        self.headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}

    def scan_source(self, platform_query, source_name):
        url = "https://google.serper.dev/search"
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
            except: break

    def run_full_scan(self):
        self.scan_source(f'"{self.product}" "{self.location}" email', "Google Search")
        self.scan_source(f'site:yellowpages.com "{self.product}" "{self.location}"', "Yellow Pages")
        self.scan_source(f'site:thomasnet.com "{self.product}" "{self.location}"', "ThomasNet")
        self.scan_source(f'site:facebook.com "{self.product}" "{self.location}" email', "Facebook")
        unique = {v['Email']: v for v in self.leads}.values()
        return list(unique)

# --- NEW BULK MAILING LOGIC ---
def send_bulk_resend(emails, subject, content):
    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
    
    # Resend allows sending to multiple people in one API call
    payload = {
        "from": "Acquisition <onboarding@resend.dev>",
        "to": emails[:50], # Send to first 50 leads as a batch
        "subject": subject,
        "html": content
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        return resp.status_code == 200
    except: return False

# --- UI WITH SIDEBAR CONTROL PANEL ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Extractor Pro + Mailer</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f4f7f6; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 260px; background: #1a73e8; color: white; padding: 30px; display: flex; flex-direction: column; gap: 20px; }
        .main { flex: 1; padding: 40px; overflow-y: auto; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; }
        .sidebar h2 { margin-bottom: 30px; font-size: 22px; border-bottom: 1px solid #ffffff33; padding-bottom: 10px; }
        .nav-item { color: #ffffffcc; text-decoration: none; font-weight: 500; display: flex; align-items: center; gap: 10px; }
        .nav-item.active { color: white; font-weight: bold; }
        input, textarea { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { background: #34a853; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th, td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; }
        .tag { background: #e8f0fe; color: #1a73e8; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🛠 Control Panel</h2>
        <a href="/" class="nav-item active">🏠 Dashboard</a>
        <a href="#" class="nav-item">📈 Analytics</a>
        <a href="#" class="nav-item">⚙️ Settings</a>
        <div style="margin-top:auto; font-size: 12px; color: #ffffff99;">V2025.12 High Volume</div>
    </div>

    <div class="main">
        <div class="card">
            <h3>🔍 1. Extract Institutional Leads</h3>
            <form action="/search" method="get" style="display: flex; gap: 10px;">
                <input type="text" name="product" placeholder="Product (e.g. Caterpillar)" required>
                <input type="text" name="location" placeholder="Location (e.g. Accra)" required>
                <button type="submit" style="width: 150px;">Extract</button>
            </form>
        </div>

        {% if results %}
        <div class="card" style="border-left: 5px solid #1a73e8;">
            <h3>✉️ 2. Bulk Email Campaign ({{ total }} Leads Found)</h3>
            <form action="/send-bulk" method="post">
                <input type="hidden" name="emails" value="{{ email_list }}">
                <input type="text" name="subject" placeholder="Campaign Subject" required>
                <textarea name="msg" rows="4" placeholder="Email body (HTML support enabled)..." required></textarea>
                <button type="submit" style="background: #1a73e8;">Launch Campaign</button>
            </form>
        </div>

        <div class="card">
            <h3>📋 3. Lead Results</h3>
            <table>
                <thead><tr><th>Company</th><th>Email</th><th>Source</th></tr></thead>
                <tbody>
                    {% for item in results %}
                    <tr>
                        <td><strong>{{ item.Company[:40] }}</strong></td>
                        <td><span style="color:#d35400;">{{ item.Email }}</span></td>
                        <td><span class="tag">{{ item.Director }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        {% if status %}
        <div class="card" style="background: #e6fffa; border: 1px solid #b2f5ea; color: #2c7a7b;">
            <b>Status:</b> {{ status }}
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
    p, l = request.args.get('product', ''), request.args.get('location', '')
    scanner = DirectorScanner(p, l)
    data = scanner.run_full_scan()
    email_list = ",".join([x['Email'] for x in data])
    return render_template_string(HTML_TEMPLATE, results=data[:100], total=len(data), email_list=email_list)

@app.route('/send-bulk', methods=['POST'])
def send_bulk():
    emails = request.form.get('emails', '').split(',')
    sub = request.form.get('subject', '')
    msg = request.form.get('msg', '')
    success = send_bulk_resend(emails, sub, msg)
    return render_template_string(HTML_TEMPLATE, status="Campaign Launched Successfully!" if success else "Failed to send.")
