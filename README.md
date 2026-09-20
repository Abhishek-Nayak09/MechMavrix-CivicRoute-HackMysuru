# MechMavrix CivicRoute

> Evidence-driven civic complaint routing for Mysuru.

**Team:** MechMavrix  
**Hackathon:** HackMysuru 1.0  
**Track:** Civic Governance & Clean Mysuru  
**Primary Subproblem:** Routing

---

## 1. Problem

Citizens often know **what problem they see**, but they may not know:

- Which civic authority owns the location
- Which department should receive the complaint
- How urgent the issue is
- Whether a similar complaint already exists
- What happens after submission

A complaint system that asks citizens to manually choose jurisdiction, department, severity or priority can create incorrect routing and delay.

---

## 2. Our Solution

**CivicRoute** asks the citizen for only:

1. Complaint photo
2. Current GPS location
3. Optional description

The system then performs the remaining routing workflow automatically.

CivicRoute analyses:

- Civic issue type
- Visual severity
- Location context
- Nearby public-risk locations
- Jurisdiction rule
- Responsible authority
- Responsible department
- Priority score
- Duplicate candidates

It then creates a persistent complaint ID that can be tracked by the citizen and managed by civic staff.

---

## 3. Core Workflow

```text
Citizen
   |
   | Photo + GPS + optional description
   v
CivicRoute
   |
   +--> Validate evidence
   |
   +--> Server-side location context
   |
   +--> AI issue classification
   |
   +--> AI severity estimation
   |
   +--> Duplicate protection
   |
   +--> Jurisdiction routing
   |
   +--> Department routing
   |
   +--> Priority calculation
   |
   v
Complaint Database
   |
   +--> Citizen Tracking
   |
   +--> Staff Dashboard
   |
   +--> Status History
```

---

## 4. Priority Model

CivicRoute uses a transparent 100-point model.

| Component | Maximum Score |
|---|---:|
| Location Risk | 50 |
| Problem Type | 30 |
| Severity | 20 |
| **Total** | **100** |

Location is intentionally given the highest weight because the same issue can have very different public impact depending on where it occurs.

Examples of nearby public-risk context include:

- Hospital / clinic
- School / college / university
- Traffic signal
- Bus station
- Marketplace

CivicRoute does **not** claim real-time crowd density.

---

## 5. AI-Assisted Complaint Analysis

The prototype uses **OpenAI CLIP ViT-B/32** through Hugging Face Transformers for local zero-shot image classification.

Supported examples include:

- Pothole / road damage
- Garbage dump / litter
- Overflowing dustbin
- Open manhole / open drain
- Blocked drain
- Sewage overflow
- Waterlogging
- Construction debris
- Burning waste
- Dead animal
- Broken streetlight
- Damaged footpath
- Fallen tree / road obstruction
- Broken traffic signal

Low-confidence or ambiguous evidence is routed to `REVIEW REQUIRED` instead of forcing an automatic decision.

---

## 6. Server-Side Location Context

The browser sends GPS coordinates to the backend.

The backend independently derives location context using public map services:

- OpenStreetMap
- Nominatim
- Overpass API

Frontend-provided address, risk score or priority values are not trusted as authoritative backend inputs.

If external location context cannot be sufficiently obtained, CivicRoute falls back to human review rather than silently assuming a result.

---

## 7. Jurisdiction Routing

The prototype includes a **versioned jurisdiction rule engine**.

Each rule can contain:

- Rule ID
- Jurisdiction
- Authority
- Effective-from date
- Effective-to date
- Source metadata
- Provenance status

Inactive or unverified rules are prevented from being automatically activated.

The current hackathon prototype uses locality-based rules for demonstration.

> Production deployment would require authoritative civic GIS boundary data. The current keyword rules must not be interpreted as official legal boundary polygons.

---

## 8. Duplicate Protection

CivicRoute uses two levels of duplicate handling.

### Exact duplicate

If the same image bytes are submitted again from a nearby location, CivicRoute can reuse the existing complaint instead of creating another record.

### Nearby recent duplicate candidate

If a recent unresolved complaint for the same detected issue exists very close to the new report, the new submission is flagged for review.

This is treated as a **duplicate candidate**, not automatically as spam.

---

## 9. Offline Support

CivicRoute supports weak-network and offline reporting.

Implemented using:

- Service Worker
- Cache API
- IndexedDB

When connectivity is lost:

```text
Citizen Report
     |
     v
IndexedDB Offline Queue
     |
     | Internet restored
     v
Automatic Sync
     |
     v
Backend Complaint ID
```

The application shell can also reopen from cache after it has been loaded online at least once.

Fresh online map tiles and external map-service requests may be unavailable while completely offline.

---

## 10. Citizen Tracking

Each accepted complaint receives a persistent ID such as:

```text
CR-20260920-ABC123
```

Citizens can use `/track` to view:

- Current status
- Detected issue
- Responsible authority
- Department
- Priority
- Location
- Assignment information
- Resolution information
- Complaint timeline

---

## 11. Staff Dashboard

Staff can use `/staff` to:

- View submitted complaints
- Filter complaints
- Search complaint IDs
- Inspect evidence
- Assign complaints
- Start work
- Update complaint status
- Resolve complaints
- View complaint history

The current staff interface is a hackathon prototype and does not yet include production-grade staff authentication or role-based access control.

---

## 12. Technology Stack

### Backend
- Python 3.10+
- Flask
- SQLite
- Pillow

### AI
- PyTorch
- Transformers
- OpenAI CLIP ViT-B/32

### Frontend
- HTML
- CSS
- JavaScript
- Leaflet

### Offline
- Service Worker
- Cache API
- IndexedDB

### Public Map Context
- OpenStreetMap
- Nominatim
- Overpass API

---

## 13. Repository Structure

```text
MechMavrix-submission/
|
|-- README.md
|-- resource.md
|-- ai.md
|-- requirements.txt
|
|-- docs/
|   |-- architecture.md
|   |-- constraints.md
|   |-- limitations.md
|   |-- setup.md
|
|-- src/
|   |-- app.py
|   |-- database.py
|   |-- jurisdiction.py
|   |-- boundary_sources.py
|   |-- location_engine.py
|   |
|   |-- templates/
|   |   |-- index.html
|   |   |-- track.html
|   |   `-- staff.html
|   |
|   `-- static/
|       |-- styles.css
|       |-- app.js
|       |-- track.js
|       |-- staff.js
|       |-- offline-db.js
|       |-- register-sw.js
|       `-- sw.js
|
`-- tests/
    |-- verify_system.py
    |-- verify_boundary_sources.py
    |-- verify_boundary_versioning.py
    `-- verify_ai_benchmark.py
```

---

## 14. Local Setup

### Create virtual environment

```bash
python -m venv .venv
```

### Activate on Windows

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start CivicRoute

```bash
python src/app.py
```

Open:

```text
http://127.0.0.1:5000
```

Citizen tracking:

```text
http://127.0.0.1:5000/track
```

Staff dashboard:

```text
http://127.0.0.1:5000/staff
```

---

## 15. Verification Tests

Core logic tests are available inside `tests/`.

Example:

```bash
python tests/verify_system.py
python tests/verify_boundary_sources.py
python tests/verify_boundary_versioning.py
```

The tests cover areas including:

- Jurisdiction routing
- Versioned rules
- Rule provenance
- Priority calculation
- Invalid input handling
- Review fallbacks

---

## 16. Safety-by-Design Decisions

CivicRoute deliberately avoids several unsafe assumptions:

- Citizens do not manually choose final priority
- Low-confidence AI output is not forced into automatic routing
- Nearby complaints are not automatically labelled as spam
- Public map data is not represented as perfect or complete
- Locality rules are not represented as official GIS boundaries
- Offline submissions receive a temporary local ID before server sync
- Routing decisions preserve complaint history for follow-through

---

## 17. Current Prototype Limitations

This HackMysuru MVP is not a production municipal deployment.

Important limitations include:

- Public OpenStreetMap coverage can be incomplete
- External Nominatim / Overpass services can be unavailable or rate-limited
- CLIP zero-shot confidence is not a calibrated civic-risk probability
- Current jurisdiction rules are demonstration rules, not legal GIS polygons
- SQLite is suitable for the MVP but not intended for large distributed deployment
- Staff authentication and RBAC are not yet implemented
- Exact-image hashing does not detect every edited or cropped duplicate
- Offline maps cannot fetch uncached internet map tiles

See `docs/limitations.md` for the detailed limitations.

---

## 18. Demo Links

### Local MVP
`http://127.0.0.1:5000`

### Public MVP
Will be added before final submission.

### Public GitHub Repository
Will be added before final submission.

---

## 19. HackMysuru Demonstration Flow

The recommended continuous demo is:

1. Open Citizen Portal
2. Upload civic issue photo
3. Capture GPS
4. Analyse and route complaint
5. Show automatic authority / department / priority
6. Show persistent complaint ID
7. Track complaint from Citizen Tracking
8. Open Staff Dashboard
9. Assign complaint
10. Update complaint status
11. Show history
12. Demonstrate bad / ambiguous input
13. Disconnect network
14. Submit complaint offline
15. Show IndexedDB pending queue
16. Reconnect
17. Show automatic sync

---

## 20. Team

**MechMavrix**

HackMysuru 1.0  
Civic Governance & Clean Mysuru

> Citizens report the evidence. CivicRoute handles the routing logic.
