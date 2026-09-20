# MechMavrix CivicRoute - 1-Page Decision Log

**Hackathon:** HackMysuru 1.0  
**Track:** Civic Governance & Clean Mysuru  
**Primary Subproblem:** Routing

## Core decision
We focused deeply on **routing** instead of building a broad grievance portal. The citizen provides evidence and GPS; CivicRoute determines the issue, urgency, authority, department, and follow-through path.

## Key decisions and trade-offs

1. **Minimal citizen input** - Photo + GPS + optional description only.  
   **Why:** Citizens may not know jurisdiction, department, severity, or priority.  
   **Trade-off:** The backend must perform more verification and handle uncertainty.

2. **Server-side decision context** - The backend derives address, nearby-risk context, routing, and priority instead of trusting browser-calculated values.  
   **Why:** Reduces client-side manipulation and inconsistent decisions.  
   **Trade-off:** Depends on external map services while online.

3. **Transparent priority model: 50/30/20** - Location Risk 50, Problem Type 30, Severity 20.  
   **Why:** The same issue can be more dangerous near a hospital, school, traffic signal, bus station, or marketplace.  
   **Trade-off:** Weights are prototype policy values, not municipal policy.

4. **AI assists, humans handle uncertainty** - CLIP zero-shot classification estimates issue and severity; low-confidence cases become `REVIEW REQUIRED`.  
   **Why:** Avoids forcing uncertain AI outputs into automatic routing.  
   **Trade-off:** Some complaints require manual review.

5. **Versioned jurisdiction rules with provenance** - Rules include effective dates and source metadata.  
   **Why:** Civic boundaries and ownership can change.  
   **Trade-off:** Current MVP uses locality rules, not authoritative GIS polygons.

6. **Conservative duplicate handling** - Exact same image nearby can reuse an existing complaint; nearby recent matches are only flagged as duplicate candidates.  
   **Why:** Prevents duplicate inflation without accusing citizens of spam.  
   **Trade-off:** Edited/cropped images may bypass exact hashing.

7. **Offline-first complaint preservation** - Service Worker caches the app shell; IndexedDB stores pending reports and syncs after reconnection.  
   **Why:** Weak connectivity should not cause complaint loss.  
   **Trade-off:** Final AI/routing waits until the backend is reachable.

8. **Persistent follow-through** - Every accepted complaint gets a `CR-*` ID, citizen tracking, staff workflow, and history.  
   **Why:** Routing alone is not enough; visibility and accountability matter.  
   **Trade-off:** Current staff dashboard is demo-only and lacks production authentication/RBAC.

## What we deliberately did not claim
- No real-time crowd-density detection
- No official/legal GIS boundary proof
- No production AI accuracy percentage
- No production-grade staff authentication
- No claim of existing municipal-system integration

## Next production steps
Official GIS/PostGIS routing, authenticated staff roles, secure object storage, rate limiting, calibrated civic AI evaluation, SLA/escalation rules, and resolution evidence verification.
