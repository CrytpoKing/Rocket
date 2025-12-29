from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# --- THE SCRAPER LOGIC ---
def extract_leads(product, location):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = f"https://www.google.com/search?q={product}+{location}+dealers+email"
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for g in soup.find_all('div', class_='g'):
            text = g.get_text()
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            if emails:
                results.append({"url": "Found Business", "email": emails[0]})
        return results
    except Exception as e:
        return [{"url": "Error", "email": str(e)}]

# --- THE UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Lead Extractor</title></head>
<body style="font-family: sans-serif; padding: 40px;">
    <h2>🚀 Lead Extractor</h2>
    <form action="/search" method="get">
        <input type="text" name="product" placeholder="Product" required>
        <input type="text" name="location" placeholder="Location" required>
        <button type="submit">Search</button>
    </form>
    {% if results %}
    <table border="1" style="margin-top:20px; width:100%;">
        <tr><th>Source</th><th>Email</th></tr>
        {% for item in results %}
        <tr><td>{{ item.url }}</td><td>{{ item.email }}</td></tr>
        {% endfor %}
    </table>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    p = request.args.get('product')
    l = request.args.get('location')
    data = extract_leads(p, l)
    return render_template_string(HTML_TEMPLATE, results=data)

# No __main__ block or handler needed for Vercel
