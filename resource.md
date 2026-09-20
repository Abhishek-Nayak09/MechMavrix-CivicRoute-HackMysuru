# resource.md

# MechMavrix CivicRoute — External Resources

This file records the external datasets, APIs, libraries, models, documentation, and public references used while building the HackMysuru 1.0 prototype.

---

## 1. OpenStreetMap

**Purpose:** Base map data and public geographic context.

**Used for:**
- Map display
- Reverse-geocoded locality context
- Nearby public-risk place discovery through Overpass

**Website:** https://www.openstreetmap.org/

**Important limitation:** OpenStreetMap is community-maintained and may be incomplete or outdated in some locations. CivicRoute does not treat OSM data as an official municipal boundary source.

---

## 2. Nominatim

**Purpose:** Reverse geocoding GPS coordinates into a human-readable location.

**Used for:**
- Converting submitted latitude/longitude into locality/address context
- Server-side location verification workflow

**Documentation:** https://nominatim.org/release-docs/latest/

**Important limitation:** Nominatim is an external public service and may be rate-limited, unavailable, or return incomplete address information.

---

## 3. Overpass API

**Purpose:** Query OpenStreetMap features around the complaint location.

**Used for:**
- Detecting nearby hospitals/clinics
- Schools/colleges/universities
- Traffic signals
- Bus stations
- Marketplaces

These nearby features contribute to CivicRoute's location-risk score.

**Website:** https://overpass-api.de/

**Documentation:** https://wiki.openstreetmap.org/wiki/Overpass_API

**Important limitation:** Availability and completeness depend on the underlying OpenStreetMap data and the public Overpass service.

---

## 4. OpenAI CLIP ViT-B/32

**Purpose:** Zero-shot image classification for complaint evidence.

**Used for:**
- Civic issue type estimation
- Visual severity estimation

**Model:** `openai/clip-vit-base-patch32`

**Hugging Face model page:**  
https://huggingface.co/openai/clip-vit-base-patch32

**Important limitation:** CLIP is a general-purpose vision-language model. Its zero-shot scores are not calibrated civic-risk probabilities. Ambiguous outputs are routed to human review.

---

## 5. Hugging Face Transformers

**Purpose:** Run the CLIP model locally through the zero-shot image classification pipeline.

**Website:** https://huggingface.co/docs/transformers/

**Used package:** `transformers`

---

## 6. PyTorch

**Purpose:** ML runtime used by the Transformers/CLIP pipeline.

**Website:** https://pytorch.org/

---

## 7. Flask

**Purpose:** Python web backend and API server.

**Used for:**
- Citizen portal
- Complaint submission API
- Citizen tracking
- Staff dashboard APIs
- Service Worker delivery
- Uploaded evidence serving

**Website:** https://flask.palletsprojects.com/

---

## 8. SQLite

**Purpose:** Local persistent complaint database for the MVP.

**Used for:**
- Complaint records
- Complaint IDs
- Status tracking
- Assignment
- Resolution history
- Duplicate checks

**Website:** https://www.sqlite.org/

**Important limitation:** SQLite is appropriate for this hackathon MVP but is not the intended database architecture for a large multi-instance municipal deployment.

---

## 9. Pillow

**Purpose:** Image validation and preprocessing before AI analysis and storage.

**Website:** https://python-pillow.org/

---

## 10. Leaflet

**Purpose:** Interactive map rendering in the browser.

**Website:** https://leafletjs.com/

**Used for:**
- Citizen GPS preview
- Complaint result map
- Authority/location visualization

---

## 11. Browser Service Worker API

**Purpose:** Offline app-shell caching.

**Used for:**
- Reopening the Citizen Portal after it has previously loaded online
- Serving cached frontend files when connectivity is lost

**Reference:** https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API

---

## 12. IndexedDB

**Purpose:** Store unsent complaints locally when the device is offline.

**Used for:**
- Temporary offline complaint IDs
- Photo + GPS + description queue
- Automatic re-submission after connectivity returns

**Reference:** https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API

---

## 13. Mysuru District Official Portal

**Purpose:** Public-government reference used as provenance metadata for the current demonstration jurisdiction rule set.

**Website:** https://mysore.nic.in/

**Important limitation:** The current CivicRoute MVP does not contain authoritative legal GIS boundary polygons. Locality keyword rules are demonstration routing rules and must not be interpreted as official municipal boundary definitions.

---

## 14. Karnataka Government / Public GIS References

The jurisdiction-rule provenance validator is designed to accept references from trusted government domains such as:

- `karnataka.gov.in`
- `mysore.nic.in`
- `kgis.ksrsac.in`
- `sujala3lri.karnataka.gov.in`

The current prototype demonstrates provenance validation and versioned-rule activation logic.

---

## 15. AI Assistance Disclosure

Generative AI tools were used during development for:
- Brainstorming architecture
- Reviewing code structure
- Drafting documentation
- Debugging support
- Test-case planning

All generated material was reviewed, adapted, and integrated by the team.

Detailed disclosure is maintained in:

`ai.md`

---

## 16. Original Team Work

The following project-specific logic was implemented for CivicRoute:

- 100-point priority model
- Location-risk weighting
- Issue-to-department routing
- Versioned jurisdiction rules
- Provenance validation
- Human-review fallback
- Exact-image duplicate protection
- Nearby-recent duplicate candidate detection
- Complaint persistence and history
- Citizen tracking interface
- Staff dashboard
- Offline IndexedDB queue
- Service Worker offline app shell
- Automatic reconnect synchronization

---

## 17. Licensing and Responsible Use

CivicRoute is a hackathon prototype.

External libraries, models, map services and datasets remain subject to their respective licenses, attribution requirements, usage policies and service limits.

No external public-data source is represented by CivicRoute as guaranteed complete, legally authoritative, or real-time unless explicitly stated by that source.


---

## 18. HackMysuru Demo Video

**Video duration:** 08:41

**Google Drive:**  
https://drive.google.com/file/d/1HDRdpDZ2PZ-qCRcw6lXBFex7jPvzMUnD/view?usp=sharing

**SHA-256:**  
`4AC00459BD68FC47F7C4915D9E0672A1E07DD7B2A39DFD77DF3406F80A9FA80C`

**SHA-256 first 16 characters:**  
`4AC00459BD68FC47`

### Video Chapters

- `00:00` — CivicRoute problem and solution overview
- `00:45` — Citizen complaint submission: photo + GPS
- `02:00` — AI analysis, routing and priority result
- `03:20` — Complaint ID and citizen tracking
- `04:15` — Staff dashboard and complaint follow-through
- `05:25` — Duplicate / uncertainty handling
- `06:15` — Offline complaint queue demonstration
- `07:10` — Reconnect and automatic synchronization
- `07:50` — Public GitHub repository, architecture and documentation
- `08:30` — Closing summary

> Chapter timestamps are provided to help judges navigate the continuous demonstration video.


---

## 19. Submission Deliverables

**Live Working MVP:**  
https://meditation-eden-jump-news.trycloudflare.com

> **Note:** If the live MVP is temporarily unavailable during review, kindly contact a Team MechMavrix member at **+91 63605 18036**. We will make the demo available as soon as possible.

**Demo Video:**  
https://drive.google.com/file/d/1HDRdpDZ2PZ-qCRcw6lXBFex7jPvzMUnD/view?usp=sharing

**Video SHA-256 first 16:** `4AC00459BD68FC47`

**1-Page Decision Log:**  
https://github.com/Abhishek-Nayak09/MechMavrix-CivicRoute-HackMysuru/blob/main/decision-log.pdf

**Decision Log SHA-256 first 16:** `7E60F43A1A40BB34`

**Max 10-Slide Presentation Deck:**  
https://github.com/Abhishek-Nayak09/MechMavrix-CivicRoute-HackMysuru/blob/main/presentation.pdf

**Presentation SHA-256 first 16:** `D328E2FECCC04FB6`
