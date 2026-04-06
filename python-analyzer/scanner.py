import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

TARGET = input("Target URL: ").strip()
results = []

COMMON_PATHS = ["/robots.txt", "/sitemap.xml", "/admin", "/backup", "/api-docs"]

SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy"
]

def add_finding(title, severity, evidence, remediation):
    results.append({
        "finding": title,
        "severity": severity,
        "evidence": evidence,
        "remediation": remediation
    })

try:
    r = requests.get(TARGET, timeout=10, verify=False)
    headers = r.headers

    if TARGET.startswith("http://"):
        add_finding(
            "HTTP used instead of HTTPS",
            "High",
            TARGET,
            "Serve the application over HTTPS and redirect HTTP to HTTPS."
        )

    for h in SECURITY_HEADERS:
        if h not in headers:
            add_finding(
                f"Missing security header: {h}",
                "Medium",
                f"{h} not present",
                f"Configure the server to return the {h} header."
            )

    if "Server" in headers:
        add_finding(
            "Server banner disclosed",
            "Low",
            headers["Server"],
            "Reduce or suppress server version disclosure."
        )

    soup = BeautifulSoup(r.text, "html.parser")
    forms = soup.find_all("form")
    for form in forms:
        action = form.get("action", "")
        full_action = urljoin(TARGET, action)
        if full_action.startswith("http://"):
            add_finding(
                "Form submits over HTTP",
                "High",
                full_action,
                "Ensure forms submit only over HTTPS."
            )

    for path in COMMON_PATHS:
        test_url = urljoin(TARGET, path)
        try:
            rr = requests.get(test_url, timeout=5, verify=False)
            if rr.status_code == 200:
                add_finding(
                    f"Interesting path exposed: {path}",
                    "Low",
                    test_url,
                    "Review whether this path should remain public."
                )
        except:
            pass

    risk_score = 0
    for item in results:
        if item["severity"] == "High":
            risk_score += 3
        elif item["severity"] == "Medium":
            risk_score += 2
        else:
            risk_score += 1

    report = {
        "target": TARGET,
        "risk_score": risk_score,
        "findings": results
    }

    with open("report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Done. Report saved to report.json")

except Exception as e:
    print("Scan error:", e)