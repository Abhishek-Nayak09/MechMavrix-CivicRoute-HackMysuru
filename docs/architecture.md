# CivicRoute Architecture

## 1. Overview

CivicRoute is a civic complaint routing MVP built for HackMysuru 1.0.

The system is designed around one principle:

> Citizens provide evidence and location; the system handles routing, prioritization, follow-through and review fallback.

The architecture separates:

- Citizen interaction
- Evidence validation
- AI-assisted image interpretation
- Server-side location context
- Jurisdiction routing
- Priority scoring
- Complaint persistence
- Staff workflow
- Offline queue and synchronization

---

## 2. High-Level Architecture

```text
Citizen Browser
    |
    | Photo + GPS + optional description
    v
Flask Backend
    |
    +--> Image validation
    |
    +--> Exact duplicate check
    |
    +--> Server-side location context
    |       |
    |       +--> Nominatim
    |       +--> Overpass API
    |
    +--> AI issue classification
    |
    +--> AI severity estimation
    |
    +--> Nearby duplicate candidate check
    |
    +--> Jurisdiction rule engine
    |
    +--> Department mapping
    |
    +--> Priority calculation
    |
    v
SQLite Complaint Database
    |
    +--> Citizen Tracking
    |
    +--> Staff Dashboard
    |
    +--> Complaint History
```

---

## 3. Frontend Components

### Citizen Portal

Main route:

`/`

Responsibilities:

- Select complaint photo
- Capture current GPS
- Show map preview
- Show online/offline state
- Submit complaint
- Display routing result
- Display complaint ID
- Display authority, department and priority

Primary files:

- `src/templates/index.html`
- `src/static/styles.css`
- `src/static/app.js`

---

### Citizen Tracking

Route:

`/track`

Responsibilities:

- Accept complaint ID
- Fetch complaint status
- Display authority and department
- Display priority
- Display assignment and resolution details
- Display complaint timeline

Primary files:

- `src/templates/track.html`
- `src/static/track.js`

---

### Staff Dashboard

Route:

`/staff`

Responsibilities:

- Display complaints
- Filter/search complaints
- Inspect evidence
- Assign complaint
- Update status
- Resolve complaint
- View complaint history

Primary files:

- `src/templates/staff.html`
- `src/static/staff.js`

---

## 4. Offline Architecture

CivicRoute uses two browser mechanisms.

### Service Worker

Files:

- `src/static/sw.js`
- `src/static/register-sw.js`

Purpose:

- Cache the app shell
- Allow the Citizen Portal to reopen after it has previously loaded online
- Serve cached static resources when connectivity is unavailable

---

### IndexedDB Queue

File:

`src/static/offline-db.js`

Purpose:

- Store pending complaint data locally
- Preserve:
  - Photo
  - GPS coordinates
  - GPS accuracy
  - Description
  - Temporary offline ID
  - Creation time

When internet returns, `app.js` automatically retries queued submissions.

Flow:

```text
Offline Citizen Submission
        |
        v
IndexedDB
        |
        | connectivity restored
        v
Automatic Sync
        |
        v
Flask Backend
        |
        v
Permanent CR-* Complaint ID
```

---

## 5. Backend Application Layer

Primary file:

`src/app.py`

Responsibilities:

- HTTP routes
- Complaint API
- Image validation
- AI inference orchestration
- Server-side location verification
- Routing orchestration
- Priority calculation
- Duplicate response handling
- Citizen tracking API
- Staff workflow APIs
- Service Worker delivery

---

## 6. Location Context Engine

Primary file:

`src/location_engine.py`

Purpose:

- Reverse-geocode GPS coordinates
- Query nearby public-risk places
- Calculate location risk
- Return location verification state

External public services:

- Nominatim
- Overpass API
- OpenStreetMap data

Location risk has a maximum contribution of:

`50 points`

Examples of nearby public-risk places:

- Hospital / clinic
- School / college / university
- Traffic signal
- Bus station
- Marketplace

If both address and nearby-risk context cannot be obtained, the system uses a safe review fallback instead of silently trusting frontend values.

---

## 7. Jurisdiction Engine

Primary files:

- `src/jurisdiction.py`
- `src/boundary_sources.py`

Responsibilities:

- Versioned jurisdiction rules
- Effective date handling
- Rule provenance checks
- Trusted source-domain validation
- Safe fallback to review queue

Rule structure includes:

- Rule ID
- Keywords
- Jurisdiction
- Authority
- Effective-from
- Effective-to
- Confidence
- Source title
- Source URL
- Verification status

The current prototype uses locality-based routing rules.

Production deployment should replace these demonstration rules with authoritative GIS boundary polygons and official civic boundary datasets.

---

## 8. AI Layer

Model:

`openai/clip-vit-base-patch32`

Framework:

- Hugging Face Transformers
- PyTorch

Tasks:

- Zero-shot civic issue classification
- Zero-shot visual severity estimation

The model is loaded lazily the first time image analysis is required.

---

## 9. AI Safety Gate

Automatic AI output is not accepted unconditionally.

The system checks:

- Top confidence
- Margin between best and second prediction
- Supported complaint type
- Severity confidence

If confidence conditions fail:

`REVIEW REQUIRED`

This prevents uncertain image evidence from being treated as authoritative.

---

## 10. Duplicate Detection

Primary file:

`src/database.py`

### Exact Duplicate

Uses:

- SHA-256 image hash
- Geographic proximity

If the exact same image is submitted again nearby, CivicRoute can reuse the existing complaint.

---

### Nearby Recent Duplicate Candidate

Uses:

- Same detected issue
- Geographic proximity
- Recent time window
- Unresolved status

This does not automatically label the citizen as spam.

It flags the submission for review.

---

## 11. Priority Engine

Priority is deterministic.

Maximum score:

`100`

Components:

```text
Location Risk    50
Problem Type     30
Severity         20
-------------------
Total           100
```

Priority bands:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- REVIEW REQUIRED

Human-review conditions override normal automatic priority labeling.

---

## 12. Persistence Layer

Primary file:

`src/database.py`

Database:

`SQLite`

Runtime location:

`data/civicroute.db`

Stored information includes:

- Complaint ID
- Photo path
- Image hash
- Description
- GPS coordinates
- GPS accuracy
- Address
- Location risk
- Issue type
- AI confidence
- Severity
- Authority
- Jurisdiction
- Department
- Priority
- Status
- Assignment
- Resolution
- Review flag
- Created/updated timestamps

---

## 13. Complaint History

CivicRoute stores complaint history separately from the main complaint row.

This allows status transitions and operational actions to remain visible.

Examples:

```text
CREATED
ASSIGNED
IN_PROGRESS
RESOLVED
```

History supports the hackathon goal of follow-through and visibility.

---

## 14. API Structure

### Citizen

`POST /api/analyze`

Creates or reuses a complaint after analysis.

`GET /api/complaints/<complaint_id>`

Returns citizen-safe complaint tracking information.

---

### Staff

`GET /api/staff/complaints`

Returns complaint list.

`GET /api/staff/complaints/<complaint_id>/history`

Returns complaint history.

`POST /api/staff/complaints/<complaint_id>/assign`

Assigns complaint.

`POST /api/staff/complaints/<complaint_id>/status`

Updates workflow status.

`POST /api/staff/complaints/<complaint_id>/resolve`

Resolves complaint.

---

## 15. Failure and Review Strategy

CivicRoute prefers explicit uncertainty over silent guessing.

Examples:

### AI uncertain

Result:

`REVIEW REQUIRED`

### Location context unavailable

Result:

`REVIEW REQUIRED`

### Jurisdiction rule unresolved

Result:

`Jurisdiction Review Queue`

### Nearby duplicate candidate

Result:

`FLAGGED_FOR_REVIEW`

---

## 16. Trust Boundaries

The frontend is not treated as authoritative for:

- Address
- Location-risk score
- Final priority
- Jurisdiction
- Department
- AI result

The backend recomputes the important decision inputs.

This reduces accidental or intentional client-side manipulation.

---

## 17. Current Prototype Security Boundary

The current hackathon MVP does not implement production-grade:

- Staff authentication
- Role-based access control
- Municipal SSO
- Rate limiting
- Abuse throttling
- Encrypted evidence storage
- Full audit identity

These are documented limitations, not hidden assumptions.

---

## 18. Scaling Direction

A production architecture could replace:

### SQLite

with:

- PostgreSQL
- PostGIS

### Local upload storage

with:

- Object storage

### Local AI inference

with:

- Dedicated inference service

### Locality keyword rules

with:

- Official GIS polygons
- PostGIS point-in-polygon queries

### Single Flask process

with:

- Production WSGI server
- Reverse proxy
- Background worker queue
- Horizontal scaling

---

## 19. Architecture Decision Summary

Key decisions:

1. Citizen does not choose department or priority.
2. Backend independently derives decision context.
3. Location receives the largest priority weight.
4. AI uncertainty triggers review.
5. Duplicate detection is evidence-based and conservative.
6. Jurisdiction rules are versioned.
7. Offline reports are queued locally instead of lost.
8. Complaint history is persistent.
9. Current GIS claims are explicitly limited to what the prototype can verify.

---

## 20. Architecture Principle

> CivicRoute automates routing where evidence is sufficient and exposes uncertainty where it is not.
