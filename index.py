import os
import requests
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
SERPER_API_KEY = "be17ec094e7663c3d4be5ad14f89429ae34ed76f"

# SMTP Settings (Use App Passwords for Gmail)
SMTP_SERVER = "smtp.gmail.com" 
SMTP_PORT = 587
SMTP_USER = "YOUR_EMAIL@gmail.com"
SMTP_PASS = "YOUR_APP_PASSWORD" 

# --- LEAD ENGINE (REUSE FROM PREVIOUS VERSION) ---
def deep_volume_extractor(product, location):
    # ... (Keep your previous extraction code here) ...
    # For now, I'm using a simplified version for the demo
    return [{"Company": "Example Corp", "Email": "test@example.com", "Phone": "123", "Director": "Google"}]

# --- MAILING ENGINE ---
def send_bulk_campaign(emails, subject, body):
    sent_count = 0
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        for recipient in emails:
            msg = MIMEMultipart()
            msg['From'] = f"Lead Engine <{SMTP_USER}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server.send_message(msg)
            sent_count += 1
            
        server.quit()
        return sent_count
    except Exception as e:
        print(f"Mail Error: {e}")
        return 0

# --- THE UNIFIED UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lead Engine + Bulk Mailer</title>
    <style>
        body { font-family: 'Inter', sans-serif; background: #f0f2f5; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 300px; background: #1a73e8; color: white; padding: 20px; }
        .main-content { flex: 1; padding: 30px; overflow-y: auto; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        input, textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { background: #34a853; color: white; border: none; padding: 12px 25px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
        .status-success { color: #2ecc71; font-weight: bold; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🛠 Control Panel</h2>
        <hr>
        <p>1. Extract Leads</p>
        <p>2. Review Results</p>
        <p>3. Send Bulk Campaign</p>
    </div>

    <div class="main-content">
        <div class="card">
            <h3>🚀 Step 1: Extract Leads</h3>
            <form action="/search" method="get" style="display: flex; gap: 10px;">
                <input type="text" name="product" placeholder="Product" required>
                <input type="text" name="location" placeholder="Location" required>
                <button type="submit" style="width: auto;">Search</button>
            </form>
        </div>

        {% if results %}
        <div class="card">
            <h3>✉️ Step 2: Send Bulk Email to {{ total_count }} Leads</h3>
            <form action="/send-campaign" method="post">
                <input type="hidden" name="emails" value="{{ email_list }}">
                <div class="form-group">
                    <input type="text" name="subject" placeholder="Email Subject" required>
                </div>
                <div class="form-group">
                    <textarea name="message" rows="5" placeholder="Your Message (HTML allowed)" required></textarea>
                </div>
                <button type="submit" style="background: #1a73e8;">Launch Campaign Now</button>
            </form>
        </div>

        <div class="card">
            <h3>📋 Extraction Results</h3>
            <table>
                <thead><tr><th>Name</th><th>Email</th><th>Source</th></tr></thead>
                <tbody>
                    {% for item in results %}
                    <tr>
                        <td>{{ item.Company[:40] }}</td>
                        <td>{{ item.Email }}</td>
                        <td>{{ item.Director }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        {% if success_msg %}
        <div class="card status-success">
            ✅ {{ success_msg }}
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
    data = deep_volume_extractor(p, l) # Use the logic from the previous step
    email_list = ",".join([x['Email'] for x in data])
    
    return render_template_string(
        HTML_TEMPLATE, 
        results=data, 
        total_count=len(data),
        email_list=email_list
    )

@app.route('/send-campaign', methods=['POST'])
def campaign():
    emails = request.form.get('emails', '').split(',')
    subject = request.form.get('subject', '')
    message = request.form.get('message', '')
    
    count = send_bulk_campaign(emails, subject, message)
    return render_template_string(HTML_TEMPLATE, success_msg=f"Successfully sent {count} emails!")

if __name__ == "__main__":
    app.run(debug=True)
