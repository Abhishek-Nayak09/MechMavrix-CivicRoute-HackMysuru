from urllib.parse import urlparse


# ============================================================
# TRUSTED GOVERNMENT SOURCES
# ============================================================

TRUSTED_DOMAINS = {
    "mysore.nic.in",
    "karnataka.gov.in",
    "sujala3lri.karnataka.gov.in",
    "kgis.ksrsac.in"
}


# ============================================================
# OFFICIAL SOURCE REGISTRY
# ============================================================

BOUNDARY_SOURCES = [

    {
        "name":
            "Mysuru District Official Notifications",

        "url":
            "https://mysore.nic.in/",

        "type":
            "Government Notification / District Portal",

        "authority":
            "District Mysuru, Government of Karnataka",

        "machine_readable":
            False,

        "purpose":
            "Track official municipal notifications and jurisdiction changes."
    },

    {
        "name":
            "Karnataka Government Geoportal",

        "url":
            "https://sujala3lri.karnataka.gov.in/",

        "type":
            "Government GIS / Boundary Dataset",

        "authority":
            "Government of Karnataka",

        "machine_readable":
            True,

        "purpose":
            "Download official administrative boundary datasets such as KML and shapefiles."
    }

]


# ============================================================
# DOMAIN VALIDATION
# ============================================================

def is_trusted_source(url):

    if not url:
        return False

    try:

        parsed = urlparse(
            url
        )

        hostname = (
            parsed.hostname or ""
        ).lower()

        if hostname in TRUSTED_DOMAINS:
            return True

        for domain in TRUSTED_DOMAINS:

            if hostname.endswith(
                "." + domain
            ):
                return True

        return False

    except Exception:
        return False


# ============================================================
# RULE PROVENANCE VALIDATION
# ============================================================

def validate_rule_provenance(rule):

    required_fields = [
        "source_url",
        "source_title",
        "effective_from"
    ]

    missing = [

        field

        for field in required_fields

        if not rule.get(field)

    ]


    if missing:

        return {

            "valid":
                False,

            "reason":
                "Missing required provenance fields: "
                + ", ".join(missing)
        }


    source_url = rule[
        "source_url"
    ]


    if not is_trusted_source(
        source_url
    ):

        return {

            "valid":
                False,

            "reason":
                "Boundary rule source is not from an approved government domain."
        }


    return {

        "valid":
            True,

        "reason":
            "Boundary rule has trusted government-source provenance."
    }


# ============================================================
# DATASET VERSION VALIDATION
# ============================================================

def validate_dataset_version(
    dataset
):

    required_fields = [
        "dataset_id",
        "version",
        "source_url",
        "retrieved_at",
        "effective_from"
    ]


    missing = [

        field

        for field in required_fields

        if not dataset.get(field)

    ]


    if missing:

        return {

            "valid":
                False,

            "reason":
                "Missing dataset metadata: "
                + ", ".join(missing)
        }


    if not is_trusted_source(
        dataset[
            "source_url"
        ]
    ):

        return {

            "valid":
                False,

            "reason":
                "Dataset source is not an approved government source."
        }


    return {

        "valid":
            True,

        "reason":
            "Dataset version metadata and government provenance verified."
    }


# ============================================================
# SAFE ACTIVATION CHECK
# ============================================================

def can_activate_boundary_rule(
    rule
):

    verification = (
        validate_rule_provenance(
            rule
        )
    )


    if not verification[
        "valid"
    ]:

        return {

            "activate":
                False,

            "reason":
                verification[
                    "reason"
                ]
        }


    if rule.get(
        "status"
    ) != "VERIFIED":

        return {

            "activate":
                False,

            "reason":
                "Boundary rule is not marked VERIFIED."
        }


    return {

        "activate":
            True,

        "reason":
            "Rule passed provenance and verification checks."
    }