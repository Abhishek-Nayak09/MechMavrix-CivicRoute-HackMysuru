import os
import sys
import io
from PIL import Image


# ============================================================
# PROJECT PATH SETUP
# ============================================================

ROOT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

SRC_DIR = os.path.join(
    ROOT_DIR,
    "src"
)

if SRC_DIR not in sys.path:
    sys.path.insert(
        0,
        SRC_DIR
    )


# ============================================================
# IMPORT PROJECT COMPONENTS
# ============================================================

from jurisdiction import resolve_jurisdiction

from app import (
    app,
    calculate_priority
)


# ============================================================
# TEST RESULT STORAGE
# ============================================================

results = []


def record_result(
    category,
    test_name,
    passed,
    expected=None,
    actual=None
):
    results.append({
        "category": category,
        "name": test_name,
        "passed": passed,
        "expected": expected,
        "actual": actual
    })

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"[{status}] "
        f"{category} -> {test_name}"
    )

    if not passed:

        print(
            f"       Expected: {expected}"
        )

        print(
            f"       Actual:   {actual}"
        )


# ============================================================
# JURISDICTION TESTS
# ============================================================

def test_jurisdiction():

    print(
        "\n"
        "========================================"
    )

    print(
        " JURISDICTION ENGINE TESTS"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # BELAVADI
    # --------------------------------------------------------

    result = resolve_jurisdiction(
        address=(
            "Belavadi, Mysuru, "
            "Mysuru District, Karnataka"
        )
    )

    expected = (
        "Hootagalli City Municipal Council"
    )

    actual = result[
        "authority"
    ]

    record_result(
        "Jurisdiction",
        "Belavadi routes to Hootagalli CMC",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # KOORGALLI
    # --------------------------------------------------------

    result = resolve_jurisdiction(
        address=(
            "Koorgalli Industrial Area, "
            "Mysuru, Karnataka"
        )
    )

    expected = (
        "Hootagalli City Municipal Council"
    )

    actual = result[
        "authority"
    ]

    record_result(
        "Jurisdiction",
        "Koorgalli routes to Hootagalli CMC",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # CASE INSENSITIVE
    # --------------------------------------------------------

    result = resolve_jurisdiction(
        address=(
            "BELAVADI, MYSURU, KARNATAKA"
        )
    )

    expected = True

    actual = result[
        "resolved"
    ]

    record_result(
        "Jurisdiction",
        "Locality matching is case insensitive",
        actual is expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # UNKNOWN LOCATION MUST NOT BE GUESSED
    # --------------------------------------------------------

    result = resolve_jurisdiction(
        address=(
            "Unknown Boundary Area, "
            "Mysuru District, Karnataka"
        )
    )

    expected = (
        "Jurisdiction Review Queue"
    )

    actual = result[
        "authority"
    ]

    record_result(
        "Jurisdiction",
        "Unknown boundary prevents misrouting",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # UNKNOWN LOCATION = UNRESOLVED
    # --------------------------------------------------------

    expected = False

    actual = result[
        "resolved"
    ]

    record_result(
        "Jurisdiction",
        "Unknown jurisdiction marked unresolved",
        actual is expected,
        expected,
        actual
    )


# ============================================================
# PRIORITY ENGINE TESTS
# ============================================================

def test_priority():

    print(
        "\n"
        "========================================"
    )

    print(
        " PRIORITY ENGINE TESTS"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # CURRENT SCREENSHOT TYPE CASE
    #
    # 15 location
    # 27 pothole
    # 16 high severity
    #
    # TOTAL = 58
    # --------------------------------------------------------

    result = calculate_priority(
        location_score=15,
        detected_issue=
            "Pothole / Road Damage",
        detected_severity=
            "HIGH",
        review_required=False
    )

    expected = 58

    actual = result[
        "score"
    ]

    record_result(
        "Priority",
        "Pothole score calculation",
        actual == expected,
        expected,
        actual
    )


    expected = "MEDIUM"

    actual = result[
        "priority"
    ]

    record_result(
        "Priority",
        "58/100 produces MEDIUM priority",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # CRITICAL CASE
    # --------------------------------------------------------

    result = calculate_priority(
        location_score=50,
        detected_issue=
            "Open Manhole / Open Drain",
        detected_severity=
            "CRITICAL",
        review_required=False
    )

    expected = 100

    actual = result[
        "score"
    ]

    record_result(
        "Priority",
        "Maximum risk reaches 100",
        actual == expected,
        expected,
        actual
    )


    expected = "CRITICAL"

    actual = result[
        "priority"
    ]

    record_result(
        "Priority",
        "High-risk case becomes CRITICAL",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # REVIEW SAFETY
    # --------------------------------------------------------

    result = calculate_priority(
        location_score=50,
        detected_issue=
            "Open Manhole / Open Drain",
        detected_severity=
            "CRITICAL",
        review_required=True
    )

    expected = (
        "REVIEW REQUIRED"
    )

    actual = result[
        "priority"
    ]

    record_result(
        "Priority",
        "Unverified evidence blocks auto-dispatch",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # LOW-RISK CASE
    # --------------------------------------------------------

    result = calculate_priority(
        location_score=15,
        detected_issue=
            "No Clear Civic Issue",
        detected_severity=
            "UNVERIFIED",
        review_required=False
    )

    expected = "LOW"

    actual = result[
        "priority"
    ]

    record_result(
        "Priority",
        "No civic issue stays LOW",
        actual == expected,
        expected,
        actual
    )


# ============================================================
# API / BAD INPUT TESTS
#
# These tests deliberately stop BEFORE the AI model.
# Therefore they are fast and do not download/load CLIP.
# ============================================================

def create_tiny_image():

    image = Image.new(
        "RGB",
        (32, 32)
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG"
    )

    buffer.seek(0)

    return buffer


def test_bad_inputs():

    print(
        "\n"
        "========================================"
    )

    print(
        " BAD INPUT / API TESTS"
    )

    print(
        "========================================"
    )


    app.config[
        "TESTING"
    ] = True


    client = app.test_client()


    # --------------------------------------------------------
    # NO PHOTO
    # --------------------------------------------------------

    response = client.post(
        "/api/analyze",
        data={
            "latitude": "12.341486",
            "longitude": "76.576232"
        }
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Missing photo rejected",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # PHOTO BUT NO GPS
    # --------------------------------------------------------

    response = client.post(
        "/api/analyze",
        data={
            "photo": (
                io.BytesIO(
                    b"fake-image"
                ),
                "test.jpg"
            )
        },
        content_type=
            "multipart/form-data"
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Missing GPS rejected",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # NON-NUMERIC GPS
    # --------------------------------------------------------

    response = client.post(
        "/api/analyze",
        data={
            "latitude":
                "not-a-number",

            "longitude":
                "76.576232",

            "photo": (
                io.BytesIO(
                    b"fake-image"
                ),
                "test.jpg"
            )
        },
        content_type=
            "multipart/form-data"
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Non-numeric GPS rejected",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # OUT-OF-RANGE GPS
    # --------------------------------------------------------

    response = client.post(
        "/api/analyze",
        data={
            "latitude":
                "200",

            "longitude":
                "300",

            "photo": (
                io.BytesIO(
                    b"fake-image"
                ),
                "test.jpg"
            )
        },
        content_type=
            "multipart/form-data"
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Impossible GPS rejected",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # FAKE IMAGE FILE
    # --------------------------------------------------------

    response = client.post(
        "/api/analyze",
        data={
            "latitude":
                "12.341486",

            "longitude":
                "76.576232",

            "location_score":
                "15",

            "location_risk":
                "LOW",

            "detected_address":
                "Belavadi, Mysuru, Karnataka",

            "photo": (
                io.BytesIO(
                    b"This is not a real image"
                ),
                "fake.jpg"
            )
        },
        content_type=
            "multipart/form-data"
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Fake JPG rejected",
        actual == expected,
        expected,
        actual
    )


    # --------------------------------------------------------
    # VERY SMALL IMAGE
    # --------------------------------------------------------

    tiny_image = (
        create_tiny_image()
    )


    response = client.post(
        "/api/analyze",
        data={
            "latitude":
                "12.341486",

            "longitude":
                "76.576232",

            "location_score":
                "15",

            "location_risk":
                "LOW",

            "detected_address":
                "Belavadi, Mysuru, Karnataka",

            "photo": (
                tiny_image,
                "tiny.jpg"
            )
        },
        content_type=
            "multipart/form-data"
    )

    expected = 400

    actual = response.status_code

    record_result(
        "Bad Input",
        "Very low-resolution photo rejected",
        actual == expected,
        expected,
        actual
    )


# ============================================================
# FINAL REPORT
# ============================================================

def print_summary():

    print(
        "\n"
        "========================================"
    )

    print(
        " CIVICROUTE AUTOMATED VERIFICATION"
    )

    print(
        "========================================"
    )


    categories = []


    for result in results:

        category = result[
            "category"
        ]

        if category not in categories:
            categories.append(
                category
            )


    total_passed = 0

    total_tests = len(
        results
    )


    for category in categories:

        category_results = [

            result

            for result in results

            if result[
                "category"
            ] == category
        ]


        passed = sum(

            1

            for result in category_results

            if result[
                "passed"
            ]
        )


        total = len(
            category_results
        )


        total_passed += passed


        print(
            f"{category:<18}"
            f"{passed}/{total} PASS"
        )


    print(
        "----------------------------------------"
    )


    print(
        f"OVERALL            "
        f"{total_passed}/{total_tests} PASS"
    )


    print(
        "========================================"
    )


    failed = [

        result

        for result in results

        if not result[
            "passed"
        ]
    ]


    if failed:

        print(
            "\nSTATUS: FAILED"
        )

        print(
            "Fix failing checks before submission."
        )

        return False


    print(
        "\nSTATUS: ALL CURRENT CHECKS PASSED"
    )

    print(
        "Note: AI image-accuracy benchmark "
        "will be tested separately with "
        "ground-truth complaint photos."
    )

    return True


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":

    print(
        "\nStarting CivicRoute automated verification..."
    )


    test_jurisdiction()

    test_priority()

    test_bad_inputs()


    success = print_summary()


    if not success:
        sys.exit(1)


    sys.exit(0)