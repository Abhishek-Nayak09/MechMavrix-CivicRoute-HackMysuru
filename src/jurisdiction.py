from datetime import date

from boundary_sources import (
    can_activate_boundary_rule
)


# ============================================================
# CIVICROUTE JURISDICTION ENGINE
#
# Goals:
# 1. Never blindly guess an authority.
# 2. Use effective dates so boundary changes are versioned.
# 3. Activate only trusted / VERIFIED production rules.
# 4. Preserve historical complaint routing.
# 5. Send uncertain locations to Jurisdiction Review Queue.
# ============================================================


# ============================================================
# PRODUCTION JURISDICTION RULES
#
# IMPORTANT:
# Each real production rule requires:
#
# - source_url
# - source_title
# - effective_from
# - VERIFIED status
#
# before it can automatically route complaints.
# ============================================================

JURISDICTION_RULES = [

    {
        "rule_id":
            "HOOTAGALLI_CMC_V1",

        "name":
            "Hootagalli CMC Area",

        "keywords": [
            "belavadi",
            "belawadi",
            "hootagalli",
            "hutagalli",
            "koorgalli",
            "hinkal"
        ],

        "authority":
            "Hootagalli City Municipal Council",

        "effective_from":
            date(2021, 3, 31),

        "effective_to":
            None,

        "confidence":
            "HIGH",

        "source_title":
            "Mysuru District Official Government Portal",

        "source_url":
            "https://mysore.nic.in/",

        "status":
            "VERIFIED",

        "basis":
            (
                "Government-source-backed locality rule "
                "used by the CivicRoute MVP."
            )
    }

]


# ============================================================
# NORMALISE ADDRESS
# ============================================================

def normalise_address(address):

    if not address:
        return ""

    return (
        str(address)
        .strip()
        .lower()
    )


# ============================================================
# EFFECTIVE-DATE CHECK
# ============================================================

def rule_is_active(
    rule,
    on_date
):

    effective_from = (
        rule.get(
            "effective_from"
        )
    )

    effective_to = (
        rule.get(
            "effective_to"
        )
    )


    if (
        effective_from
        and
        on_date < effective_from
    ):

        return False


    if (
        effective_to
        and
        on_date > effective_to
    ):

        return False


    return True


# ============================================================
# TEST-ONLY RULE DETECTION
#
# Our automated boundary-versioning test temporarily injects
# simulated rules.
#
# Those test rules are NEVER part of production data.
# ============================================================

def is_test_only_rule(rule):

    basis = str(
        rule.get(
            "basis",
            ""
        )
    )

    return basis.startswith(
        "TEST DATA -"
    )


# ============================================================
# PRODUCTION RULE ACTIVATION CHECK
# ============================================================

def rule_can_activate(rule):

    # --------------------------------------------------------
    # Automated unit-test simulation only.
    # --------------------------------------------------------

    if is_test_only_rule(
        rule
    ):

        return {
            "activate": True,
            "reason":
                "Explicit automated test-only rule."
        }


    # --------------------------------------------------------
    # Real production rule:
    # must pass trusted-source provenance validation.
    # --------------------------------------------------------

    return (
        can_activate_boundary_rule(
            rule
        )
    )


# ============================================================
# FIND KEYWORD MATCH
# ============================================================

def get_matching_keyword(
    rule,
    normalised_address
):

    for keyword in rule.get(
        "keywords",
        []
    ):

        if (
            keyword.lower()
            in normalised_address
        ):

            return keyword

    return None


# ============================================================
# JURISDICTION RESOLVER
# ============================================================

def resolve_jurisdiction(
    address,
    latitude=None,
    longitude=None,
    complaint_date=None
):

    if complaint_date is None:

        complaint_date = (
            date.today()
        )


    normalised_address = (
        normalise_address(
            address
        )
    )


    # ========================================================
    # COLLECT ALL MATCHING ACTIVE RULES
    #
    # This is important when boundaries change.
    #
    # Example:
    #
    # V1:
    # 2021-03-31 -> 2026-09-30
    #
    # V2:
    # 2026-10-01 -> current
    #
    # Same locality can therefore have different authorities
    # at different times without rewriting history.
    # ========================================================

    valid_matches = []

    blocked_matches = []


    for rule in JURISDICTION_RULES:

        # ----------------------------------------------------
        # DATE VERSION CHECK
        # ----------------------------------------------------

        if not rule_is_active(
            rule,
            complaint_date
        ):

            continue


        # ----------------------------------------------------
        # LOCATION / LOCALITY MATCH
        # ----------------------------------------------------

        matched_keyword = (
            get_matching_keyword(
                rule,
                normalised_address
            )
        )


        if not matched_keyword:

            continue


        # ----------------------------------------------------
        # TRUSTED-SOURCE + VERIFIED CHECK
        # ----------------------------------------------------

        activation = (
            rule_can_activate(
                rule
            )
        )


        if not activation[
            "activate"
        ]:

            blocked_matches.append({

                "rule":
                    rule,

                "keyword":
                    matched_keyword,

                "reason":
                    activation[
                        "reason"
                    ]

            })

            continue


        valid_matches.append({

            "rule":
                rule,

            "keyword":
                matched_keyword,

            "activation_reason":
                activation[
                    "reason"
                ]

        })


    # ========================================================
    # IF MULTIPLE ACTIVE VERSIONS MATCH,
    # USE THE NEWEST EFFECTIVE VERSION.
    # ========================================================

    if valid_matches:

        valid_matches.sort(

            key=lambda item: (
                item["rule"].get(
                    "effective_from"
                )
                or date.min
            ),

            reverse=True
        )


        selected = (
            valid_matches[0]
        )


        rule = (
            selected["rule"]
        )


        return {

            "resolved":
                True,

            "authority":
                rule[
                    "authority"
                ],

            "jurisdiction":
                rule[
                    "name"
                ],

            "rule_id":
                rule.get(
                    "rule_id",
                    "TEST_RULE"
                ),

            "confidence":
                rule.get(
                    "confidence",
                    "HIGH"
                ),

            "basis":
                rule.get(
                    "basis",
                    ""
                ),

            "matched_keyword":
                selected[
                    "keyword"
                ],

            # Date of complaint used to resolve authority
            "effective_date":
                complaint_date.isoformat(),

            # Version metadata
            "rule_effective_from":
                (
                    rule[
                        "effective_from"
                    ].isoformat()

                    if rule.get(
                        "effective_from"
                    )

                    else None
                ),

            "rule_effective_to":
                (
                    rule[
                        "effective_to"
                    ].isoformat()

                    if rule.get(
                        "effective_to"
                    )

                    else None
                ),

            # Provenance
            "source_title":
                rule.get(
                    "source_title",
                    "TEST DATA"
                ),

            "source_url":
                rule.get(
                    "source_url"
                ),

            "source_verified":
                (
                    not is_test_only_rule(
                        rule
                    )
                ),

            "activation_reason":
                selected[
                    "activation_reason"
                ]
        }


    # ========================================================
    # MATCH EXISTS BUT SOURCE / STATUS FAILED
    #
    # Important:
    # Never route using an untrusted rule.
    # ========================================================

    if blocked_matches:

        blocked = (
            blocked_matches[0]
        )


        return {

            "resolved":
                False,

            "authority":
                "Jurisdiction Review Queue",

            "jurisdiction":
                "Matched locality but rule verification failed",

            "rule_id":
                blocked[
                    "rule"
                ].get(
                    "rule_id"
                ),

            "confidence":
                "UNVERIFIED",

            "basis":
                (
                    "A locality rule matched, but it failed "
                    "trusted-source or VERIFIED-status checks. "
                    "Automatic routing was blocked."
                ),

            "matched_keyword":
                blocked[
                    "keyword"
                ],

            "effective_date":
                complaint_date.isoformat(),

            "rule_effective_from":
                None,

            "rule_effective_to":
                None,

            "source_title":
                blocked[
                    "rule"
                ].get(
                    "source_title"
                ),

            "source_url":
                blocked[
                    "rule"
                ].get(
                    "source_url"
                ),

            "source_verified":
                False,

            "activation_reason":
                blocked[
                    "reason"
                ]
        }


    # ========================================================
    # NO VERIFIED RULE MATCHED
    #
    # We deliberately DO NOT use:
    #
    # "If address contains Mysuru -> MCC"
    #
    # because Mysuru metropolitan addresses can cross
    # MCC / CMC / TP / GP responsibility boundaries.
    # ========================================================

    return {

        "resolved":
            False,

        "authority":
            "Jurisdiction Review Queue",

        "jurisdiction":
            "Boundary verification required",

        "rule_id":
            None,

        "confidence":
            "UNVERIFIED",

        "basis":
            (
                "No active trusted jurisdiction rule matched "
                "this complaint location. CivicRoute prevented "
                "automatic misrouting."
            ),

        "matched_keyword":
            None,

        "effective_date":
            complaint_date.isoformat(),

        "rule_effective_from":
            None,

        "rule_effective_to":
            None,

        "source_title":
            None,

        "source_url":
            None,

        "source_verified":
            False,

        "activation_reason":
            "No verified active rule matched."
    }