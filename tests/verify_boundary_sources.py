import os
import sys
from datetime import date


# ============================================================
# PROJECT PATH
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
# IMPORT SYSTEM
# ============================================================

from boundary_sources import (
    is_trusted_source,
    validate_rule_provenance,
    validate_dataset_version,
    can_activate_boundary_rule
)


results = []


def check(
    name,
    actual,
    expected
):

    passed = (
        actual == expected
    )

    results.append(
        passed
    )

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"[{status}] {name}"
    )

    if not passed:

        print(
            f"       Expected: {expected}"
        )

        print(
            f"       Actual:   {actual}"
        )


# ============================================================
# TEST TRUSTED DOMAINS
# ============================================================

def test_domains():

    print(
        "\n========================================"
    )

    print(
        " TRUSTED SOURCE TESTS"
    )

    print(
        "========================================"
    )


    check(
        "Mysuru government domain accepted",
        is_trusted_source(
            "https://mysore.nic.in/"
        ),
        True
    )


    check(
        "Karnataka government domain accepted",
        is_trusted_source(
            "https://sujala3lri.karnataka.gov.in/"
        ),
        True
    )


    check(
        "Random website rejected",
        is_trusted_source(
            "https://example.com/boundary-update"
        ),
        False
    )


    check(
        "Fake lookalike domain rejected",
        is_trusted_source(
            "https://mysore.nic.in.fakewebsite.com/"
        ),
        False
    )


# ============================================================
# RULE PROVENANCE TESTS
# ============================================================

def test_rule_provenance():

    print(
        "\n========================================"
    )

    print(
        " RULE PROVENANCE TESTS"
    )

    print(
        "========================================"
    )


    valid_rule = {

        "name":
            "Test Jurisdiction Rule",

        "authority":
            "Test Municipal Authority",

        "effective_from":
            date(2026, 10, 1),

        "source_title":
            "Official Government Notification",

        "source_url":
            "https://mysore.nic.in/",

        "status":
            "VERIFIED"
    }


    result = (
        validate_rule_provenance(
            valid_rule
        )
    )


    check(
        "Valid government rule provenance accepted",
        result["valid"],
        True
    )


    missing_source_rule = {

        "name":
            "Bad Test Rule",

        "authority":
            "Unknown Authority",

        "effective_from":
            date(2026, 10, 1),

        "status":
            "VERIFIED"
    }


    result = (
        validate_rule_provenance(
            missing_source_rule
        )
    )


    check(
        "Rule without source rejected",
        result["valid"],
        False
    )


    untrusted_rule = {

        "name":
            "Untrusted Test Rule",

        "authority":
            "Fake Authority",

        "effective_from":
            date(2026, 10, 1),

        "source_title":
            "Random Blog",

        "source_url":
            "https://example.com/change",

        "status":
            "VERIFIED"
    }


    result = (
        validate_rule_provenance(
            untrusted_rule
        )
    )


    check(
        "Non-government source rejected",
        result["valid"],
        False
    )


# ============================================================
# ACTIVATION TESTS
# ============================================================

def test_activation():

    print(
        "\n========================================"
    )

    print(
        " SAFE ACTIVATION TESTS"
    )

    print(
        "========================================"
    )


    verified_rule = {

        "name":
            "Verified Test Rule",

        "authority":
            "Verified Authority",

        "effective_from":
            date(2026, 10, 1),

        "source_title":
            "Official Notification",

        "source_url":
            "https://mysore.nic.in/",

        "status":
            "VERIFIED"
    }


    result = (
        can_activate_boundary_rule(
            verified_rule
        )
    )


    check(
        "Verified official rule can activate",
        result["activate"],
        True
    )


    pending_rule = {

        "name":
            "Pending Test Rule",

        "authority":
            "Pending Authority",

        "effective_from":
            date(2026, 10, 1),

        "source_title":
            "Official Notification",

        "source_url":
            "https://mysore.nic.in/",

        "status":
            "PENDING"
    }


    result = (
        can_activate_boundary_rule(
            pending_rule
        )
    )


    check(
        "Pending rule cannot activate",
        result["activate"],
        False
    )


    fake_verified_rule = {

        "name":
            "Fake Verified Rule",

        "authority":
            "Fake Authority",

        "effective_from":
            date(2026, 10, 1),

        "source_title":
            "Fake Source",

        "source_url":
            "https://not-government.example.com/",

        "status":
            "VERIFIED"
    }


    result = (
        can_activate_boundary_rule(
            fake_verified_rule
        )
    )


    check(
        "VERIFIED flag cannot bypass source validation",
        result["activate"],
        False
    )


# ============================================================
# DATASET VERSION TESTS
# ============================================================

def test_dataset():

    print(
        "\n========================================"
    )

    print(
        " DATASET VERSION TESTS"
    )

    print(
        "========================================"
    )


    valid_dataset = {

        "dataset_id":
            "MYSURU_BOUNDARY_TEST",

        "version":
            "2026.10",

        "source_url":
            "https://sujala3lri.karnataka.gov.in/",

        "retrieved_at":
            "2026-09-20T15:00:00+05:30",

        "effective_from":
            "2026-10-01"
    }


    result = (
        validate_dataset_version(
            valid_dataset
        )
    )


    check(
        "Versioned government dataset accepted",
        result["valid"],
        True
    )


    incomplete_dataset = {

        "dataset_id":
            "BROKEN_DATASET",

        "version":
            "1"
    }


    result = (
        validate_dataset_version(
            incomplete_dataset
        )
    )


    check(
        "Incomplete dataset metadata rejected",
        result["valid"],
        False
    )


# ============================================================
# SUMMARY
# ============================================================

def summary():

    passed = sum(
        1
        for item in results
        if item
    )

    total = len(
        results
    )


    print(
        "\n========================================"
    )

    print(
        " BOUNDARY SOURCE VERIFICATION"
    )

    print(
        "========================================"
    )

    print(
        f"OVERALL            {passed}/{total} PASS"
    )

    print(
        "========================================"
    )


    if passed == total:

        print(
            "\nSTATUS: SOURCE SAFETY CHECKS VERIFIED"
        )

        print(
            "Only rules with trusted government-source "
            "provenance and VERIFIED status can activate."
        )

        return 0


    print(
        "\nSTATUS: VERIFICATION FAILED"
    )

    return 1


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    test_domains()

    test_rule_provenance()

    test_activation()

    test_dataset()

    sys.exit(
        summary()
    )