# AegisGuard
Real-Time Multi-Vector Attack Detection, Blocking, and Recommendation System

FYP - BS Software Engineering, FUUAST Islamabad (Section SE 6A)
Solo project: Sana Ullah (42051)

## What this is
A working prototype of a cybersecurity tool that watches traffic hitting a
protected application, figures out **which kind of attack** is happening
and, where possible, **which tool** is likely behind it, **blocks the
source before it does more damage**, and tells you **exactly which
security control to add** so the same attack doesn't work again.

Five attack types are covered end to end:

| Attack type | How it's detected | How it's blocked | What's recommended |
|---|---|---|---|
| Brute force | Failed-login rate per IP in a sliding window (`detector/brute_force_detector.py`) | IP blocked with 403 after threshold | 2FA, CAPTCHA, account lockout, rate limiting |
| Phishing | Rule-based URL scorer — IP-as-domain, hyphens, suspicious keywords, shady TLDs, shorteners, punycode (`phishing/phishing_rules.py`) | Link flagged, would be blocked at DNS/email-gateway level | SPF/DKIM/DMARC, phishing-awareness training, 2FA |
| DoS / flood | Total request rate per IP across all endpoints (`detector/dos_detector.py`) | IP blocked with 403 once flood threshold crossed | Rate limiting, anti-DDoS/CDN, connection caps |
| Spoofing | HTTP-layer header checks — forged X-Forwarded-For, Host header injection (`detector/spoofing_detector.py`) | Flagged and logged (see note below) | Trusted-proxy validation, strict Host allow-list, HSTS |
| Trojan / malware | SHA-256 signature match + entropy/suspicious-string/double-extension heuristics (`detector/malware_detector.py`) | File quarantined, not processed | Quarantine, AV/EDR scan, application allow-listing |

A rule-based attack fingerprinting layer (`fingerprint/attack_classifier.py`)
also recognizes known attack-tool signatures — e.g. THC-Hydra's User-Agent
string for brute force, Nmap's for reconnaissance/scanning — so the tool
can name the likely tool, not just the attack category.

## Why phishing detection is rule-based, not the trained ML model

A Random Forest was trained on a real, public phishing-URL dataset
(58,645 labeled samples, `data/phishing.csv`, from GregaVrbancic's
Phishing Dataset) and reached **90.1% accuracy** — see
`outputs/artifacts/phishing_metrics.json`. That result is reported as a
benchmark.

But that dataset's 97 structural features are only loosely documented,
and rebuilding them from a raw URL string at inference time (which is all
a live tool has to work with) produced unreliable results — it flagged
**google.com** as phishing with 93% confidence in early testing here.
Rather than ship a detector that misclassifies obviously safe sites, the
**live** `/check-url` endpoint uses a transparent, hand-verified rule-based
scorer instead. Every flag it raises comes with the specific reason (e.g.
"uses a URL-shortening service", "5 hyphens in the domain"), which is more
defensible for a security tool than an unexplained probability from a
model whose features can't be reliably reproduced outside its original
dataset. This trade-off — and how it was discovered — is documented
because it's a real engineering decision worth explaining in your defense,
not a shortcut to hide.

## How to run it yourself

```bash
pip install -r requirements.txt

# (Optional) retrain/re-verify the benchmark phishing model
python phishing/train_phishing_model.py

# Start the protected demo app
python app/server.py

# In another terminal, play the attacker
python simulate_attack.py

# View results
streamlit run dashboard/app.py
```

## Folder structure

```
aegisguard/
├── app/server.py              Protected Flask demo app + AegisGuard middleware
├── detector/
│   ├── brute_force_detector.py
│   ├── dos_detector.py
│   ├── spoofing_detector.py
│   └── malware_detector.py
├── fingerprint/attack_classifier.py   Attack-tool signature matching
├── phishing/
│   ├── phishing_rules.py       Live rule-based URL scorer (used by the app)
│   ├── train_phishing_model.py Benchmark ML model (research result)
│   └── url_features.py         Structural feature extractor
├── recommend/recommendation_engine.py  Attack type -> mitigation mapping
├── dashboard/app.py             Streamlit dashboard
├── simulate_attack.py           End-to-end attack simulator
├── data/phishing.csv            Real phishing dataset (benchmark only)
└── outputs/                     Trained model, metrics, live incident log
```

## Honest limitations to mention in your defense

- Spoofing detection here works at the HTTP header layer (forged
  X-Forwarded-For, Host injection). True network-layer spoofing (ARP
  cache poisoning, raw IP source-address forgery) needs packet capture —
  a natural extension using Scapy against real network interfaces.
- Malware detection never uses real malware. Hash matching is demonstrated
  with the EICAR test string, the industry-standard safe file every
  antivirus vendor recognizes for exactly this purpose.
- The phishing rule weights were hand-tuned against a handful of test
  cases, not formally optimized — a good next step is calibrating them
  against a labeled URL set the same way the benchmark model was trained.

## What to build next (for the two-semester timeline)

- Wire the spoofing detector into a real packet-capture layer (Scapy) for
  ARP/IP-level spoofing, not just HTTP headers.
- Calibrate the phishing rule weights against a labeled dataset instead of
  hand-picked thresholds.
- Add persistent storage (SQLite) for the incident log instead of a flat
  JSON file, and add authentication to the dashboard.
- Extend the malware scanner with real (safely sandboxed) dynamic analysis
  instead of static heuristics only.
