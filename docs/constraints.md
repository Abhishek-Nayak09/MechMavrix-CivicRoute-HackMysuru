# CivicRoute Constraints

## 1. Hackathon Time Constraint

CivicRoute was developed as a HackMysuru 1.0 prototype within a short hackathon timeline.

This affected:

- Model evaluation depth
- Availability of official GIS datasets
- Production security hardening
- Deployment architecture
- UI polish
- Load testing
- Long-term reliability testing

The project therefore prioritizes a working, explainable MVP over a fully production-ready municipal platform.

---

## 2. Data Availability Constraint

Accurate civic routing ideally requires:

- Official municipal GIS boundaries
- Department ownership layers
- Zone/ward polygons
- Road ownership data
- Utility ownership data
- Updated jurisdiction effective dates

These datasets were not fully available in machine-readable form during the prototype timeline.

Therefore the current jurisdiction engine uses versioned locality-based demonstration rules with explicit provenance metadata.

These rules are not represented as official legal GIS polygons.

---

## 3. Public Map Data Constraint

CivicRoute uses public map data from OpenStreetMap-related services.

This introduces constraints such as:

- Missing points of interest
- Delayed edits
- Inconsistent tagging
- Incomplete addresses
- Different mapping quality across locations

The system therefore treats public-map context as assistive rather than guaranteed ground truth.

---

## 4. External Service Constraint

Location context depends on public internet services such as:

- Nominatim
- Overpass API

These services can experience:

- Network failure
- Rate limiting
- Timeout
- Partial results
- Temporary unavailability

If location context cannot be sufficiently verified, CivicRoute routes the complaint to human review instead of silently assuming a location-risk result.

---

## 5. AI Model Constraint

The prototype uses a general-purpose CLIP model.

Constraints include:

- No Mysuru-specific fine-tuning
- No municipal complaint-specific training
- No production calibration
- No complete benchmark dataset
- Possible confusion between visually similar issues

CivicRoute therefore uses confidence thresholds and a review fallback.

---

## 6. Device GPS Constraint

The system depends on browser geolocation.

GPS accuracy can vary because of:

- Indoor use
- Desktop computers
- Wi-Fi positioning
- Browser permission settings
- Device sensor quality
- Urban obstruction

CivicRoute records available GPS accuracy information but does not claim cryptographic proof that the user physically captured the image at that exact location.

---

## 7. Offline Constraint

Offline support is intentionally scoped to complaint preservation.

Implemented capabilities:

- Cached citizen app shell
- IndexedDB complaint queue
- Temporary offline complaint ID
- Automatic synchronization when connectivity returns

Offline limitations include:

- Fresh OpenStreetMap tiles may not load
- Server-side AI cannot run until reconnection
- Reverse geocoding cannot run until reconnection
- Jurisdiction routing cannot be finalized until sync
- Staff dashboard data is not intended for offline operation

---

## 8. Compute Constraint

AI inference currently runs in the same prototype application environment.

This creates constraints on:

- Startup time
- Memory use
- First-inference latency
- Concurrent request handling

The CLIP model is loaded lazily to avoid unnecessary startup cost.

A production system should separate AI inference from the main web process.

---

## 9. Database Constraint

The MVP uses SQLite.

Advantages:

- Simple
- Reliable for local prototype use
- No separate database server
- Fast development

Constraints:

- Limited multi-instance scaling
- Limited high-concurrency write workloads
- No native geospatial indexing comparable to PostGIS

A production deployment should migrate to PostgreSQL/PostGIS or an equivalent managed database.

---

## 10. Image Storage Constraint

Complaint images are stored in local filesystem storage in the prototype.

This is acceptable for local demonstration but unsuitable for distributed deployment because:

- Multiple app instances would not automatically share files
- Backup is manual
- Storage growth is unmanaged
- Access control is limited

Production deployment should use controlled object storage.

---

## 11. Duplicate Detection Constraint

Exact duplicate detection uses SHA-256 image hashing.

This reliably detects identical image bytes but does not automatically detect:

- Cropped versions
- Screenshots
- Resized copies
- Re-encoded images
- Different photographs of the same physical problem

The nearby-recent duplicate check is intentionally conservative and only flags possible duplicates for review.

---

## 12. Jurisdiction Change Constraint

Municipal boundaries and administrative responsibility can change over time.

CivicRoute addresses this structurally through:

- Effective-from dates
- Effective-to dates
- Versioned rule IDs
- Source metadata
- Provenance checks

However, the quality of routing still depends on receiving timely authoritative updates.

---

## 13. Priority Model Constraint

The 100-point priority model is a prototype policy model.

Weights:

- Location Risk: 50
- Problem Type: 30
- Severity: 20

The weights are intentionally transparent but have not been formally adopted or calibrated by a municipal authority.

Production deployment would require policy validation with civic officials and historical incident data.

---

## 14. Staff Access Constraint

The current staff dashboard is a hackathon demonstration interface.

It does not yet include:

- Authentication
- Role-based access control
- Municipal SSO
- Fine-grained permissions
- Identity-backed audit trails

It should not be exposed as a real operational municipal dashboard without these controls.

---

## 15. Abuse Prevention Constraint

The prototype does not yet include complete production anti-abuse controls such as:

- Rate limiting
- CAPTCHA
- Device reputation
- Account verification
- Phone OTP
- Image-forensics pipeline
- Automated coordinated-spam detection

Current protections focus on:

- Exact duplicate evidence
- Nearby-recent duplicate candidates
- Image validation
- Review fallback

---

## 16. Privacy Constraint

A real civic complaint system may process sensitive information including:

- Location
- Images
- Descriptions
- Potentially identifiable people in photos

The hackathon prototype does not implement a complete municipal privacy program.

Production deployment would require:

- Data minimization
- Retention policy
- Access control
- Encryption
- Privacy notice
- Consent handling
- Secure deletion
- Audit logging

---

## 17. Browser Constraint

Offline features depend on modern browser support for:

- Service Workers
- IndexedDB
- Fetch API
- Geolocation API

Behaviour may differ across browsers, private browsing modes, device policies and permission settings.

---

## 18. Network Constraint

The prototype assumes intermittent public internet access.

Poor connectivity can affect:

- Map tiles
- Reverse geocoding
- Overpass queries
- Initial AI model download
- Public deployment availability

Offline complaint queuing reduces data-loss risk but cannot eliminate every network dependency.

---

## 19. Testing Constraint

Core logic has automated verification tests.

However, the current test scope does not represent:

- Large-scale production load
- Full mobile-device matrix
- Complete browser compatibility
- Real municipal GIS truth validation
- Complete AI accuracy benchmark
- Security penetration testing

The test suite should be viewed as MVP verification, not production certification.

---

## 20. Deployment Constraint

The local Flask development server is only for development and demonstration.

It is not intended as a production WSGI deployment.

Production hosting should include:

- Production WSGI server
- HTTPS
- Reverse proxy or managed platform
- Secure secrets management
- Monitoring
- Backups
- Centralized logging
- Database migration strategy

---

## 21. Core Constraint Principle

When CivicRoute lacks enough evidence to make a trustworthy automatic decision, the system should expose uncertainty and route the case to review rather than fabricate confidence.
