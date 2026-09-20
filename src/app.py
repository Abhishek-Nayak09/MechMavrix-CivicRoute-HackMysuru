from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    url_for
)

from PIL import (
    Image,
    UnidentifiedImageError
)

from jurisdiction import (
    resolve_jurisdiction
)

from location_engine import (
    verify_location_context
)

from database import (
    init_db,
    create_complaint,
    get_complaint,
    get_complaint_history,
    list_complaints,
    update_complaint_status,
    assign_complaint,
    resolve_complaint,
    find_exact_duplicate,
    find_nearby_duplicate,
    UPLOAD_DIR,
    PROJECT_ROOT
)

import io
import os
import uuid
import hashlib


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)

init_db()


# ============================================================
# AI CONFIDENCE
# ============================================================

ISSUE_MIN_CONFIDENCE = 0.18
ISSUE_MIN_MARGIN = 0.02

SEVERITY_MIN_CONFIDENCE = 0.30
SEVERITY_MIN_MARGIN = 0.02


# ============================================================
# SUPPORTED ISSUES
# ============================================================

ISSUE_PROMPTS = {

    "Pothole / Road Damage":
        "a pothole, broken asphalt, cracked road or badly damaged road surface",

    "Garbage Dump / Litter":
        "garbage, litter or solid waste dumped on a street, roadside or public place",

    "Overflowing / Unclean Dustbin":
        "an overflowing public garbage bin or dustbin with waste spilling outside",

    "Open Manhole / Open Drain":
        "an uncovered manhole, missing manhole cover or dangerous open roadside drain",

    "Blocked / Overflowing Drain":
        "a blocked dirty drain filled with waste, sludge or overflowing water",

    "Sewage / Storm-Water Overflow":
        "sewage, wastewater or storm water overflowing onto a public road",

    "Stagnant Water / Waterlogging":
        "stagnant water, waterlogging or a flooded public road",

    "Construction / Demolition Debris":
        "construction rubble, demolition waste, bricks, concrete or debris dumped in a public area",

    "Burning Garbage / Waste":
        "garbage, plastic or waste burning in an open public area with visible fire or smoke",

    "Dead Animal":
        "a dead animal lying on a road, roadside or public place",

    "Broken Streetlight":
        "a damaged, broken, fallen or non-working streetlight pole or street lamp",

    "Damaged Footpath / Public Path":
        "a broken footpath, damaged pavement, unsafe sidewalk or damaged pedestrian path",

    "Fallen Tree / Road Obstruction":
        "a fallen tree, large branch or physical obstruction blocking a public road",

    "Broken Traffic Signal":
        "a damaged, broken or non-working traffic signal at a road junction",

    "No Clear Civic Issue":
        "a normal clean road, indoor scene, unrelated object or image with no obvious civic complaint"
}


# ============================================================
# DEPARTMENT MAPPING
# ============================================================

DEPARTMENT_MAP = {

    "Pothole / Road Damage":
        "Engineering / Roads",

    "Garbage Dump / Litter":
        "Solid Waste Management",

    "Overflowing / Unclean Dustbin":
        "Solid Waste Management",

    "Open Manhole / Open Drain":
        "Drainage / Engineering",

    "Blocked / Overflowing Drain":
        "Drainage / Engineering",

    "Sewage / Storm-Water Overflow":
        "Underground Drainage / Engineering",

    "Stagnant Water / Waterlogging":
        "Storm-Water Drainage / Engineering",

    "Construction / Demolition Debris":
        "Solid Waste / C&D Waste Management",

    "Burning Garbage / Waste":
        "Solid Waste Management / Environmental Health",

    "Dead Animal":
        "Solid Waste / Sanitation",

    "Broken Streetlight":
        "Electrical / Street Lighting",

    "Damaged Footpath / Public Path":
        "Engineering / Roads & Footpaths",

    "Fallen Tree / Road Obstruction":
        "Horticulture / Engineering",

    "Broken Traffic Signal":
        "Traffic Engineering / Electrical",

    "No Clear Civic Issue":
        "No Automatic Department",

    "Manual Review Required":
        "Civic Control Room / Manual Review"
}


# ============================================================
# PROBLEM SCORE — MAX 30
# ============================================================

PROBLEM_PRIORITY_SCORE = {

    "Pothole / Road Damage": 27,
    "Garbage Dump / Litter": 20,
    "Overflowing / Unclean Dustbin": 18,
    "Open Manhole / Open Drain": 30,
    "Blocked / Overflowing Drain": 26,
    "Sewage / Storm-Water Overflow": 28,
    "Stagnant Water / Waterlogging": 26,
    "Construction / Demolition Debris": 22,
    "Burning Garbage / Waste": 30,
    "Dead Animal": 24,
    "Broken Streetlight": 20,
    "Damaged Footpath / Public Path": 21,
    "Fallen Tree / Road Obstruction": 30,
    "Broken Traffic Signal": 28,
    "No Clear Civic Issue": 0,
    "Manual Review Required": 0
}


# ============================================================
# SEVERITY SCORE — MAX 20
# ============================================================

SEVERITY_PRIORITY_SCORE = {

    "LOW": 5,
    "MEDIUM": 10,
    "HIGH": 16,
    "CRITICAL": 20,
    "UNVERIFIED": 0
}


# ============================================================
# AI MODEL
# ============================================================

vision_classifier = None


def get_vision_classifier():

    global vision_classifier

    if vision_classifier is None:

        from transformers import pipeline

        print(
            "Loading CivicRoute vision model..."
        )

        vision_classifier = pipeline(
            task="zero-shot-image-classification",
            model="openai/clip-vit-base-patch32",
            device=-1
        )

        print(
            "Vision model ready."
        )

    return vision_classifier


# ============================================================
# ISSUE DETECTION
# ============================================================

def detect_issue(image):

    classifier = (
        get_vision_classifier()
    )

    results = classifier(
        image,
        candidate_labels=
            list(
                ISSUE_PROMPTS.values()
            )
    )

    if not results:

        return {
            "issue":
                "Manual Review Required",

            "confidence":
                0.0,

            "margin":
                0.0,

            "review_required":
                True,

            "reason":
                "Vision model returned no classification."
        }

    best = results[0]

    second = (
        results[1]
        if len(results) > 1
        else {
            "score": 0.0
        }
    )

    best_prompt = (
        best["label"]
    )

    best_score = float(
        best["score"]
    )

    second_score = float(
        second["score"]
    )

    margin = (
        best_score -
        second_score
    )

    detected_issue = None

    for (
        issue_name,
        prompt
    ) in ISSUE_PROMPTS.items():

        if prompt == best_prompt:

            detected_issue = (
                issue_name
            )

            break

    if detected_issue is None:

        detected_issue = (
            "Manual Review Required"
        )

    if (
        best_score <
        ISSUE_MIN_CONFIDENCE

        or

        margin <
        ISSUE_MIN_MARGIN
    ):

        return {
            "issue":
                "Manual Review Required",

            "confidence":
                best_score,

            "margin":
                margin,

            "review_required":
                True,

            "reason":
                "Photo is ambiguous or AI confidence is too low."
        }

    if (
        detected_issue ==
        "No Clear Civic Issue"
    ):

        return {
            "issue":
                detected_issue,

            "confidence":
                best_score,

            "margin":
                margin,

            "review_required":
                True,

            "reason":
                "No clear supported civic issue was detected."
        }

    return {
        "issue":
            detected_issue,

        "confidence":
            best_score,

        "margin":
            margin,

        "review_required":
            False,

        "reason":
            "Photo passed automatic issue classification."
    }


# ============================================================
# SEVERITY DETECTION
# ============================================================

def detect_severity(
    image,
    detected_issue
):

    if detected_issue in [
        "Manual Review Required",
        "No Clear Civic Issue"
    ]:

        return {
            "severity":
                "UNVERIFIED",

            "confidence":
                0.0,

            "margin":
                0.0,

            "review_required":
                True,

            "reason":
                "Severity cannot be estimated until evidence is verified."
        }

    classifier = (
        get_vision_classifier()
    )

    severity_prompts = {

        "LOW":
            f"a minor {detected_issue} affecting only a small area with little immediate public danger",

        "MEDIUM":
            f"a moderate {detected_issue} needing municipal attention without major immediate danger",

        "HIGH":
            f"a severe {detected_issue} creating significant public danger, obstruction or service disruption",

        "CRITICAL":
            f"a critical {detected_issue} creating immediate danger, major blockage or serious threat to public safety"
    }

    results = classifier(
        image,
        candidate_labels=
            list(
                severity_prompts.values()
            )
    )

    if not results:

        return {
            "severity":
                "UNVERIFIED",

            "confidence":
                0.0,

            "margin":
                0.0,

            "review_required":
                True,

            "reason":
                "Severity model returned no result."
        }

    best = results[0]

    second = (
        results[1]
        if len(results) > 1
        else {
            "score": 0.0
        }
    )

    best_prompt = (
        best["label"]
    )

    best_score = float(
        best["score"]
    )

    second_score = float(
        second["score"]
    )

    margin = (
        best_score -
        second_score
    )

    detected_severity = None

    for (
        severity,
        prompt
    ) in severity_prompts.items():

        if prompt == best_prompt:

            detected_severity = (
                severity
            )

            break

    if detected_severity is None:

        detected_severity = (
            "UNVERIFIED"
        )

    if (
        best_score <
        SEVERITY_MIN_CONFIDENCE

        or

        margin <
        SEVERITY_MIN_MARGIN
    ):

        return {
            "severity":
                "UNVERIFIED",

            "confidence":
                best_score,

            "margin":
                margin,

            "review_required":
                True,

            "reason":
                "Visual severity is ambiguous."
        }

    return {
        "severity":
            detected_severity,

        "confidence":
            best_score,

        "margin":
            margin,

        "review_required":
            False,

        "reason":
            "Visual severity passed confidence checks."
    }


# ============================================================
# PRIORITY
# ============================================================

def calculate_priority(
    location_score,
    detected_issue,
    detected_severity,
    review_required
):

    problem_score = (
        PROBLEM_PRIORITY_SCORE.get(
            detected_issue,
            0
        )
    )

    severity_score = (
        SEVERITY_PRIORITY_SCORE.get(
            detected_severity,
            0
        )
    )

    total_score = (
        int(
            location_score
        )
        +
        problem_score
        +
        severity_score
    )

    total_score = max(
        0,
        min(
            total_score,
            100
        )
    )

    if review_required:

        priority = (
            "REVIEW REQUIRED"
        )

    elif total_score >= 80:

        priority = (
            "CRITICAL"
        )

    elif total_score >= 65:

        priority = (
            "HIGH"
        )

    elif total_score >= 45:

        priority = (
            "MEDIUM"
        )

    else:

        priority = (
            "LOW"
        )

    return {
        "priority":
            priority,

        "score":
            total_score,

        "location_score":
            int(
                location_score
            ),

        "problem_score":
            problem_score,

        "severity_score":
            severity_score
    }


# ============================================================
# SAVE PHOTO
# ============================================================

def save_complaint_photo(image):

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    filename = (
        f"{uuid.uuid4().hex}.jpg"
    )

    absolute_path = (
        os.path.join(
            UPLOAD_DIR,
            filename
        )
    )

    image.save(
        absolute_path,
        format="JPEG",
        quality=90,
        optimize=True
    )

    relative_path = (
        os.path.relpath(
            absolute_path,
            PROJECT_ROOT
        )
        .replace(
            "\\",
            "/"
        )
    )

    return relative_path


# ============================================================
# EXACT DUPLICATE RESPONSE
# ============================================================

def build_existing_complaint_response(
    existing,
    duplicate_type,
    duplicate_reason,
    duplicate_distance
):

    complaint = dict(
        existing
    )

    return jsonify({

        "success":
            True,

        "complaint": {

            "complaint_id":
                complaint[
                    "complaint_id"
                ],

            "status":
                complaint[
                    "status"
                ],

            "created_at":
                complaint[
                    "created_at"
                ]
        },

        "duplicate": {

            "detected":
                True,

            "type":
                duplicate_type,

            "action":
                "EXISTING_COMPLAINT_REUSED",

            "existing_complaint_id":
                complaint[
                    "complaint_id"
                ],

            "distance_metres":
                duplicate_distance,

            "reason":
                duplicate_reason
        },

        "gps": {

            "latitude":
                complaint[
                    "latitude"
                ],

            "longitude":
                complaint[
                    "longitude"
                ],

            "accuracy":
                complaint[
                    "gps_accuracy"
                ]
        },

        "location": {

            "address":
                complaint[
                    "detected_address"
                ],

            "risk":
                complaint[
                    "location_risk"
                ],

            "score":
                complaint[
                    "location_score"
                ],

            "verified_by_server":
                True,

            "address_verified":
                True,

            "risk_verified":
                True,

            "nearby":
                []
        },

        "vision": {

            "issue":
                complaint[
                    "detected_issue"
                ],

            "issue_confidence":
                round(
                    float(
                        complaint[
                            "issue_confidence"
                        ]
                        or 0
                    ),
                    1
                ),

            "issue_margin":
                None,

            "severity":
                complaint[
                    "detected_severity"
                ],

            "severity_confidence":
                round(
                    float(
                        complaint[
                            "severity_confidence"
                        ]
                        or 0
                    ),
                    1
                ),

            "severity_margin":
                None,

            "review_required":
                bool(
                    complaint.get(
                        "review_required",
                        0
                    )
                )
        },

        "routing": {

            "authority":
                complaint[
                    "responsible_authority"
                ],

            "department":
                complaint[
                    "department"
                ],

            "jurisdiction":
                complaint[
                    "jurisdiction"
                ],

            "jurisdiction_resolved":
                (
                    complaint[
                        "responsible_authority"
                    ]
                    !=
                    "Jurisdiction Review Queue"
                ),

            "jurisdiction_confidence":
                complaint[
                    "jurisdiction_confidence"
                ],

            "rule_id":
                complaint[
                    "jurisdiction_rule_id"
                ],

            "effective_date":
                None,

            "source_verified":
                None
        },

        "priority": {

            "level":
                complaint[
                    "priority"
                ],

            "score":
                complaint[
                    "priority_score"
                ],

            "components": {

                "location":
                    complaint[
                        "location_score"
                    ],

                "problem":
                    PROBLEM_PRIORITY_SCORE.get(
                        complaint[
                            "detected_issue"
                        ],
                        0
                    ),

                "severity":
                    SEVERITY_PRIORITY_SCORE.get(
                        complaint[
                            "detected_severity"
                        ],
                        0
                    )
            },

            "explanation": (
                "Duplicate protection detected the same "
                "photo evidence from this area. CivicRoute "
                "reused the existing complaint instead of "
                "creating another record."
            )
        }
    })


# ============================================================
# CITIZEN PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# CITIZEN TRACKING PAGE
# ============================================================

@app.route("/track")
def track_page():

    return render_template(
        "track.html"
    )


# ============================================================
# STAFF DASHBOARD PAGE
# ============================================================

@app.route("/staff")
def staff_dashboard():

    return render_template(
        "staff.html"
    )


# ============================================================
# SERVICE WORKER
#
# IMPORTANT:
# Served from root /sw.js so its scope can cover:
# /
# /track
# /staff
# /static/*
# ============================================================

@app.route("/sw.js")
def service_worker():

    response = send_from_directory(
        app.static_folder,
        "sw.js",
        mimetype="application/javascript"
    )

    response.headers[
        "Service-Worker-Allowed"
    ] = "/"

    response.headers[
        "Cache-Control"
    ] = "no-cache"

    return response


# ============================================================
# PHOTO SERVING
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def serve_upload(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# ============================================================
# CITIZEN TRACKING API
# ============================================================

@app.route(
    "/api/complaints/<complaint_id>",
    methods=[
        "GET"
    ]
)
def citizen_track_complaint(
    complaint_id
):

    complaint_id = (
        complaint_id
        .strip()
        .upper()
    )

    complaint = (
        get_complaint(
            complaint_id
        )
    )

    if complaint is None:

        return jsonify({
            "success":
                False,

            "error":
                "Complaint ID not found. Please check the ID and try again."
        }), 404

    complaint_data = (
        dict(
            complaint
        )
    )

    public_complaint = {

        "complaint_id":
            complaint_data.get(
                "complaint_id"
            ),

        "created_at":
            complaint_data.get(
                "created_at"
            ),

        "updated_at":
            complaint_data.get(
                "updated_at"
            ),

        "status":
            complaint_data.get(
                "status"
            ),

        "detected_issue":
            complaint_data.get(
                "detected_issue"
            ),

        "detected_severity":
            complaint_data.get(
                "detected_severity"
            ),

        "responsible_authority":
            complaint_data.get(
                "responsible_authority"
            ),

        "department":
            complaint_data.get(
                "department"
            ),

        "priority":
            complaint_data.get(
                "priority"
            ),

        "priority_score":
            complaint_data.get(
                "priority_score"
            ),

        "detected_address":
            complaint_data.get(
                "detected_address"
            ),

        "assigned_to":
            complaint_data.get(
                "assigned_to"
            ),

        "resolution_note":
            complaint_data.get(
                "resolution_note"
            ),

        "resolved_at":
            complaint_data.get(
                "resolved_at"
            )
    }

    history_rows = (
        get_complaint_history(
            complaint_id
        )
    )

    public_history = [
        {
            "event_type":
                row["event_type"],

            "old_status":
                row["old_status"],

            "new_status":
                row["new_status"],

            "timestamp":
                row["timestamp"],

            "actor":
                row["actor"],

            "note":
                row["note"]
        }
        for row in history_rows
    ]

    return jsonify({
        "success":
            True,

        "complaint":
            public_complaint,

        "history":
            public_history
    })


# ============================================================
# ANALYSE + SAVE COMPLAINT
# ============================================================

@app.route(
    "/api/analyze",
    methods=[
        "POST"
    ]
)
def analyze_complaint():

    saved_photo_absolute_path = None

    try:

        # ----------------------------------------------------
        # PHOTO
        # ----------------------------------------------------

        if (
            "photo"
            not in request.files
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "Photo evidence is required."
            }), 400

        photo = (
            request.files[
                "photo"
            ]
        )

        if (
            photo.filename == ""
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "No photo was selected."
            }), 400

        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        latitude_raw = (
            request.form.get(
                "latitude"
            )
        )

        longitude_raw = (
            request.form.get(
                "longitude"
            )
        )

        if (
            not latitude_raw
            or
            not longitude_raw
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "GPS location is required."
            }), 400

        try:

            latitude = float(
                latitude_raw
            )

            longitude = float(
                longitude_raw
            )

        except ValueError:

            return jsonify({
                "success":
                    False,

                "error":
                    "Invalid GPS coordinates."
            }), 400

        if not (
            -90 <= latitude <= 90
            and
            -180 <= longitude <= 180
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "GPS coordinates are outside valid range."
            }), 400

        # ----------------------------------------------------
        # GPS ACCURACY
        # ----------------------------------------------------

        gps_accuracy_raw = (
            request.form.get(
                "gps_accuracy"
            )
        )

        try:

            gps_accuracy = (
                float(
                    gps_accuracy_raw
                )
                if gps_accuracy_raw
                else None
            )

        except ValueError:

            gps_accuracy = None

        # ----------------------------------------------------
        # DESCRIPTION
        #
        # Frontend address/risk/score are intentionally ignored.
        # ----------------------------------------------------

        description = (
            request.form.get(
                "description",
                ""
            )
            .strip()
        )

        # ----------------------------------------------------
        # READ IMAGE
        # ----------------------------------------------------

        image_bytes = (
            photo.read()
        )

        if not image_bytes:

            return jsonify({
                "success":
                    False,

                "error":
                    "Uploaded photo is empty."
            }), 400

        # ----------------------------------------------------
        # IMAGE HASH
        # ----------------------------------------------------

        image_hash = (
            hashlib
            .sha256(
                image_bytes
            )
            .hexdigest()
        )

        # ----------------------------------------------------
        # EXACT DUPLICATE
        #
        # Same image bytes + nearby position.
        # This happens before AI inference.
        # ----------------------------------------------------

        exact_duplicate = (
            find_exact_duplicate(

                image_hash=
                    image_hash,

                latitude=
                    latitude,

                longitude=
                    longitude,

                radius_metres=
                    100
            )
        )

        if exact_duplicate:

            return (
                build_existing_complaint_response(

                    existing=
                        exact_duplicate,

                    duplicate_type=
                        exact_duplicate[
                            "duplicate_type"
                        ],

                    duplicate_reason=
                        exact_duplicate[
                            "duplicate_reason"
                        ],

                    duplicate_distance=
                        exact_duplicate[
                            "duplicate_distance_metres"
                        ]
                )
            )

        # ----------------------------------------------------
        # IMAGE VALIDATION
        # ----------------------------------------------------

        try:

            verification_image = (
                Image.open(
                    io.BytesIO(
                        image_bytes
                    )
                )
            )

            verification_image.verify()

            image = (
                Image.open(
                    io.BytesIO(
                        image_bytes
                    )
                )
                .convert(
                    "RGB"
                )
            )

        except (
            UnidentifiedImageError,
            OSError
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "Uploaded file is not a valid image."
            }), 400

        # ----------------------------------------------------
        # MINIMUM IMAGE SIZE
        # ----------------------------------------------------

        if (
            image.width < 96
            or
            image.height < 96
        ):

            return jsonify({
                "success":
                    False,

                "error":
                    "Photo resolution is too low for reliable analysis."
            }), 400

        # ====================================================
        # SERVER-SIDE LOCATION VERIFICATION
        #
        # Browser-provided:
        # location_score
        # location_risk
        # detected_address
        #
        # are NOT trusted.
        # ====================================================

        location_context = (
            verify_location_context(
                latitude,
                longitude
            )
        )

        detected_address = (
            location_context[
                "address"
            ]
        )

        location_risk = (
            location_context[
                "risk"
            ]
        )

        location_score = (
            int(
                location_context[
                    "score"
                ]
            )
        )

        location_context_verified = (
            bool(
                location_context[
                    "context_verified"
                ]
            )
        )

        # ----------------------------------------------------
        # JURISDICTION
        # ----------------------------------------------------

        jurisdiction_result = (
            resolve_jurisdiction(

                address=
                    detected_address,

                latitude=
                    latitude,

                longitude=
                    longitude
            )
        )

        # ----------------------------------------------------
        # AI ISSUE
        # ----------------------------------------------------

        issue_result = (
            detect_issue(
                image
            )
        )

        detected_issue = (
            issue_result[
                "issue"
            ]
        )

        # ----------------------------------------------------
        # NEARBY RECENT DUPLICATE CANDIDATE
        # ----------------------------------------------------

        nearby_duplicate = None

        if detected_issue not in [
            "Manual Review Required",
            "No Clear Civic Issue"
        ]:

            nearby_duplicate = (
                find_nearby_duplicate(

                    detected_issue=
                        detected_issue,

                    latitude=
                        latitude,

                    longitude=
                        longitude,

                    radius_metres=
                        35,

                    within_hours=
                        24
                )
            )

        # ----------------------------------------------------
        # AI SEVERITY
        # ----------------------------------------------------

        severity_result = (
            detect_severity(
                image,
                detected_issue
            )
        )

        detected_severity = (
            severity_result[
                "severity"
            ]
        )

        # ----------------------------------------------------
        # REVIEW SAFETY GATES
        # ----------------------------------------------------

        location_review_required = (
            not
            location_context_verified
        )

        evidence_review_required = (
            issue_result[
                "review_required"
            ]

            or

            severity_result[
                "review_required"
            ]

            or

            location_review_required

            or

            nearby_duplicate
            is not None
        )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        department = (
            DEPARTMENT_MAP.get(
                detected_issue,
                "Civic Control Room / Manual Review"
            )
        )

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        priority_result = (
            calculate_priority(

                location_score=
                    location_score,

                detected_issue=
                    detected_issue,

                detected_severity=
                    detected_severity,

                review_required=
                    evidence_review_required
            )
        )

        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        explanation = (

            f"Server-side GPS context contributed "
            f"{priority_result['location_score']}/50 points. "

            f"Detected issue "
            f"({detected_issue}) contributed "
            f"{priority_result['problem_score']}/30 points. "

            f"Photo-estimated severity "
            f"({detected_severity}) contributed "
            f"{priority_result['severity_score']}/20 points. "
        )

        if (
            location_context_verified
        ):

            explanation += (
                "Address and nearby public-risk context were "
                "independently derived on the server from the "
                "submitted GPS coordinates. "
            )

        else:

            explanation += (
                "The external location-context service could "
                "not fully verify both address and nearby risk, "
                "so automatic dispatch was blocked and human "
                "review is required. "
            )

        if nearby_duplicate:

            explanation += (

                "A recent unresolved complaint for the same "
                "detected issue exists very close to this "
                "location. This is treated as a duplicate "
                "candidate, not automatically as spam. "
            )

        if (
            issue_result[
                "review_required"
            ]

            or

            severity_result[
                "review_required"
            ]
        ):

            explanation += (
                "The image evidence did not pass all AI "
                "confidence checks. "
            )

        if (
            jurisdiction_result[
                "resolved"
            ]
        ):

            explanation += (

                f"Jurisdiction matched "
                f"{jurisdiction_result['jurisdiction']} "
                f"and routed to "
                f"{jurisdiction_result['authority']}."
            )

        else:

            explanation += (

                "Jurisdiction could not be safely resolved "
                "using an active verified rule, so the report "
                "was routed to the Jurisdiction Review Queue."
            )

        # ----------------------------------------------------
        # SAVE PHOTO
        # ----------------------------------------------------

        photo_path = (
            save_complaint_photo(
                image
            )
        )

        saved_photo_absolute_path = (
            os.path.join(
                PROJECT_ROOT,
                photo_path
            )
        )

        # ----------------------------------------------------
        # CREATE DATABASE RECORD
        # ----------------------------------------------------

        complaint_id = (
            create_complaint(

                photo_path=
                    photo_path,

                image_hash=
                    image_hash,

                description=
                    description,

                latitude=
                    latitude,

                longitude=
                    longitude,

                gps_accuracy=
                    gps_accuracy,

                detected_address=
                    detected_address,

                location_risk=
                    location_risk,

                location_score=
                    location_score,

                detected_issue=
                    detected_issue,

                issue_confidence=
                    issue_result[
                        "confidence"
                    ]
                    * 100,

                detected_severity=
                    detected_severity,

                severity_confidence=
                    severity_result[
                        "confidence"
                    ]
                    * 100,

                responsible_authority=
                    jurisdiction_result[
                        "authority"
                    ],

                jurisdiction=
                    jurisdiction_result[
                        "jurisdiction"
                    ],

                jurisdiction_confidence=
                    jurisdiction_result[
                        "confidence"
                    ],

                jurisdiction_rule_id=
                    jurisdiction_result[
                        "rule_id"
                    ],

                department=
                    department,

                priority=
                    priority_result[
                        "priority"
                    ],

                priority_score=
                    priority_result[
                        "score"
                    ],

                review_required=
                    evidence_review_required
            )
        )

        saved_complaint = (
            get_complaint(
                complaint_id
            )
        )

        # ----------------------------------------------------
        # DUPLICATE RESPONSE
        # ----------------------------------------------------

        if nearby_duplicate:

            duplicate_response = {

                "detected":
                    True,

                "type":
                    nearby_duplicate[
                        "duplicate_type"
                    ],

                "action":
                    "FLAGGED_FOR_REVIEW",

                "existing_complaint_id":
                    nearby_duplicate[
                        "complaint_id"
                    ],

                "distance_metres":
                    nearby_duplicate[
                        "duplicate_distance_metres"
                    ],

                "reason":
                    nearby_duplicate[
                        "duplicate_reason"
                    ]
            }

        else:

            duplicate_response = {

                "detected":
                    False,

                "type":
                    None,

                "action":
                    "NONE",

                "existing_complaint_id":
                    None,

                "distance_metres":
                    None,

                "reason":
                    None
            }

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "complaint": {

                "complaint_id":
                    complaint_id,

                "status":
                    saved_complaint[
                        "status"
                    ],

                "created_at":
                    saved_complaint[
                        "created_at"
                    ]
            },

            "duplicate":
                duplicate_response,

            "gps": {

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "accuracy":
                    gps_accuracy
            },

            "location": {

                "address":
                    detected_address,

                "risk":
                    location_risk,

                "score":
                    location_score,

                "verified_by_server":
                    True,

                "address_verified":
                    location_context[
                        "address_verified"
                    ],

                "risk_verified":
                    location_context[
                        "risk_verified"
                    ],

                "context_verified":
                    location_context[
                        "context_verified"
                    ],

                "nearby":
                    location_context[
                        "nearby"
                    ],

                "verification_notes":
                    location_context[
                        "verification_notes"
                    ]
            },

            "vision": {

                "issue":
                    detected_issue,

                "issue_confidence":
                    round(
                        issue_result[
                            "confidence"
                        ]
                        * 100,
                        1
                    ),

                "issue_margin":
                    round(
                        issue_result[
                            "margin"
                        ]
                        * 100,
                        1
                    ),

                "severity":
                    detected_severity,

                "severity_confidence":
                    round(
                        severity_result[
                            "confidence"
                        ]
                        * 100,
                        1
                    ),

                "severity_margin":
                    round(
                        severity_result[
                            "margin"
                        ]
                        * 100,
                        1
                    ),

                "review_required":
                    evidence_review_required
            },

            "routing": {

                "authority":
                    jurisdiction_result[
                        "authority"
                    ],

                "department":
                    department,

                "jurisdiction":
                    jurisdiction_result[
                        "jurisdiction"
                    ],

                "jurisdiction_resolved":
                    jurisdiction_result[
                        "resolved"
                    ],

                "jurisdiction_confidence":
                    jurisdiction_result[
                        "confidence"
                    ],

                "rule_id":
                    jurisdiction_result[
                        "rule_id"
                    ],

                "effective_date":
                    jurisdiction_result[
                        "effective_date"
                    ],

                "source_verified":
                    jurisdiction_result[
                        "source_verified"
                    ]
            },

            "priority": {

                "level":
                    priority_result[
                        "priority"
                    ],

                "score":
                    priority_result[
                        "score"
                    ],

                "components": {

                    "location":
                        priority_result[
                            "location_score"
                        ],

                    "problem":
                        priority_result[
                            "problem_score"
                        ],

                    "severity":
                        priority_result[
                            "severity_score"
                        ]
                },

                "explanation":
                    explanation
            }
        })

    except Exception as error:

        if (
            saved_photo_absolute_path
            and
            os.path.exists(
                saved_photo_absolute_path
            )
        ):

            try:

                os.remove(
                    saved_photo_absolute_path
                )

            except OSError:

                pass

        print(
            "ANALYSIS ERROR:",
            repr(
                error
            )
        )

        return jsonify({
            "success":
                False,

            "error":
                "Automatic analysis failed.",

            "details":
                str(
                    error
                )
        }), 500


# ============================================================
# STAFF — LIST COMPLAINTS
# ============================================================

@app.route(
    "/api/staff/complaints",
    methods=[
        "GET"
    ]
)
def staff_list_complaints():

    try:

        complaints = (
            list_complaints(
                limit=500
            )
        )

        response_complaints = []

        for complaint in complaints:

            item = dict(
                complaint
            )

            photo_path = (
                item.get(
                    "photo_path"
                )
            )

            if photo_path:

                filename = (
                    os.path.basename(
                        photo_path
                    )
                )

                item[
                    "photo_url"
                ] = url_for(
                    "serve_upload",
                    filename=
                        filename
                )

            else:

                item[
                    "photo_url"
                ] = None

            response_complaints.append(
                item
            )

        return jsonify({
            "success":
                True,

            "count":
                len(
                    response_complaints
                ),

            "complaints":
                response_complaints
        })

    except Exception as error:

        print(
            "STAFF LIST ERROR:",
            repr(
                error
            )
        )

        return jsonify({
            "success":
                False,

            "error":
                "Unable to load complaints."
        }), 500


# ============================================================
# STAFF — COMPLAINT HISTORY
# ============================================================

@app.route(
    "/api/staff/complaints/<complaint_id>/history",
    methods=[
        "GET"
    ]
)
def staff_complaint_history(
    complaint_id
):

    complaint = (
        get_complaint(
            complaint_id
        )
    )

    if complaint is None:

        return jsonify({
            "success":
                False,

            "error":
                "Complaint not found."
        }), 404

    history_rows = (
        get_complaint_history(
            complaint_id
        )
    )

    history = [
        dict(
            row
        )
        for row in history_rows
    ]

    return jsonify({
        "success":
            True,

        "complaint_id":
            complaint_id,

        "history":
            history
    })


# ============================================================
# STAFF — ASSIGN COMPLAINT
# ============================================================

@app.route(
    "/api/staff/complaints/<complaint_id>/assign",
    methods=[
        "POST"
    ]
)
def staff_assign_complaint(
    complaint_id
):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        assigned_to = (
            str(
                data.get(
                    "assigned_to",
                    ""
                )
            )
            .strip()
        )

        if not assigned_to:

            return jsonify({
                "success":
                    False,

                "error":
                    "Officer or team name is required."
            }), 400

        success = (
            assign_complaint(

                complaint_id=
                    complaint_id,

                assigned_to=
                    assigned_to,

                actor=
                    "Civic Staff Dashboard"
            )
        )

        if not success:

            return jsonify({
                "success":
                    False,

                "error":
                    "Complaint not found."
            }), 404

        updated = (
            get_complaint(
                complaint_id
            )
        )

        return jsonify({
            "success":
                True,

            "complaint":
                dict(
                    updated
                )
        })

    except Exception as error:

        print(
            "ASSIGN ERROR:",
            repr(
                error
            )
        )

        return jsonify({
            "success":
                False,

            "error":
                str(
                    error
                )
        }), 400


# ============================================================
# STAFF — UPDATE STATUS
# ============================================================

@app.route(
    "/api/staff/complaints/<complaint_id>/status",
    methods=[
        "POST"
    ]
)
def staff_update_status(
    complaint_id
):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        new_status = (
            str(
                data.get(
                    "status",
                    ""
                )
            )
            .strip()
            .upper()
        )

        note = (
            str(
                data.get(
                    "note",
                    ""
                )
            )
            .strip()
        )

        if not new_status:

            return jsonify({
                "success":
                    False,

                "error":
                    "New status is required."
            }), 400

        success = (
            update_complaint_status(

                complaint_id=
                    complaint_id,

                new_status=
                    new_status,

                actor=
                    "Civic Staff Dashboard",

                note=
                    note
            )
        )

        if not success:

            return jsonify({
                "success":
                    False,

                "error":
                    "Complaint not found."
            }), 404

        updated = (
            get_complaint(
                complaint_id
            )
        )

        return jsonify({
            "success":
                True,

            "complaint":
                dict(
                    updated
                )
        })

    except ValueError as error:

        return jsonify({
            "success":
                False,

            "error":
                str(
                    error
                )
        }), 400

    except Exception as error:

        print(
            "STATUS UPDATE ERROR:",
            repr(
                error
            )
        )

        return jsonify({
            "success":
                False,

            "error":
                "Unable to update complaint status."
        }), 500


# ============================================================
# STAFF — RESOLVE
# ============================================================

@app.route(
    "/api/staff/complaints/<complaint_id>/resolve",
    methods=[
        "POST"
    ]
)
def staff_resolve_complaint(
    complaint_id
):

    try:

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )

        resolution_note = (
            str(
                data.get(
                    "resolution_note",
                    ""
                )
            )
            .strip()
        )

        if not resolution_note:

            return jsonify({
                "success":
                    False,

                "error":
                    "Resolution note is required."
            }), 400

        success = (
            resolve_complaint(

                complaint_id=
                    complaint_id,

                resolution_note=
                    resolution_note,

                actor=
                    "Civic Staff Dashboard"
            )
        )

        if not success:

            return jsonify({
                "success":
                    False,

                "error":
                    "Complaint not found."
            }), 404

        updated = (
            get_complaint(
                complaint_id
            )
        )

        return jsonify({
            "success":
                True,

            "complaint":
                dict(
                    updated
                )
        })

    except ValueError as error:

        return jsonify({
            "success":
                False,

            "error":
                str(
                    error
                )
        }), 400

    except Exception as error:

        print(
            "RESOLVE ERROR:",
            repr(
                error
            )
        )

        return jsonify({
            "success":
                False,

            "error":
                "Unable to resolve complaint."
        }), 500


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )