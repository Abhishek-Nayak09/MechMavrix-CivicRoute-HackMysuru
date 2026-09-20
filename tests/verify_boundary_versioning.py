import os
import sys
from datetime import date


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
# IMPORT JURISDICTION MODULE
# ============================================================

import jurisdiction


# ============================================================
# SIMPLE TEST HELPER
# ============================================================

results = []


def check(
    name,
    actual,
    expected
):
    passed = actual == expected

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
# TEST-ONLY SIMULATED BOUNDARY HISTORY
#
# IMPORTANT:
# These dates/authorities are NOT claimed as real government
# notifications.
#
# They exist only to prove that the routing engine preserves
# historical jurisdiction and switches automatically when a
# new rule becomes effective.
# ============================================================

TEST_RULES = [

    {
        "name":
            "Belavadi Historical Jurisdiction",

        "keywords": [
            "belavadi",
            "belawadi"
        ],

        "authority":
            "Hootagalli City Municipal Council",

        "effective_from":
            date(2021, 3, 31),

        "effective_to":
            date(2026, 9, 30),

        "confidence":
            "HIGH",

        "basis":
            "TEST DATA - historical jurisdiction version"
    },

    {
        "name":
            "Belavadi New Jurisdiction",

        "keywords": [
            "belavadi",
            "belawadi"
        ],

        "authority":
            "New Municipal Authority - TEST ONLY",

        "effective_from":
            date(2026, 10, 1),

        "effective_to":
            None,

        "confidence":
            "HIGH",

        "basis":
            "TEST DATA - simulated new boundary version"
    }

]


# ============================================================
# RUN VERSIONING TEST
# ============================================================

def run_tests():

    print(
        "\n========================================"
    )

    print(
        " CIVICROUTE BOUNDARY VERSIONING TEST"
    )

    print(
        "========================================"
    )

    print(
        "NOTE: New authority below is simulated "
        "test data, not a real government change.\n"
    )


    # --------------------------------------------------------
    # SAVE REAL PRODUCTION RULES
    # --------------------------------------------------------

    original_rules = (
        jurisdiction.JURISDICTION_RULES
    )


    try:

        # ----------------------------------------------------
        # TEMPORARILY USE TEST-ONLY RULES
        # ----------------------------------------------------

        jurisdiction.JURISDICTION_RULES = (
            TEST_RULES
        )


        address = (
            "Belavadi, Mysuru, "
            "Mysuru District, Karnataka"
        )


        # ----------------------------------------------------
        # TEST 1
        # BEFORE BOUNDARY CHANGE
        # ----------------------------------------------------

        old_result = (
            jurisdiction.resolve_jurisdiction(
                address=address,
                complaint_date=date(
                    2026,
                    9,
                    20
                )
            )
        )


        check(
            "Old complaint routes to old authority",
            old_result[
                "authority"
            ],
            "Hootagalli City Municipal Council"
        )


        # ----------------------------------------------------
        # TEST 2
        # OLD RULE'S FINAL ACTIVE DAY
        # ----------------------------------------------------

        final_old_day = (
            jurisdiction.resolve_jurisdiction(
                address=address,
                complaint_date=date(
                    2026,
                    9,
                    30
                )
            )
        )


        check(
            "Old authority remains active through effective_to",
            final_old_day[
                "authority"
            ],
            "Hootagalli City Municipal Council"
        )


        # ----------------------------------------------------
        # TEST 3
        # NEW RULE EFFECTIVE DATE
        # ----------------------------------------------------

        new_result = (
            jurisdiction.resolve_jurisdiction(
                address=address,
                complaint_date=date(
                    2026,
                    10,
                    1
                )
            )
        )


        check(
            "New complaint switches on effective date",
            new_result[
                "authority"
            ],
            "New Municipal Authority - TEST ONLY"
        )


        # ----------------------------------------------------
        # TEST 4
        # FUTURE COMPLAINT
        # ----------------------------------------------------

        future_result = (
            jurisdiction.resolve_jurisdiction(
                address=address,
                complaint_date=date(
                    2027,
                    1,
                    15
                )
            )
        )


        check(
            "Future complaint stays with new authority",
            future_result[
                "authority"
            ],
            "New Municipal Authority - TEST ONLY"
        )


        # ----------------------------------------------------
        # TEST 5
        # HISTORICAL COMPLAINT MUST NOT CHANGE
        #
        # Even after a new rule exists, querying an old
        # complaint date must return its historical authority.
        # ----------------------------------------------------

        historical_recheck = (
            jurisdiction.resolve_jurisdiction(
                address=address,
                complaint_date=date(
                    2026,
                    9,
                    20
                )
            )
        )


        check(
            "Historical complaint preserves original authority",
            historical_recheck[
                "authority"
            ],
            "Hootagalli City Municipal Council"
        )


        # ----------------------------------------------------
        # TEST 6
        # EFFECTIVE DATE IS RETURNED
        # ----------------------------------------------------

        check(
            "Engine records routing date used",
            new_result[
                "effective_date"
            ],
            "2026-10-01"
        )


    finally:

        # ----------------------------------------------------
        # ALWAYS RESTORE REAL PRODUCTION RULES
        # ----------------------------------------------------

        jurisdiction.JURISDICTION_RULES = (
            original_rules
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    passed = sum(
        1
        for item in results
        if item
    )

    total = len(
        results
    )


    print(
        "\n----------------------------------------"
    )

    print(
        f"BOUNDARY VERSION TESTS   {passed}/{total} PASS"
    )

    print(
        "----------------------------------------"
    )


    if passed == total:

        print(
            "\nSTATUS: VERSIONING ENGINE VERIFIED"
        )

        print(
            "The test proves that CivicRoute can:"
        )

        print(
            "- preserve historical jurisdiction"
        )

        print(
            "- activate a new authority on its effective date"
        )

        print(
            "- avoid rewriting old complaint routing history"
        )

        print(
            "\nIt does NOT prove that government boundary "
            "updates are automatically downloaded. "
            "Official boundary data still needs a trusted "
            "update source."
        )

        return 0


    print(
        "\nSTATUS: VERSIONING TEST FAILED"
    )

    return 1


# ============================================================
# START TEST
# ============================================================

if __name__ == "__main__":

    exit(
        run_tests()
    )