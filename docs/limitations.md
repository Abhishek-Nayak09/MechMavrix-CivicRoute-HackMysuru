# CivicRoute Limitations

## 1. Prototype Scope

CivicRoute is a HackMysuru 1.0 MVP, not a production municipal grievance platform.

It demonstrates:

- Evidence-based complaint submission
- AI-assisted issue classification
- Severity estimation
- Location-context scoring
- Jurisdiction routing
- Department routing
- Priority scoring
- Duplicate protection
- Citizen tracking
- Staff workflow
- Offline queue and synchronization

The current implementation should be evaluated as a functional prototype.

---

## 2. Jurisdiction Accuracy

The current prototype uses locality-based jurisdiction rules for demonstration.

These rules:

- Are versioned
- Include effective dates
- Include provenance metadata
- Can be disabled if unverified

However, they are **not official legal GIS boundary polygons**.

Therefore CivicRoute must not claim that its current locality rules prove legal administrative ownership at every coordinate.

A production deployment should use authoritative civic GIS data and point-in-polygon checks.

---

## 3. Public Map Coverage

CivicRoute uses OpenStreetMap-derived services for address and nearby public-risk context.

OpenStreetMap may have:

- Missing places
- Incomplete tags
- Old information
- Inconsistent naming
- Different coverage quality across neighborhoods

A location being absent from OSM does not prove that the real-world feature is absent.

---

## 4. Nominatim and Overpass Availability

Server-side location context depends on external public services.

Possible failure modes include:

- API timeout
- Rate limiting
- Temporary outage
- Network interruption
- Partial response

When this happens, CivicRoute uses a review fallback instead of inventing a fully verified location result.

---

## 5. AI Classification Accuracy

CivicRoute uses CLIP zero-shot image classification.

The model can misclassify:

- Poor-quality photos
- Night-time photos
- Blurry images
- Occluded issues
- Unusual civic problems
- Images containing multiple issues
- Visually similar complaint types

The project does not claim production-level AI accuracy.

---

## 6. Severity Estimation

Visual severity is estimated from the uploaded image.

An image may not reveal:

- Full physical extent
- Traffic impact
- Depth
- Smell
- Water contamination
- Underground damage
- Time duration
- Hidden danger

Therefore severity estimation is assistive and confidence-gated.

---

## 7. GPS Is Not Cryptographic Proof

Browser GPS coordinates are useful routing evidence, but the prototype does not provide cryptographic proof that:

- The user physically captured the image at that coordinate
- The GPS reading was not spoofed
- The photo timestamp matches the submission time

The application records available geolocation information but does not claim forensic location authenticity.

---

## 8. Location-Risk Score

Nearby public-risk context contributes up to 50 points.

The prototype checks categories such as:

- Hospital / clinic
- School / college / university
- Traffic signal
- Bus station
- Marketplace

This is not a real-time crowd-density system.

The score reflects mapped nearby public-risk features, not the actual number of people present at submission time.

---

## 9. Priority Policy

The priority model is:

- Location Risk: 50
- Problem Type: 30
- Severity: 20

This weighting is a transparent prototype policy.

It has not been formally approved or statistically calibrated by a municipal authority.

Production deployment should validate weights using:

- Civic officials
- Historical complaints
- Response-time data
- Safety outcomes
- Public policy requirements

---

## 10. Duplicate Detection

Exact duplicate detection uses SHA-256 image hashes.

This works for identical image bytes but may not detect:

- Cropped images
- Resized images
- Screenshots
- Recompressed images
- Different photos of the same physical issue

Nearby-recent duplicate detection is intentionally treated as a candidate only.

It does not prove spam or malicious reporting.

---

## 11. Offline Map Behaviour

The Citizen Portal can reopen from a cached app shell after a prior successful online load.

However, when fully offline:

- Fresh map tiles may not load
- Reverse geocoding cannot complete
- Nearby-risk queries cannot complete
- AI analysis cannot run on the server
- Final routing waits for synchronization

The complaint itself is preserved locally through IndexedDB.

---

## 12. First-Time Offline Use

The Service Worker must be installed while the app is online at least once.

A device that has never opened CivicRoute before cannot load the full web application offline for the first time.

---

## 13. Offline Queue Storage

Offline complaints are stored in the browser's IndexedDB.

Possible risks include:

- Browser storage being manually cleared
- Private browsing restrictions
- Storage eviction
- Device reset
- Unsupported browser behaviour

The offline queue is resilient for an MVP but is not equivalent to guaranteed device-level durable storage.

---

## 14. Staff Dashboard Security

The current staff dashboard is designed for hackathon demonstration.

It does not yet include production-grade:

- Authentication
- Role-based access control
- Municipal SSO
- Per-user permissions
- Session hardening
- Identity-backed audit trails

The current `/staff` workflow should not be exposed as a real operational municipal system without these controls.

---

## 15. API Abuse Protection

The prototype does not yet implement full protections such as:

- Rate limiting
- CAPTCHA
- OTP verification
- Account reputation
- Request throttling
- Bot mitigation
- IP reputation
- Automated abuse scoring

These are important before public production deployment.

---

## 16. Privacy and Personal Data

Complaint photos and locations can contain sensitive information.

The prototype does not implement a complete production privacy program.

A real deployment would require:

- Privacy notice
- Data minimization
- Consent handling
- Retention policy
- Encryption
- Access controls
- Secure deletion
- Legal compliance review

---

## 17. Image Content Safety

The prototype validates that the upload is an image, but it does not yet include a dedicated moderation pipeline for:

- Faces
- Vehicle registration plates
- Graphic content
- Private documents
- Sensitive personal information

Production deployment should include appropriate privacy and moderation safeguards.

---

## 18. Local File Storage

Uploaded complaint images are stored on the local filesystem.

This is suitable for a local MVP, but it creates production limitations:

- No distributed file sharing
- No managed backup
- No lifecycle policy
- No scalable object storage
- Limited access control

Production systems should use secured object storage.

---

## 19. SQLite

SQLite is used for simplicity.

Limitations include:

- Limited multi-instance scaling
- Limited high-concurrency writes
- No production geospatial capabilities comparable to PostGIS
- Local-file dependency

A production version should use a managed relational database, preferably with geospatial support.

---

## 20. Flask Development Server

Running:

`python src/app.py`

starts Flask's development server.

It is suitable for development/demo use only.

Production deployment should use:

- Production WSGI server
- HTTPS
- Secure reverse proxy
- Monitoring
- Central logging
- Secrets management

---

## 21. AI Model Download

The first AI analysis may require the model to be downloaded if it is not already cached.

This can increase:

- First-run latency
- Setup time
- Network usage
- Disk usage

Production deployment should pre-package or pre-cache the required model.

---

## 22. AI Benchmark

The repository contains AI benchmark scaffolding, but the evaluation dataset is not complete enough to support a reliable overall accuracy claim.

The project therefore does **not** claim a specific production AI accuracy percentage.

---

## 23. Complaint Categories

The current AI prompt set covers a selected list of civic issues.

Real municipal systems may need many additional categories such as:

- Water-supply problems
- Illegal encroachment
- Public toilet maintenance
- Animal-control issues
- Park maintenance
- Signage damage
- Utility-specific complaints

Unsupported or ambiguous cases should be reviewed manually.

---

## 24. Department Mapping

Issue-to-department mapping is a prototype routing map.

Actual civic responsibility may depend on:

- Ward
- Road ownership
- Utility ownership
- Contractor responsibility
- State agency ownership
- Special development authority
- Temporary administrative orders

Production mapping should be sourced from authoritative administrative data.

---

## 25. Authority Office Map

Where an exact authority office location is unavailable, the prototype may use an authority-area reference rather than claiming an exact office coordinate.

Any approximate fallback should be clearly represented as approximate.

---

## 26. Complaint Status Workflow

The MVP supports status tracking and history, but it does not yet implement:

- SLA timers
- Escalation hierarchy
- Supervisor approval
- Reopen workflow
- Citizen satisfaction feedback
- Inter-department transfer workflow
- Official closure verification

These are natural production extensions.

---

## 27. Resolution Verification

A staff member can mark a complaint resolved and provide a note.

The current prototype does not require:

- After-resolution photo
- Citizen confirmation
- Supervisor verification
- Geo-tagged completion evidence

Therefore "resolved" in the prototype represents the workflow state entered by staff.

---

## 28. Browser Compatibility

The prototype relies on modern browser features.

Older or restricted browsers may have limited support for:

- Service Workers
- IndexedDB
- Geolocation
- Fetch API
- Camera capture

The primary demo environment should use a current Chromium-based browser.

---

## 29. Mobile Behaviour

The web UI is responsive, but the project has not undergone exhaustive testing across:

- Android versions
- iOS versions
- Screen sizes
- Low-memory devices
- Browser permission policies

Mobile production readiness requires a broader device matrix.

---

## 30. No Real-Time Crowd Density

CivicRoute does not use:

- Live CCTV analytics
- Telecom-density data
- Real-time pedestrian counts
- Real-time traffic density feeds

Any location-risk result is based on mapped public-risk context and the prototype scoring rules.

---

## 31. No Claim of Official Municipal Integration

The current HackMysuru prototype is not represented as already integrated with:

- Mysuru City Corporation production systems
- Janaspandana production systems
- Official municipal staff accounts
- Government GIS backend
- Official grievance ticket database

It demonstrates how such integration could be structured.

---

## 32. Production Validation Needed

Before deployment, CivicRoute should undergo:

- Security review
- Privacy review
- Accessibility testing
- Load testing
- GIS validation
- AI benchmark evaluation
- Civic-policy validation
- Staff workflow testing
- Citizen usability testing
- Disaster-recovery planning

---

## 33. Limitation Principle

CivicRoute intentionally exposes uncertainty rather than hiding it.

> If the system cannot verify enough evidence to route safely, it should request human review instead of inventing certainty.
