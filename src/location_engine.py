import json
import math
import urllib.parse
import urllib.request


# ============================================================
# CONFIGURATION
# ============================================================

NOMINATIM_REVERSE_URL = (
    "https://nominatim.openstreetmap.org/reverse"
)

OVERPASS_URL = (
    "https://overpass-api.de/api/interpreter"
)

USER_AGENT = (
    "MechMavrix-CivicRoute-HackMysuru/1.0"
)

RISK_RADIUS_METRES = 150


# ============================================================
# DISTANCE
# ============================================================

def distance_in_metres(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):

    earth_radius = 6371000.0

    lat1 = math.radians(
        latitude_1
    )

    lat2 = math.radians(
        latitude_2
    )

    delta_lat = math.radians(
        latitude_2 -
        latitude_1
    )

    delta_lon = math.radians(
        longitude_2 -
        longitude_1
    )

    a = (
        math.sin(
            delta_lat / 2
        ) ** 2

        +

        math.cos(
            lat1
        )
        *
        math.cos(
            lat2
        )
        *
        math.sin(
            delta_lon / 2
        ) ** 2
    )

    c = (
        2
        *
        math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )
    )

    return (
        earth_radius * c
    )


# ============================================================
# HTTP JSON GET
# ============================================================

def fetch_json_get(
    url,
    timeout=10
):

    request = (
        urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    USER_AGENT,

                "Accept":
                    "application/json",

                "Accept-Language":
                    "en"
            }
        )
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        return json.loads(
            response.read()
            .decode(
                "utf-8"
            )
        )


# ============================================================
# HTTP JSON POST
# ============================================================

def fetch_json_post(
    url,
    form_data,
    timeout=15
):

    encoded = (
        urllib.parse.urlencode(
            form_data
        )
        .encode(
            "utf-8"
        )
    )

    request = (
        urllib.request.Request(
            url,
            data=encoded,
            headers={
                "User-Agent":
                    USER_AGENT,

                "Accept":
                    "application/json",

                "Content-Type":
                    "application/x-www-form-urlencoded"
            },
            method="POST"
        )
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        return json.loads(
            response.read()
            .decode(
                "utf-8"
            )
        )


# ============================================================
# SERVER-SIDE REVERSE GEOCODING
# ============================================================

def reverse_geocode(
    latitude,
    longitude
):

    parameters = {
        "format":
            "jsonv2",

        "lat":
            latitude,

        "lon":
            longitude,

        "zoom":
            18,

        "addressdetails":
            1
    }

    url = (
        NOMINATIM_REVERSE_URL
        +
        "?"
        +
        urllib.parse.urlencode(
            parameters
        )
    )

    data = (
        fetch_json_get(
            url,
            timeout=10
        )
    )

    display_name = (
        data.get(
            "display_name"
        )
    )

    if not display_name:

        raise RuntimeError(
            "Reverse geocoder returned no address."
        )

    return {
        "address":
            display_name,

        "raw_address":
            data.get(
                "address",
                {}
            )
    }


# ============================================================
# SERVER-SIDE NEARBY CIVIC CONTEXT
# ============================================================

def fetch_nearby_places(
    latitude,
    longitude
):

    query = f"""
        [out:json][timeout:15];

        (
            nwr(
                around:{RISK_RADIUS_METRES},
                {latitude},
                {longitude}
            )
            ["amenity"~"hospital|clinic|school|college|university|bus_station|marketplace"];

            nwr(
                around:{RISK_RADIUS_METRES},
                {latitude},
                {longitude}
            )
            ["highway"="traffic_signals"];
        );

        out center tags;
    """

    data = (
        fetch_json_post(
            OVERPASS_URL,
            {
                "data":
                    query
            },
            timeout=18
        )
    )

    return (
        data.get(
            "elements",
            []
        )
    )


# ============================================================
# LOCATION RISK ENGINE
#
# Location is weighted most heavily:
# max 50 points.
# ============================================================

def analyse_location_risk(
    elements,
    latitude,
    longitude
):

    highest_score = 15

    nearby_context = []


    for element in elements:

        tags = (
            element.get(
                "tags",
                {}
            )
        )

        element_latitude = (
            element.get(
                "lat"
            )
        )

        element_longitude = (
            element.get(
                "lon"
            )
        )


        if (
            element_latitude is None
            or
            element_longitude is None
        ):

            center = (
                element.get(
                    "center",
                    {}
                )
            )

            element_latitude = (
                center.get(
                    "lat"
                )
            )

            element_longitude = (
                center.get(
                    "lon"
                )
            )


        if (
            element_latitude is None
            or
            element_longitude is None
        ):

            continue


        distance = (
            distance_in_metres(
                latitude,
                longitude,
                float(
                    element_latitude
                ),
                float(
                    element_longitude
                )
            )
        )


        if (
            distance >
            RISK_RADIUS_METRES
        ):

            continue


        amenity = (
            tags.get(
                "amenity",
                ""
            )
        )

        highway = (
            tags.get(
                "highway",
                ""
            )
        )

        name = (
            tags.get(
                "name"
            )
            or
            "Unnamed mapped place"
        )


        score = 0
        place_type = ""


        # ----------------------------------------------------
        # HOSPITAL / CLINIC
        # ----------------------------------------------------

        if amenity in [
            "hospital",
            "clinic"
        ]:

            place_type = (
                "Hospital / Emergency Zone"
            )

            if distance <= 50:

                score = 50

            elif distance <= 100:

                score = 45

            else:

                score = 38


        # ----------------------------------------------------
        # EDUCATION
        # ----------------------------------------------------

        elif amenity in [
            "school",
            "college",
            "university"
        ]:

            place_type = (
                "School / Education Zone"
            )

            if distance <= 50:

                score = 47

            elif distance <= 100:

                score = 42

            else:

                score = 35


        # ----------------------------------------------------
        # TRAFFIC SIGNAL
        # ----------------------------------------------------

        elif (
            highway ==
            "traffic_signals"
        ):

            place_type = (
                "Traffic Junction"
            )

            if distance <= 40:

                score = 45

            elif distance <= 80:

                score = 38

            else:

                score = 30


        # ----------------------------------------------------
        # BUS STATION
        # ----------------------------------------------------

        elif (
            amenity ==
            "bus_station"
        ):

            place_type = (
                "High Public Movement Zone"
            )

            score = (
                43
                if distance <= 75
                else 34
            )


        # ----------------------------------------------------
        # MARKETPLACE
        # ----------------------------------------------------

        elif (
            amenity ==
            "marketplace"
        ):

            place_type = (
                "Market / Public Activity Zone"
            )

            score = (
                42
                if distance <= 75
                else 33
            )


        if score <= 0:

            continue


        highest_score = max(
            highest_score,
            score
        )


        nearby_context.append({
            "name":
                name,

            "type":
                place_type,

            "distance_metres":
                round(
                    distance,
                    1
                ),

            "risk_score":
                score
        })


    nearby_context.sort(
        key=lambda item:
            item[
                "distance_metres"
            ]
    )


    if highest_score >= 45:

        risk_level = (
            "CRITICAL"
        )

    elif highest_score >= 35:

        risk_level = (
            "HIGH"
        )

    elif highest_score >= 25:

        risk_level = (
            "MEDIUM"
        )

    else:

        risk_level = (
            "LOW"
        )


    return {
        "risk":
            risk_level,

        "score":
            highest_score,

        "nearby":
            nearby_context[:5]
    }


# ============================================================
# AUTHORITATIVE SERVER-SIDE LOCATION ANALYSIS
#
# Browser location context is only for UI preview.
# Backend result from GPS coordinates is authoritative.
# ============================================================

def verify_location_context(
    latitude,
    longitude
):

    result = {
        "latitude":
            latitude,

        "longitude":
            longitude,

        "address":
            (
                f"{latitude:.6f}, "
                f"{longitude:.6f}"
            ),

        "risk":
            "UNVERIFIED",

        "score":
            15,

        "nearby":
            [],

        "address_verified":
            False,

        "risk_verified":
            False,

        "context_verified":
            False,

        "verification_notes":
            []
    }


    # --------------------------------------------------------
    # SERVER-SIDE ADDRESS
    # --------------------------------------------------------

    try:

        address_result = (
            reverse_geocode(
                latitude,
                longitude
            )
        )

        result[
            "address"
        ] = (
            address_result[
                "address"
            ]
        )

        result[
            "address_verified"
        ] = True

        result[
            "verification_notes"
        ].append(
            "Address derived server-side from GPS coordinates."
        )

    except Exception as error:

        result[
            "verification_notes"
        ].append(
            "Server-side address lookup unavailable: "
            +
            str(
                error
            )
        )


    # --------------------------------------------------------
    # SERVER-SIDE PUBLIC-RISK CONTEXT
    # --------------------------------------------------------

    try:

        elements = (
            fetch_nearby_places(
                latitude,
                longitude
            )
        )

        risk_result = (
            analyse_location_risk(
                elements,
                latitude,
                longitude
            )
        )

        result[
            "risk"
        ] = (
            risk_result[
                "risk"
            ]
        )

        result[
            "score"
        ] = (
            risk_result[
                "score"
            ]
        )

        result[
            "nearby"
        ] = (
            risk_result[
                "nearby"
            ]
        )

        result[
            "risk_verified"
        ] = True

        result[
            "verification_notes"
        ].append(
            "Nearby public-risk context calculated server-side."
        )

    except Exception as error:

        result[
            "verification_notes"
        ].append(
            "Server-side nearby-place lookup unavailable: "
            +
            str(
                error
            )
        )


    # --------------------------------------------------------
    # SAFE VERIFICATION GATE
    # --------------------------------------------------------

    result[
        "context_verified"
    ] = (
        result[
            "address_verified"
        ]
        and
        result[
            "risk_verified"
        ]
    )


    if not result[
        "context_verified"
    ]:

        result[
            "risk"
        ] = (
            "UNVERIFIED"
        )

        # Conservative fallback.
        # It is NOT treated as verified priority evidence.
        result[
            "score"
        ] = 15


    return result


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    # Sample Mysuru coordinate only for module smoke testing.
    test_result = (
        verify_location_context(
            12.3415,
            76.5762
        )
    )

    print(
        json.dumps(
            test_result,
            indent=2
        )
    )