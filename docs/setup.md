# CivicRoute Setup Guide

## 1. Prerequisites

Recommended environment:

- Windows 10/11
- Python 3.10+
- Git
- Modern Chromium-based browser
- Internet connection for first-time dependency/model download

---

## 2. Clone Repository

```bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
cd MechMavrix-submission
```

If you already have the project locally, open:

```text
C:\hackthon\MechMavrix-submission
```

---

## 3. Create Virtual Environment

From the project root:

```bash
python -m venv .venv
```

---

## 4. Activate Virtual Environment

Windows CMD:

```bash
.venv\Scripts\activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

---

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

The first install may take time because PyTorch and Transformers are large packages.

---

## 6. Start CivicRoute

From the project root:

```bash
python src/app.py
```

Expected development URL:

```text
http://127.0.0.1:5000
```

---

## 7. Open Citizen Portal

Browser:

```text
http://127.0.0.1:5000
```

The page should show:

- MechMavrix CivicRoute
- Complaint photo upload
- GPS capture
- Online/offline banner
- Analyse & Route Complaint button
- Track Complaint link
- Staff Dashboard link

---

## 8. First AI Run

The first complaint analysis may download:

`openai/clip-vit-base-patch32`

through Hugging Face Transformers.

This can take time depending on internet speed.

After the model is cached locally, later runs are faster.

---

## 9. Submit a Test Complaint

1. Choose a civic complaint photo.
2. Click `Capture Current Location`.
3. Optionally enter a description.
4. Click `Analyse & Route Complaint`.

The backend will attempt to:

- Validate the image
- Check exact duplicates
- Reverse-geocode GPS
- Query nearby public-risk places
- Detect issue type
- Estimate severity
- Resolve jurisdiction
- Select department
- Calculate priority
- Store the complaint

A successful report receives a permanent complaint ID such as:

```text
CR-20260920-ABC123
```

---

## 10. Citizen Tracking

Open:

```text
http://127.0.0.1:5000/track
```

Enter a complaint ID.

The page can display:

- Current status
- Issue
- Authority
- Department
- Priority
- Assignment
- Resolution
- Status timeline

---

## 11. Staff Dashboard

Open:

```text
http://127.0.0.1:5000/staff
```

The prototype dashboard supports:

- Complaint list
- Filters
- Search
- Evidence inspection
- Assignment
- Status update
- Resolution
- History

Important:

The current hackathon dashboard does not include production-grade authentication or role-based access control.

---

## 12. Offline Mode Test

CivicRoute supports offline complaint queuing after the app has loaded online at least once.

### Step A — Install Service Worker

Open the Citizen Portal while online:

```text
http://127.0.0.1:5000
```

Wait for the page to finish loading.

The Service Worker should register automatically.

---

### Step B — Simulate Offline

In Chrome/Edge DevTools:

1. Open `Network`
2. Change throttling from `No throttling` to `Offline`
3. Reload the page

The cached Citizen Portal should still open.

Expected banner:

```text
Offline — complaint will be queued on this device
```

---

### Step C — Queue Complaint Offline

While offline:

1. Choose a photo
2. Capture GPS
3. Submit

The complaint should receive a temporary local ID:

```text
OFFLINE-...
```

The pending counter should increase.

---

### Step D — Reconnect

In DevTools:

Change:

```text
Offline
```

back to:

```text
No throttling
```

CivicRoute attempts to synchronize queued reports automatically.

After successful sync:

- Pending queue count decreases
- A permanent backend complaint ID is created

---

## 13. Run Core Verification Tests

### Core system tests

```bash
python tests/verify_system.py
```

### Boundary versioning tests

```bash
python tests/verify_boundary_versioning.py
```

### Boundary provenance tests

```bash
python tests/verify_boundary_sources.py
```

---

## 14. AI Benchmark Scaffold

The repository contains:

```text
tests/verify_ai_benchmark.py
```

This is intended for structured AI evaluation when a suitable labelled test image set is available.

The current project does not claim a production-level AI accuracy percentage.

---

## 15. Runtime Data

CivicRoute creates runtime data under:

```text
data/
```

This may include:

- SQLite database
- Uploaded complaint images

The runtime `data/` directory is excluded from Git.

---

## 16. Important Runtime Files

Main backend:

```text
src/app.py
```

Database:

```text
src/database.py
```

Location engine:

```text
src/location_engine.py
```

Jurisdiction engine:

```text
src/jurisdiction.py
```

Boundary provenance:

```text
src/boundary_sources.py
```

Citizen frontend:

```text
src/templates/index.html
src/static/app.js
src/static/styles.css
```

Offline queue:

```text
src/static/offline-db.js
```

Service Worker:

```text
src/static/sw.js
src/static/register-sw.js
```

Tracking:

```text
src/templates/track.html
src/static/track.js
```

Staff dashboard:

```text
src/templates/staff.html
src/static/staff.js
```

---

## 17. Service Worker Verification

Open in browser:

```text
http://127.0.0.1:5000/sw.js
```

It should return JavaScript.

In DevTools:

```text
Application > Service Workers
```

Expected scope:

```text
http://127.0.0.1:5000/
```

---

## 18. Troubleshooting — GPS Permission

If location capture fails:

- Allow location permission in the browser
- Confirm OS location services are enabled
- Retry from `127.0.0.1`
- Check browser DevTools Console

Desktop GPS accuracy may be lower than mobile-device GPS accuracy.

---

## 19. Troubleshooting — AI Model

If the first AI run appears slow:

- Confirm internet is available
- Wait for model download
- Check terminal output
- Ensure enough free disk space
- Restart the Flask server after interrupted downloads if needed

---

## 20. Troubleshooting — Public Map Services

If location context fails:

Possible causes:

- Nominatim unavailable
- Overpass unavailable
- Network timeout
- Rate limiting

CivicRoute is designed to use a review fallback rather than fabricate a verified result.

---

## 21. Troubleshooting — Offline Page Does Not Open

Check:

1. The app was loaded online first.
2. `/sw.js` returns successfully.
3. DevTools `Application > Service Workers` shows the worker.
4. Service Worker scope is `/`.
5. Browser storage has not been cleared.

---

## 22. Troubleshooting — Pending Offline Complaint

If a pending offline complaint does not sync:

1. Restore connectivity.
2. Keep the Citizen Portal open.
3. Confirm the top banner shows online.
4. Wait briefly for automatic sync.
5. Reload while online if necessary.

Do not clear browser site data before synchronization, because IndexedDB contains the pending report.

---

## 23. Development Server Warning

Flask may print:

```text
WARNING: This is a development server.
Do not use it in a production deployment.
```

This is expected during local development.

For production, use a proper WSGI deployment and HTTPS.

---

## 24. Production Requirements

Before real municipal deployment, add:

- Staff authentication
- RBAC
- HTTPS
- Production WSGI server
- PostgreSQL/PostGIS
- Secure object storage
- Rate limiting
- Monitoring
- Backups
- Privacy controls
- Official GIS boundaries
- Civic-policy validation
- AI benchmark validation

---

## 25. Quick Start Summary

```bash
cd MechMavrix-submission
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/app.py
```

Then open:

```text
http://127.0.0.1:5000
```
