# 🟦 7 — Dockerize scraper and report generation

## 🎯 Goal

Make the entire pipeline portable and reproducible.

After this milestone, anyone can run the scraper + report generation without installing Python or uv locally.

---

## ✅ What Docker enables

- consistent execution across machines  
- easier onboarding  
- CI/CD readiness  
- deployment portability  

---

## 📂 Files added

- `Dockerfile`
- `.dockerignore`

---

## 🐳 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY scraper ./scraper

RUN uv sync

COPY . .
RUN uv pip install -e .

CMD ["uv", "run", "python", "-m", "scraper.cli", "run"]
```

---

## 🗂️ .dockerignore

```
.git
.venv
__pycache__
*.pyc
iphone_price_monitor.egg-info
data
reports
assets/images
```

---

## ▶️ Build

```bash
docker build -t iphone-monitor .
```

## ▶️ Run (write outputs to your local folder)

```bash
docker run --rm -v "$(pwd):/app" iphone-monitor
```

This will generate/update:

```
data/processed/prices.csv
data/processed/prices.json
assets/images/*.png
reports/index.html
```

---

## 🧯 Troubleshooting

### ❗ "Dockerfile: no such file or directory"

Docker must be executed from the repository root (where Dockerfile exists):

```bash
ls Dockerfile pyproject.toml
```

### ❗ "package directory 'scraper' does not exist"

Ensure the Dockerfile copies the `scraper/` folder **before** running `uv sync`.

---

## ✅ What we achieved

- ✔ One-command reproducible execution  
- ✔ Environment independence  
- ✔ Outputs produced locally via volume mount  
- ✔ Ready for CI, cron, and cloud deployments  

