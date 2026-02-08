# 🗺️ Build Roadmap

El proyecto evoluciona mediante hitos incrementales y reproducibles.  
Cada paso añade una capacidad real de producción.

---

## 📌 Resumen de los 8 pasos

1. **Project setup, environment & CLI foundation**  
2. **Source adapter (GitHub Pages catalog)**  
3. **Historical persistence (CSV/JSON pipeline)**  
4. **Download & cache product images locally**  
5. **HTML dashboard with price timeline (Chart.js)**  
6. **Automated tests (normalization & dedupe)**  
7. **Dockerized execution**  
8. **Automation: local dev loop + GitHub Actions scheduled runs**

Ahora bajamos al detalle 👇

---

# 1 — Project Setup, Environment & CLI Foundation  
**Issue:** #1–#2

### 🎯 Goal  
Inicializar un proyecto Python profesional usando uv, definir la estructura y asegurar que el CLI funciona.

### ▶️ Run  
```bash
uv run python -m scraper.cli healthcheck
```

### 📦 What was introduced
- project layout  
- dependency management  
- minimal CLI  
- reproducible environment  

---

# 2 — Source Adapter (GitHub Pages Catalog)  
**Issue:** #3

### 🎯 Goal  
Scrapear páginas controladas y devolver snapshots estructurados.

**Source:**  
👉 https://andres-torrez.github.io/iphone-catalog/

### ▶️ Run  
```bash
uv run python -m scraper.cli scrape
```

### 📤 Output  
JSON con:
- model  
- title  
- sku  
- price  
- image  
- timestamp  

### 📦 What was introduced
- adapter pattern  
- HTML parsing  
- price normalization  
- typed data model  

---

# 3 — Historical Persistence (CSV/JSON Pipeline)  
**Issue:** #4

### 🎯 Goal  
Convertir snapshots en un dataset histórico.

### ▶️ Run  
```bash
uv run python -m scraper.cli run
```

### 📤 Output  
```
data/processed/prices.json
data/processed/prices.csv
```

### 📦 What was introduced
- history merge  
- deduplication  
- reproducible exports  
- storage layer  

Ahora el proyecto se comporta como un **data pipeline**, no un script.

---

# 4 — Download & Cache Product Images Locally  
**Issue:** #5

### 🎯 Goal  
Hacer los reportes independientes de internet.

### ▶️ Run  
```bash
uv run python -m scraper.cli run
```

### 📤 Output  
```
assets/images/
```

Y `image_path` dentro del dataset.

### 📦 What was introduced
- media pipeline  
- cache strategy  
- deterministic assets  

---

# 5 — Generate the HTML Dashboard (Chart.js)  
**Issue:** #6

### 🎯 Goal  
Convertir el histórico en un producto visual.

### ▶️ Run  
```bash
uv run python -m scraper.cli run
```

### 📤 Output  
```
reports/index.html
```

### 📊 Dashboard includes
- latest price per model  
- delta vs previous  
- timeline graph  
- cached images  
- last update timestamp  

Ahora stakeholders pueden ver el sistema funcionando.

---

# 6 — Automated Tests (Normalization & Dedupe)  
**Issue:** #7

### 🎯 Goal  
Garantizar la corrección de los datos.

### ▶️ Run  
```bash
uv run pytest -q
```

### 🧪 Tests cover
- European price parsing  
- duplicate detection  

### 📦 What was introduced
- repeatability  
- trust in the pipeline  
- CI readiness  

---

# 7 — Dockerized Execution  
**Issue:** #8

### 🎯 Goal  
Ejecutar todo con un solo comando, en cualquier sitio.

### ▶️ Build  
```bash
docker build -t iphone-monitor .
```

### ▶️ Run  
```bash
docker run --rm -v "$(pwd):/app" iphone-monitor
```

### 📤 Output  
Los mismos artefactos:
- CSV  
- JSON  
- images  
- HTML report  

Ahora el proyecto es **portable**.

---

# 8 — Automation: Local Dev Loop + GitHub Actions  
**Issue:** #9

### 🎯 Goal  
Eliminar la ejecución manual.

---

## 🖥️ Local development loop (visual)

Corre cada 2 minutos:

- tests  
- scraper  
- report generation  

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev_loop.ps1
```

Puedes ver los archivos actualizándose en VS Code.

---

## ☁️ GitHub Actions schedule

Corre automáticamente desde `main`.

Pipeline:

- install  
- pytest  
- run scraper  
- upload artifacts  

También puedes lanzarlo manualmente desde **Actions → Run workflow**.

---

# 🎉 Final System Capability

Al terminar el paso 8 tienes:

- modular architecture  
- real scraping  
- history  
- visual dashboard  
- local assets  
- tests  
- docker  
- automation  
- reproducibility  
- portfolio-level engineering  
