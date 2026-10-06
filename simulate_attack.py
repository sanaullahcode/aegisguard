"""
AegisGuard - Full attack simulator.
Plays the attacker for every attack type AegisGuard defends against:
brute force, phishing, DoS flood, header spoofing, and trojan/malware
file upload. Run this while app/server.py is running on localhost:5000.
"""
import time
import requests

BASE = "http://127.0.0.1:5000"


def simulate_brute_force():
    print("\n=== 1. Brute-force login attack (Hydra-style) ===")
    headers = {"User-Agent": "THC-Hydra/9.2", "X-Forwarded-For": "10.0.0.99"}
    for i in range(6):
        r = requests.post(f"{BASE}/login", json={"username": "admin", "password": f"guess{i}"}, headers=headers)
        print(f"  attempt {i+1}: status={r.status_code}")
        time.sleep(0.2)


def simulate_phishing_check():
    print("\n=== 2. Phishing link submission ===")
    test_urls = [
        "https://www.google.com",
        "http://secure-login-update-account.verify-paypal.com.suspicious-domain.tk/reset?user=victim",
        "http://paypal-account-verify-secure-login.tk/update.php?id=1",
    ]
    for url in test_urls:
        r = requests.post(f"{BASE}/check-url", json={"url": url})
        body = r.json()
        print(f"  {url}\n    -> phishing={body.get('is_phishing')} probability={body.get('phishing_probability')}")


def simulate_dos():
    print("\n=== 3. DoS flood attack ===")
    headers = {"X-Forwarded-For": "10.0.0.77"}
    blocked_at = None
    for i in range(25):
        r = requests.get(f"{BASE}/health", headers=headers)
        if r.status_code == 403 and blocked_at is None:
            blocked_at = i + 1
        time.sleep(0.05)
    print(f"  sent 25 rapid requests, blocked starting at request #{blocked_at}")


def simulate_spoofing():
    print("\n=== 4. Header spoofing ===")
    r = requests.get(f"{BASE}/health", headers={
        "X-Forwarded-For": "not-a-real-ip, 10.0.0.1, 10.0.0.2, 10.0.0.3, 10.0.0.4",
        "Host": "totally-different-domain.evil",
    })
    print(f"  spoofed-header request: status={r.status_code} (allowed + logged, since spoofing alone isn't blocking-worthy)")


def simulate_malware_scan():
    print("\n=== 5. Trojan/malware file scan ===")
    eicar = rb"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    files = {"file": ("eicar_test.com", eicar)}
    r = requests.post(f"{BASE}/scan-file", files=files)
    print(f"  EICAR test file scan: {r.json()}")

    clean_files = {"file": ("notes.txt", b"Just a normal text file, nothing malicious here.")}
    r = requests.post(f"{BASE}/scan-file", files=clean_files)
    print(f"  clean file scan: {r.json()}")

    disguised = {"file": ("invoice.pdf.exe", b"cmd.exe /c powershell -enc aGVsbG8=")}
    r = requests.post(f"{BASE}/scan-file", files=disguised)
    print(f"  disguised executable scan: {r.json()}")


def check_incidents():
    print("\n=== Incidents AegisGuard recorded ===")
    r = requests.get(f"{BASE}/incidents")
    incidents = r.json()
    print(f"Total incidents logged: {len(incidents)}")
    by_type = {}
    for inc in incidents:
        t = inc.get("attack_type")
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in by_type.items():
        print(f"  {t}: {c} incident(s)")


if __name__ == "__main__":
    simulate_brute_force()
    simulate_phishing_check()
    simulate_dos()
    simulate_spoofing()
    simulate_malware_scan()
    check_incidents()
