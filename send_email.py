import os
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# ======================================================
# Load pytest-generated environment properties
# ======================================================
def load_properties(path: str):
    if not os.path.exists(path):
        print(f"⚠ test_env.properties not found at {path}")
        return

    print("📥 Loading test_env.properties")

    with open(path, "r", encoding="utf-8") as properties_file:
        for line in properties_file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


# 🔥 CRITICAL FIX
load_properties("test_env.properties")

# ======================================================
# Environment variables
# ======================================================
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
BUILD_ID = os.getenv("CODEBUILD_BUILD_ID", "N/A")
REGION = os.getenv("REGION", "ap-south-1")
TEST_STATUS = os.getenv("TEST_STATUS", "FAILED").upper()
HTML_REPORT_PATH = os.getenv("HTML_REPORT_PATH")

# Metrics (NOW correctly loaded)
TOTAL_TESTS = os.getenv("TOTAL_TESTS", "0")
PASSED = os.getenv("PASSED", "0")
FAILED = os.getenv("FAILED", "0")
SKIPPED = os.getenv("SKIPPED", "0")
START_TIME = os.getenv("START_TIME", "N/A")
END_TIME = os.getenv("END_TIME", "N/A")
DURATION = os.getenv("DURATION", "N/A")

ENVIRONMENT = os.getenv("ENVIRONMENT", "Test")
BASE_URL = os.getenv("BASE_URL", "https://testapp.cflowapps.com")

# ======================================================
# Mandatory validation (UPDATED)
# ======================================================
required_vars = {
    "EMAIL_FROM": EMAIL_FROM,
    "EMAIL_TO": EMAIL_TO,
}

missing = [k for k, v in required_vars.items() if not v]
if missing:
    raise RuntimeError(f"❌ Missing required environment variables: {', '.join(missing)}")

# Normalize status
TEST_STATUS = "PASSED" if TEST_STATUS == "PASSED" else "FAILED"

# ======================================================
# Debug (safe to keep)
# ======================================================
print("📊 Final Test Metrics")
print("TOTAL_TESTS =", TOTAL_TESTS)
print("PASSED =", PASSED)
print("FAILED =", FAILED)
print("SKIPPED =", SKIPPED)
print("DURATION =", DURATION)

# ======================================================
# Email Setup
# ======================================================
msg = MIMEMultipart()
msg["Subject"] = f"Cflow Automation Test Report - {TEST_STATUS}"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

status_color = "green" if TEST_STATUS == "PASSED" else "red"
badge_bg = "#d4edda" if TEST_STATUS == "PASSED" else "#f8d7da"
badge_border = "#28a745" if TEST_STATUS == "PASSED" else "#dc3545"

# ======================================================
# HTML Body
# ======================================================
body_html = f"""
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; }}
    .container {{
        width: 90%;
        margin: auto;
        padding: 20px;
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}
    .header {{ text-align: center; }}
    .logo {{ width: 180px; }}
    .status-badge {{
        display: inline-block;
        padding: 6px 14px;
        font-size: 14px;
        border-radius: 20px;
        background: {badge_bg};
        border: 1px solid {badge_border};
        color: {status_color};
        font-weight: bold;
    }}
    table {{
        width: 70%;
        border-collapse: collapse;
        margin-top: 10px;
    }}
    th, td {{
        padding: 8px;
        text-align: center;
        border-bottom: 1px solid #ddd;
        font-weight: 600;
    }}
    th {{ background: #f0f4f7; }}
    h1, h2, h3 {{ color: #004085; }}
    .footer {{
        font-size: 12px;
        color: gray;
        margin-top: 30px;
        text-align: center;
    }}
  </style>
</head>

<body>
<div class="container">

    <div class="header">
        <img src="https://www.cflowapps.com/wp-content/uploads/2020/05/cflow-logo-ads.png" class="logo">
        <h1>Automation Test Report</h1>
        <div class="status-badge">{TEST_STATUS}</div>
    </div>

    <p><b>Build ID:</b> {BUILD_ID}</p>

    <h3>Test Summary</h3>
    <table>
        <tr>
            <th>Total Tests</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Skipped</th>
        </tr>
        <tr>
            <td>{TOTAL_TESTS}</td>
            <td>{PASSED}</td>
            <td>{FAILED}</td>
            <td>{SKIPPED}</td>
        </tr>
    </table>

    <h3>Execution Details</h3>
    <p><b>Start Time:</b> {START_TIME}</p>
    <p><b>End Time:</b> {END_TIME}</p>
    <p><b>Duration:</b> {DURATION}</p>
    <p><b>Environment:</b> {ENVIRONMENT}</p>
    <p><b>Base URL:</b> <a href="{BASE_URL}">{BASE_URL}</a></p>

    <p>Your detailed HTML report is attached.</p>

    <div class="footer">
        This is an automated message from Cflow Automation System. Do not reply.
    </div>

</div>
</body>
</html>
"""

msg.attach(MIMEText(body_html, "html"))

# ======================================================
# Attach HTML report (UPDATED SAFE VERSION)
# ======================================================
if HTML_REPORT_PATH and os.path.exists(HTML_REPORT_PATH):

    part = MIMEBase("text", "html")

    with open(HTML_REPORT_PATH, "rb") as f:
        part.set_payload(f.read())

    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename={os.path.basename(HTML_REPORT_PATH)}"
    )

    msg.attach(part)

else:
    print("⚠ HTML report not found. Sending email without attachment.")
# ======================================================
# Send email via SES
# ======================================================
ses = boto3.client("ses", region_name=REGION)
response = ses.send_raw_email(
    Source=EMAIL_FROM,
    Destinations=[e.strip() for e in EMAIL_TO.split(",")],
    RawMessage={"Data": msg.as_string()}
)

print(f"✅ Email sent successfully. Message ID: {response['MessageId']}")
