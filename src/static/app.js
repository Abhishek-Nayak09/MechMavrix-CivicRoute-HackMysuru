// ============================================================
// MECHMAVRIX CIVICROUTE FRONTEND
//
// Features:
// - Photo evidence preview
// - Live GPS
// - Map preview
// - Client-side civic-context preview
// - Server-authoritative location verification
// - Complaint routing result
// - Complaint ID + status
// - Exact duplicate response support
// - Offline IndexedDB queue
// - Automatic reconnect sync
// ============================================================


// ============================================================
// DOM
// ============================================================

const form =
    document.getElementById(
        "complaintForm"
    );

const photoInput =
    document.getElementById(
        "photo"
    );

const photoPreviewContainer =
    document.getElementById(
        "photoPreviewContainer"
    );

const photoPreview =
    document.getElementById(
        "photoPreview"
    );

const locationButton =
    document.getElementById(
        "locationButton"
    );

const locationStatus =
    document.getElementById(
        "locationStatus"
    );

const submitButton =
    document.getElementById(
        "submitButton"
    );

const mapContainer =
    document.getElementById(
        "mapContainer"
    );

const mapLatitude =
    document.getElementById(
        "mapLatitude"
    );

const mapLongitude =
    document.getElementById(
        "mapLongitude"
    );

const resultSection =
    document.getElementById(
        "resultSection"
    );

const resultPhoto =
    document.getElementById(
        "resultPhoto"
    );

const complaintIdElement =
    document.getElementById(
        "complaintId"
    );

const complaintStatusElement =
    document.getElementById(
        "complaintStatus"
    );

const networkBanner =
    document.getElementById(
        "networkBanner"
    );

const networkStatusText =
    document.getElementById(
        "networkStatusText"
    );

const pendingQueueBadge =
    document.getElementById(
        "pendingQueueBadge"
    );


// ============================================================
// STATE
// ============================================================

let currentLatitude = null;
let currentLongitude = null;
let currentAccuracy = null;

let previewAddress = "";
let previewLocationRisk = "UNKNOWN";
let previewLocationScore = 0;
let previewNearbyContext = [];

let photoObjectUrl = null;

let locationWatchId = null;

let lastContextLatitude = null;
let lastContextLongitude = null;

let contextRefreshRunning = false;

let syncRunning = false;

let currentlyDisplayedOfflineId = null;


// ============================================================
// MAP STATE
// ============================================================

let liveMap = null;
let liveMarker = null;
let liveAccuracyCircle = null;

let resultMap = null;
let resultMarker = null;
let resultAccuracyCircle = null;

let authorityMarker = null;
let authorityLine = null;


// ============================================================
// AUTHORITY MAP DIRECTORY
//
// This directory is only for map display.
// Routing authority itself comes from the backend.
// ============================================================

const AUTHORITY_DIRECTORY = {

    "Hootagalli City Municipal Council": {

        queries: [

            "City Municipal Council Hootagalli Mysuru Karnataka 570018",

            "Hootagalli City Municipal Council Mysuru Karnataka 570018",

            "City Municipal Council Hootagalli Housing Board Colony Mysuru Karnataka 570018",

            "Hootagalli Municipal Office Mysuru Karnataka 570018"
        ],

        fallback: {

            latitude:
                12.33673,

            longitude:
                76.58476,

            address:
                "Hootagalli, Mysuru, Karnataka 570018",

            approximate:
                true
        }
    }
};


// ============================================================
// NETWORK STATUS
// ============================================================

async function updateNetworkBanner() {

    const online =
        navigator.onLine;


    networkBanner.classList.remove(
        "online",
        "offline"
    );


    if (online) {

        networkBanner.classList.add(
            "online"
        );

        networkStatusText.textContent =
            "Online — complaints will be submitted immediately";

    }

    else {

        networkBanner.classList.add(
            "offline"
        );

        networkStatusText.textContent =
            "Offline — complaint will be queued on this device";
    }


    try {

        const pendingCount =
            await countOfflineComplaints();


        pendingQueueBadge.textContent =
            `Pending offline reports: ${pendingCount}`;

    }

    catch (error) {

        console.warn(
            "Unable to read offline queue:",
            error
        );


        pendingQueueBadge.textContent =
            "Pending offline reports: unavailable";
    }
}


// ============================================================
// SUBMIT BUTTON
// ============================================================

function updateSubmitState() {

    const hasPhoto =
        photoInput.files &&
        photoInput.files.length > 0;


    const hasLocation =
        currentLatitude !== null &&
        currentLongitude !== null;


    submitButton.disabled =
        !(
            hasPhoto &&
            hasLocation
        );
}


// ============================================================
// PHOTO PREVIEW
// ============================================================

photoInput.addEventListener(
    "change",
    () => {

        if (
            !photoInput.files ||
            photoInput.files.length === 0
        ) {

            photoPreviewContainer.classList.add(
                "hidden"
            );

            updateSubmitState();

            return;
        }


        if (photoObjectUrl) {

            URL.revokeObjectURL(
                photoObjectUrl
            );
        }


        photoObjectUrl =
            URL.createObjectURL(
                photoInput.files[0]
            );


        photoPreview.src =
            photoObjectUrl;


        resultPhoto.src =
            photoObjectUrl;


        photoPreviewContainer.classList.remove(
            "hidden"
        );


        updateSubmitState();
    }
);


// ============================================================
// DISTANCE
// ============================================================

function distanceInMeters(
    lat1,
    lon1,
    lat2,
    lon2
) {

    const earthRadius =
        6371000;


    const toRadians =
        value =>
            value *
            Math.PI /
            180;


    const dLat =
        toRadians(
            lat2 - lat1
        );


    const dLon =
        toRadians(
            lon2 - lon1
        );


    const a =
        Math.sin(
            dLat / 2
        ) ** 2

        +

        Math.cos(
            toRadians(
                lat1
            )
        )

        *

        Math.cos(
            toRadians(
                lat2
            )
        )

        *

        Math.sin(
            dLon / 2
        ) ** 2;


    const c =
        2 *
        Math.atan2(
            Math.sqrt(
                a
            ),
            Math.sqrt(
                1 - a
            )
        );


    return (
        earthRadius *
        c
    );
}


function formatDistance(
    distance
) {

    if (
        distance < 1000
    ) {

        return (
            `${Math.round(
                distance
            )} m`
        );
    }


    return (
        `${(
            distance /
            1000
        ).toFixed(2)} km`
    );
}


// ============================================================
// CREATE MAP
// ============================================================

function createMap(
    elementId,
    latitude,
    longitude,
    zoom = 17
) {

    const map =
        L.map(
            elementId
        )
        .setView(
            [
                latitude,
                longitude
            ],
            zoom
        );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {

            maxZoom:
                19,

            attribution:
                "&copy; OpenStreetMap contributors"
        }
    )
    .addTo(
        map
    );


    return map;
}


// ============================================================
// LIVE MAP
// ============================================================

function updateLiveMap(
    latitude,
    longitude,
    accuracy
) {

    mapContainer.classList.remove(
        "hidden"
    );


    mapLatitude.textContent =
        latitude.toFixed(
            6
        );


    mapLongitude.textContent =
        longitude.toFixed(
            6
        );


    if (!liveMap) {

        liveMap =
            createMap(
                "liveMap",
                latitude,
                longitude
            );


        liveMarker =
            L.marker(
                [
                    latitude,
                    longitude
                ]
            )
            .addTo(
                liveMap
            );


        liveAccuracyCircle =
            L.circle(
                [
                    latitude,
                    longitude
                ],
                {

                    radius:
                        Math.max(
                            accuracy ||
                            10,
                            5
                        )
                }
            )
            .addTo(
                liveMap
            );

    }

    else {

        liveMarker.setLatLng(
            [
                latitude,
                longitude
            ]
        );


        liveAccuracyCircle.setLatLng(
            [
                latitude,
                longitude
            ]
        );


        liveAccuracyCircle.setRadius(
            Math.max(
                accuracy ||
                10,
                5
            )
        );


        liveMap.panTo(
            [
                latitude,
                longitude
            ]
        );
    }


    liveMarker.bindPopup(
        `
        <strong>📍 Complaint GPS</strong>
        <br>
        ${latitude.toFixed(6)},
        ${longitude.toFixed(6)}
        <br>
        Accuracy:
        ±${Math.round(
            accuracy || 0
        )} m
        `
    );


    setTimeout(
        () =>
            liveMap?.invalidateSize(),
        150
    );
}


// ============================================================
// RESULT MAP
// ============================================================

function updateResultMap(
    latitude,
    longitude,
    accuracy
) {

    if (!resultMap) {

        resultMap =
            createMap(
                "resultMap",
                latitude,
                longitude
            );


        resultMarker =
            L.marker(
                [
                    latitude,
                    longitude
                ]
            )
            .addTo(
                resultMap
            );


        resultAccuracyCircle =
            L.circle(
                [
                    latitude,
                    longitude
                ],
                {

                    radius:
                        Math.max(
                            accuracy ||
                            10,
                            5
                        )
                }
            )
            .addTo(
                resultMap
            );

    }

    else {

        resultMarker.setLatLng(
            [
                latitude,
                longitude
            ]
        );


        resultAccuracyCircle.setLatLng(
            [
                latitude,
                longitude
            ]
        );


        resultAccuracyCircle.setRadius(
            Math.max(
                accuracy ||
                10,
                5
            )
        );
    }


    resultMarker.bindPopup(
        `
        <strong>📍 Complaint Location</strong>
        <br>
        ${latitude.toFixed(6)},
        ${longitude.toFixed(6)}
        `
    );


    resultMap.setView(
        [
            latitude,
            longitude
        ],
        17
    );


    setTimeout(
        () =>
            resultMap?.invalidateSize(),
        200
    );
}


// ============================================================
// CLIENT PREVIEW — REVERSE GEOCODE
//
// Preview only.
// Backend independently derives authoritative address.
// ============================================================

async function reverseGeocodePreview(
    latitude,
    longitude
) {

    const url =
        "https://nominatim.openstreetmap.org/reverse" +
        "?format=jsonv2" +
        `&lat=${latitude}` +
        `&lon=${longitude}`;


    const response =
        await fetch(
            url,
            {
                headers: {
                    "Accept-Language":
                        "en"
                }
            }
        );


    if (!response.ok) {

        throw new Error(
            "Preview reverse geocoding unavailable."
        );
    }


    const data =
        await response.json();


    return (
        data.display_name ||
        `${latitude}, ${longitude}`
    );
}


// ============================================================
// AUTHORITY SEARCH
// ============================================================

async function searchAuthorityQuery(
    searchText
) {

    if (
        !navigator.onLine
    ) {

        return null;
    }


    const url =
        "https://nominatim.openstreetmap.org/search" +
        "?format=jsonv2" +
        "&limit=5" +
        "&countrycodes=in" +
        `&q=${encodeURIComponent(
            searchText
        )}`;


    const response =
        await fetch(
            url,
            {
                headers: {
                    "Accept-Language":
                        "en"
                }
            }
        );


    if (!response.ok) {

        return null;
    }


    const results =
        await response.json();


    if (
        !results ||
        results.length === 0
    ) {

        return null;
    }


    let place =
        results.find(
            result => {

                const text =
                    (
                        result.display_name ||
                        ""
                    )
                    .toLowerCase();


                return (
                    text.includes(
                        "hootagalli"
                    )

                    ||

                    text.includes(
                        "hutagalli"
                    )
                );
            }
        );


    if (!place) {

        place =
            results.find(
                result => {

                    const text =
                        (
                            result.display_name ||
                            ""
                        )
                        .toLowerCase();


                    return (
                        text.includes(
                            "mysuru"
                        )

                        ||

                        text.includes(
                            "mysore"
                        )
                    );
                }
            );
    }


    if (!place) {

        place =
            results[0];
    }


    const latitude =
        Number(
            place.lat
        );


    const longitude =
        Number(
            place.lon
        );


    if (
        !Number.isFinite(
            latitude
        )

        ||

        !Number.isFinite(
            longitude
        )
    ) {

        return null;
    }


    return {

        latitude,

        longitude,

        address:
            place.display_name,

        approximate:
            false
    };
}


// ============================================================
// FIND AUTHORITY OFFICE
// ============================================================

async function findAuthorityOffice(
    authorityName
) {

    if (
        !authorityName

        ||

        authorityName ===
        "Jurisdiction Review Queue"
    ) {

        return null;
    }


    const directory =
        AUTHORITY_DIRECTORY[
            authorityName
        ];


    const queries =
        directory?.queries
        ||
        [
            `${authorityName}, Mysuru, Karnataka, India`
        ];


    for (
        const query
        of queries
    ) {

        try {

            const result =
                await searchAuthorityQuery(
                    query
                );


            if (result) {

                return {

                    ...result,

                    name:
                        authorityName
                };
            }

        }

        catch (error) {

            console.warn(
                "Authority lookup failed:",
                query,
                error
            );
        }
    }


    if (
        directory?.fallback
    ) {

        return {

            name:
                authorityName,

            ...directory.fallback
        };
    }


    return null;
}


// ============================================================
// SHOW AUTHORITY
// ============================================================

async function showAuthorityOnResultMap(
    authorityName,
    complaintLatitude,
    complaintLongitude
) {

    if (!resultMap) {

        return;
    }


    if (authorityMarker) {

        resultMap.removeLayer(
            authorityMarker
        );

        authorityMarker =
            null;
    }


    if (authorityLine) {

        resultMap.removeLayer(
            authorityLine
        );

        authorityLine =
            null;
    }


    const office =
        await findAuthorityOffice(
            authorityName
        );


    if (!office) {

        resultMarker?.openPopup();

        return;
    }


    const distance =
        distanceInMeters(
            complaintLatitude,
            complaintLongitude,
            office.latitude,
            office.longitude
        );


    authorityMarker =
        L.circleMarker(
            [
                office.latitude,
                office.longitude
            ],
            {

                radius:
                    11,

                weight:
                    4,

                fillOpacity:
                    0.9
            }
        )
        .addTo(
            resultMap
        );


    const title =
        office.approximate
            ?
            "🏢 Responsible Authority Area"
            :
            "🏢 Responsible Civic Authority";


    const note =
        office.approximate
            ?
            `
            <br><br>
            Exact municipal-office point was not available
            from the map provider. This marker represents
            the authority area, not an exact office entrance.
            `
            :
            "";


    authorityMarker.bindPopup(
        `
        <strong>${title}</strong>
        <br><br>
        <strong>${authorityName}</strong>
        <br>
        ${office.address}
        <br><br>
        Distance from complaint:
        <strong>
            ${formatDistance(
                distance
            )}
        </strong>
        ${note}
        `
    );


    authorityLine =
        L.polyline(
            [
                [
                    complaintLatitude,
                    complaintLongitude
                ],

                [
                    office.latitude,
                    office.longitude
                ]
            ],
            {

                weight:
                    4,

                dashArray:
                    "10,8"
            }
        )
        .addTo(
            resultMap
        );


    const bounds =
        L.latLngBounds(
            [
                [
                    complaintLatitude,
                    complaintLongitude
                ],

                [
                    office.latitude,
                    office.longitude
                ]
            ]
        );


    resultMap.fitBounds(
        bounds,
        {

            padding:
                [
                    55,
                    55
                ],

            maxZoom:
                16
        }
    );


    authorityMarker.openPopup();


    setTimeout(
        () =>
            resultMap?.invalidateSize(),
        250
    );
}


// ============================================================
// CLIENT PREVIEW — NEARBY PLACES
//
// Preview only.
// Backend runs its own authoritative lookup.
// ============================================================

async function findNearbyCriticalPlacesPreview(
    latitude,
    longitude
) {

    const query = `
        [out:json][timeout:15];

        (
            nwr(
                around:150,
                ${latitude},
                ${longitude}
            )
            ["amenity"~"hospital|clinic|school|college|university|bus_station|marketplace"];

            nwr(
                around:150,
                ${latitude},
                ${longitude}
            )
            ["highway"="traffic_signals"];
        );

        out center tags;
    `;


    const response =
        await fetch(
            "https://overpass-api.de/api/interpreter",
            {

                method:
                    "POST",

                headers: {

                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },

                body:
                    "data=" +
                    encodeURIComponent(
                        query
                    )
            }
        );


    if (!response.ok) {

        throw new Error(
            "Nearby preview unavailable."
        );
    }


    const data =
        await response.json();


    return (
        data.elements ||
        []
    );
}


// ============================================================
// CLIENT PREVIEW — RISK
// ============================================================

function analyseLocationRiskPreview(
    elements,
    latitude,
    longitude
) {

    let highestScore =
        15;


    const context =
        [];


    elements.forEach(
        element => {

            const tags =
                element.tags ||
                {};


            const elementLatitude =
                element.lat
                ??
                element.center?.lat;


            const elementLongitude =
                element.lon
                ??
                element.center?.lon;


            if (
                elementLatitude ===
                undefined

                ||

                elementLongitude ===
                undefined
            ) {

                return;
            }


            const distance =
                distanceInMeters(
                    latitude,
                    longitude,
                    elementLatitude,
                    elementLongitude
                );


            if (
                distance >
                150
            ) {

                return;
            }


            const amenity =
                tags.amenity ||
                "";


            const highway =
                tags.highway ||
                "";


            const name =
                tags.name ||
                "Unnamed mapped place";


            let score = 0;
            let type = "";


            if (
                amenity ===
                "hospital"

                ||

                amenity ===
                "clinic"
            ) {

                type =
                    "Hospital / Emergency Zone";


                if (
                    distance <=
                    50
                ) {

                    score =
                        50;

                }

                else if (
                    distance <=
                    100
                ) {

                    score =
                        45;

                }

                else {

                    score =
                        38;
                }
            }


            else if (
                amenity ===
                "school"

                ||

                amenity ===
                "college"

                ||

                amenity ===
                "university"
            ) {

                type =
                    "School / Education Zone";


                if (
                    distance <=
                    50
                ) {

                    score =
                        47;

                }

                else if (
                    distance <=
                    100
                ) {

                    score =
                        42;

                }

                else {

                    score =
                        35;
                }
            }


            else if (
                highway ===
                "traffic_signals"
            ) {

                type =
                    "Traffic Junction";


                if (
                    distance <=
                    40
                ) {

                    score =
                        45;

                }

                else if (
                    distance <=
                    80
                ) {

                    score =
                        38;

                }

                else {

                    score =
                        30;
                }
            }


            else if (
                amenity ===
                "bus_station"
            ) {

                type =
                    "High Public Movement Zone";


                score =
                    distance <=
                    75
                        ?
                        43
                        :
                        34;
            }


            else if (
                amenity ===
                "marketplace"
            ) {

                type =
                    "Market / Public Activity Zone";


                score =
                    distance <=
                    75
                        ?
                        42
                        :
                        33;
            }


            if (
                score > 0
            ) {

                context.push({

                    name,

                    type,

                    distance:
                        Math.round(
                            distance
                        ),

                    score
                });


                highestScore =
                    Math.max(
                        highestScore,
                        score
                    );
            }
        }
    );


    context.sort(
        (a, b) =>
            a.distance -
            b.distance
    );


    let riskLevel =
        "LOW";


    if (
        highestScore >=
        45
    ) {

        riskLevel =
            "CRITICAL";

    }

    else if (
        highestScore >=
        35
    ) {

        riskLevel =
            "HIGH";

    }

    else if (
        highestScore >=
        25
    ) {

        riskLevel =
            "MEDIUM";
    }


    return {

        score:
            highestScore,

        level:
            riskLevel,

        nearby:
            context.slice(
                0,
                5
            )
    };
}


// ============================================================
// REFRESH PREVIEW CONTEXT
// ============================================================

async function refreshLocationContext(
    latitude,
    longitude
) {

    if (
        contextRefreshRunning
    ) {

        return;
    }


    contextRefreshRunning =
        true;


    try {

        if (
            !navigator.onLine
        ) {

            previewAddress =
                `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;


            previewLocationRisk =
                "PENDING SERVER VERIFICATION";


            previewLocationScore =
                0;


            previewNearbyContext =
                [];


            locationStatus.textContent =
                `Live GPS captured: ` +
                `${latitude.toFixed(6)}, ` +
                `${longitude.toFixed(6)}` +
                ` | Accuracy: ±${Math.round(
                    currentAccuracy || 0
                )} m` +
                ` | Offline — location context will be verified after sync`;


            return;
        }


        locationStatus.textContent =
            "GPS captured. Loading location preview...";


        previewAddress =
            await reverseGeocodePreview(
                latitude,
                longitude
            );


        const places =
            await findNearbyCriticalPlacesPreview(
                latitude,
                longitude
            );


        const analysis =
            analyseLocationRiskPreview(
                places,
                latitude,
                longitude
            );


        previewLocationScore =
            analysis.score;


        previewLocationRisk =
            analysis.level;


        previewNearbyContext =
            analysis.nearby;


        lastContextLatitude =
            latitude;


        lastContextLongitude =
            longitude;


        let nearbyText =
            "";


        if (
            previewNearbyContext.length >
            0
        ) {

            const nearest =
                previewNearbyContext[
                    0
                ];


            nearbyText =
                ` | Preview: ${nearest.type}` +
                ` (${nearest.distance} m)`;
        }


        locationStatus.textContent =
            `Live GPS: ` +
            `${latitude.toFixed(6)}, ` +
            `${longitude.toFixed(6)}` +
            ` | Accuracy: ±${Math.round(
                currentAccuracy || 0
            )} m` +
            ` | Preview risk: ${previewLocationRisk}` +
            nearbyText +
            ` | Server re-verifies on submit`;

    }

    catch (error) {

        console.warn(
            "Location preview error:",
            error
        );


        previewAddress =
            `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;


        previewLocationRisk =
            "PENDING SERVER VERIFICATION";


        previewLocationScore =
            0;


        previewNearbyContext =
            [];


        locationStatus.textContent =
            `Live GPS: ` +
            `${latitude.toFixed(6)}, ` +
            `${longitude.toFixed(6)}` +
            ` | Accuracy: ±${Math.round(
                currentAccuracy || 0
            )} m` +
            ` | Server will verify location context`;

    }

    finally {

        contextRefreshRunning =
            false;


        updateSubmitState();
    }
}


// ============================================================
// GPS UPDATE
// ============================================================

async function handleLocationUpdate(
    position
) {

    currentLatitude =
        position.coords.latitude;


    currentLongitude =
        position.coords.longitude;


    currentAccuracy =
        position.coords.accuracy;


    updateLiveMap(
        currentLatitude,
        currentLongitude,
        currentAccuracy
    );


    locationButton.textContent =
        "✓ Live Location Active";


    updateSubmitState();


    if (
        lastContextLatitude ===
        null

        ||

        lastContextLongitude ===
        null
    ) {

        await refreshLocationContext(
            currentLatitude,
            currentLongitude
        );

        return;
    }


    const moved =
        distanceInMeters(
            lastContextLatitude,
            lastContextLongitude,
            currentLatitude,
            currentLongitude
        );


    if (
        moved >= 30
    ) {

        await refreshLocationContext(
            currentLatitude,
            currentLongitude
        );

    }

    else {

        locationStatus.textContent =
            `Live GPS: ` +
            `${currentLatitude.toFixed(6)}, ` +
            `${currentLongitude.toFixed(6)}` +
            ` | Accuracy: ±${Math.round(
                currentAccuracy || 0
            )} m` +
            ` | Backend independently verifies location`;
    }
}


// ============================================================
// GPS ERROR
// ============================================================

function handleLocationError(
    error
) {

    let message =
        "Unable to capture GPS location.";


    if (
        error.code === 1
    ) {

        message =
            "Location permission denied. Please allow location access.";

    }

    else if (
        error.code === 2
    ) {

        message =
            "Current location is temporarily unavailable.";

    }

    else if (
        error.code === 3
    ) {

        message =
            "GPS request timed out. Please try again.";
    }


    locationStatus.textContent =
        message;


    locationButton.disabled =
        false;


    locationWatchId =
        null;


    updateSubmitState();
}


// ============================================================
// START GPS
// ============================================================

locationButton.addEventListener(
    "click",
    () => {

        if (
            !navigator.geolocation
        ) {

            locationStatus.textContent =
                "GPS is not supported by this browser.";

            return;
        }


        if (
            locationWatchId !==
            null
        ) {

            locationStatus.textContent =
                "Live GPS tracking is already active.";

            return;
        }


        locationButton.disabled =
            true;


        locationButton.textContent =
            "Starting Live GPS...";


        locationStatus.textContent =
            "Requesting current GPS location...";


        locationWatchId =
            navigator.geolocation.watchPosition(

                async position => {

                    locationButton.disabled =
                        false;


                    await handleLocationUpdate(
                        position
                    );
                },


                error => {

                    handleLocationError(
                        error
                    );
                },


                {

                    enableHighAccuracy:
                        true,

                    timeout:
                        15000,

                    maximumAge:
                        3000
                }
            );
    }
);


// ============================================================
// BUILD ONLINE FORM DATA
//
// IMPORTANT:
// location_score / location_risk / detected_address
// are intentionally NOT sent.
//
// Backend derives them independently.
// ============================================================

function buildSubmissionFormData(
    photoBlob,
    photoName,
    photoType,
    latitude,
    longitude,
    accuracy,
    description
) {

    const formData =
        new FormData();


    const file =
        photoBlob instanceof File

        ?

        photoBlob

        :

        new File(
            [
                photoBlob
            ],
            photoName ||
            "offline-report.jpg",
            {

                type:
                    photoType ||
                    photoBlob.type ||
                    "image/jpeg"
            }
        );


    formData.append(
        "photo",
        file
    );


    formData.append(
        "latitude",
        latitude
    );


    formData.append(
        "longitude",
        longitude
    );


    formData.append(
        "gps_accuracy",
        accuracy ?? ""
    );


    formData.append(
        "description",
        description ||
        ""
    );


    return formData;
}


// ============================================================
// POST COMPLAINT
// ============================================================

async function postComplaint(
    formData
) {

    const response =
        await fetch(
            "/api/analyze",
            {

                method:
                    "POST",

                body:
                    formData
            }
        );


    let data = null;


    try {

        data =
            await response.json();

    }

    catch {

        throw new Error(
            "Server returned an unreadable response."
        );
    }


    if (
        !response.ok ||
        !data.success
    ) {

        throw new Error(
            data?.details ||
            data?.error ||
            "Complaint submission failed."
        );
    }


    return data;
}


// ============================================================
// OFFLINE RESULT UI
// ============================================================

function showOfflineQueuedResult(
    record
) {

    currentlyDisplayedOfflineId =
        record.offline_id;


    complaintIdElement.textContent =
        record.offline_id;


    complaintStatusElement.textContent =
        "QUEUED OFFLINE";


    document.getElementById(
        "detectedIssue"
    ).textContent =
        "Pending server analysis";


    document.getElementById(
        "detectedSeverity"
    ).textContent =
        "Pending server analysis";


    document.getElementById(
        "locationRisk"
    ).textContent =
        "Pending server verification";


    document.getElementById(
        "authority"
    ).textContent =
        "Will be determined after sync";


    document.getElementById(
        "department"
    ).textContent =
        "Will be determined after sync";


    document.getElementById(
        "priority"
    ).textContent =
        "PENDING";


    document.getElementById(
        "priorityScore"
    ).textContent =
        "Pending analysis";


    document.getElementById(
        "detectedLocation"
    ).textContent =
        (
            previewAddress
            ||
            `${record.latitude}, ${record.longitude}`
        );


    document.getElementById(
        "priorityExplanation"
    ).textContent =
        (
            "Internet connection is unavailable. "
            +
            "This report and its photo evidence were saved "
            +
            "locally on this device. CivicRoute will "
            +
            "automatically sync it when connectivity returns. "
            +
            "Issue classification, server-side location verification, "
            +
            "jurisdiction routing and priority scoring will happen "
            +
            "after successful sync."
        );


    if (
        photoObjectUrl
    ) {

        resultPhoto.src =
            photoObjectUrl;
    }


    resultSection.classList.remove(
        "hidden"
    );


    updateResultMap(
        record.latitude,
        record.longitude,
        record.gps_accuracy
    );


    resultSection.scrollIntoView(
        {

            behavior:
                "smooth",

            block:
                "start"
        }
    );
}


// ============================================================
// RENDER SERVER RESULT
// ============================================================

async function renderServerResult(
    data,
    photoUrl = null
) {

    currentlyDisplayedOfflineId =
        null;


    complaintIdElement.textContent =
        data.complaint.complaint_id;


    complaintStatusElement.textContent =
        data.complaint.status;


    if (
        photoUrl
    ) {

        resultPhoto.src =
            photoUrl;

    }

    else if (
        photoObjectUrl
    ) {

        resultPhoto.src =
            photoObjectUrl;
    }


    document.getElementById(
        "detectedIssue"
    ).textContent =
        `${data.vision.issue} ` +
        `(${data.vision.issue_confidence}% confidence)`;


    document.getElementById(
        "detectedSeverity"
    ).textContent =
        `${data.vision.severity} ` +
        `(${data.vision.severity_confidence}% confidence)`;


    document.getElementById(
        "detectedLocation"
    ).textContent =
        data.location.address;


    document.getElementById(
        "locationRisk"
    ).textContent =
        `${data.location.risk} ` +
        `(${data.location.score}/50)`;


    document.getElementById(
        "authority"
    ).textContent =
        data.routing.authority;


    document.getElementById(
        "department"
    ).textContent =
        data.routing.department;


    document.getElementById(
        "priority"
    ).textContent =
        data.priority.level;


    document.getElementById(
        "priorityScore"
    ).textContent =
        `${data.priority.score}/100`;


    let explanation =
        data.priority.explanation;


    if (
        data.duplicate?.detected
    ) {

        if (
            data.duplicate.action ===
            "EXISTING_COMPLAINT_REUSED"
        ) {

            explanation +=
                ` Duplicate protection reused existing complaint ` +
                `${data.duplicate.existing_complaint_id}.`;

        }

        else if (
            data.duplicate.action ===
            "FLAGGED_FOR_REVIEW"
        ) {

            explanation +=
                ` A nearby recent complaint ` +
                `${data.duplicate.existing_complaint_id} ` +
                `was found, so this report was flagged for review.`;
        }
    }


    const serverNearby =
        data.location?.nearby ||
        [];


    if (
        serverNearby.length > 0
    ) {

        const nearest =
            serverNearby[0];


        explanation +=
            ` Server-side location context found ` +
            `${nearest.type} approximately ` +
            `${Math.round(
                nearest.distance_metres
            )} metres away.`;
    }


    document.getElementById(
        "priorityExplanation"
    ).textContent =
        explanation;


    resultSection.classList.remove(
        "hidden"
    );


    const resultLatitude =
        Number(
            data.gps.latitude
        );


    const resultLongitude =
        Number(
            data.gps.longitude
        );


    updateResultMap(
        resultLatitude,
        resultLongitude,
        data.gps.accuracy
    );


    await showAuthorityOnResultMap(
        data.routing.authority,
        resultLatitude,
        resultLongitude
    );


    resultSection.scrollIntoView(
        {

            behavior:
                "smooth",

            block:
                "start"
        }
    );
}


// ============================================================
// QUEUE OFFLINE COMPLAINT
// ============================================================

async function queueComplaintOffline() {

    const photo =
        photoInput.files[
            0
        ];


    const description =
        document
        .getElementById(
            "description"
        )
        .value
        .trim();


    const record =
        await saveOfflineComplaint({

            photo_blob:
                photo,

            photo_name:
                photo.name ||
                "complaint-photo.jpg",

            photo_type:
                photo.type ||
                "image/jpeg",

            latitude:
                currentLatitude,

            longitude:
                currentLongitude,

            gps_accuracy:
                currentAccuracy,

            description:
                description,

            preview_address:
                previewAddress,

            preview_location_risk:
                previewLocationRisk
        });


    await updateNetworkBanner();


    showOfflineQueuedResult(
        record
    );


    return record;
}


// ============================================================
// SYNC ONE OFFLINE RECORD
// ============================================================

async function syncOfflineRecord(
    record
) {

    const formData =
        buildSubmissionFormData(

            record.photo_blob,

            record.photo_name,

            record.photo_type,

            record.latitude,

            record.longitude,

            record.gps_accuracy,

            record.description
        );


    const data =
        await postComplaint(
            formData
        );


    await deleteOfflineComplaint(
        record.offline_id
    );


    return data;
}


// ============================================================
// AUTO SYNC OFFLINE QUEUE
// ============================================================

async function syncOfflineQueue() {

    if (
        syncRunning ||
        !navigator.onLine
    ) {

        return;
    }


    syncRunning =
        true;


    try {

        const records =
            await getOfflineComplaints();


        if (
            records.length === 0
        ) {

            await updateNetworkBanner();

            return;
        }


        networkStatusText.textContent =
            `Online — syncing ${records.length} queued report(s)...`;


        for (
            const record
            of records
        ) {

            if (
                !navigator.onLine
            ) {

                break;
            }


            try {

                const data =
                    await syncOfflineRecord(
                        record
                    );


                console.log(
                    "Offline complaint synced:",
                    record.offline_id,
                    "→",
                    data.complaint.complaint_id
                );


                if (
                    currentlyDisplayedOfflineId ===
                    record.offline_id
                ) {

                    let temporaryUrl = null;


                    if (
                        record.photo_blob
                    ) {

                        temporaryUrl =
                            URL.createObjectURL(
                                record.photo_blob
                            );
                    }


                    await renderServerResult(
                        data,
                        temporaryUrl
                    );


                    if (
                        temporaryUrl
                    ) {

                        setTimeout(
                            () =>
                                URL.revokeObjectURL(
                                    temporaryUrl
                                ),
                            5000
                        );
                    }
                }

            }

            catch (error) {

                console.error(
                    "Offline sync failed for",
                    record.offline_id,
                    error
                );


                // Leave failed record in IndexedDB.
                // Later reconnect/refresh can retry.
            }
        }

    }

    catch (error) {

        console.error(
            "Offline queue sync error:",
            error
        );

    }

    finally {

        syncRunning =
            false;


        await updateNetworkBanner();
    }
}


// ============================================================
// FORM SUBMISSION
// ============================================================

form.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        if (
            currentLatitude ===
            null

            ||

            currentLongitude ===
            null
        ) {

            alert(
                "Please capture your current GPS location."
            );

            return;
        }


        if (
            !photoInput.files ||
            photoInput.files.length ===
            0
        ) {

            alert(
                "Photo evidence is required."
            );

            return;
        }


        submitButton.disabled =
            true;


        try {

            // =================================================
            // OFFLINE
            // =================================================

            if (
                !navigator.onLine
            ) {

                submitButton.textContent =
                    "Saving report offline...";


                await queueComplaintOffline();


                submitButton.textContent =
                    "Queued Offline ✓";


                setTimeout(
                    () => {

                        submitButton.textContent =
                            "Analyse & Route Complaint";


                        updateSubmitState();

                    },
                    1800
                );


                return;
            }


            // =================================================
            // ONLINE
            // =================================================

            submitButton.textContent =
                "Verifying & routing complaint...";


            const photo =
                photoInput.files[
                    0
                ];


            const description =
                document
                .getElementById(
                    "description"
                )
                .value
                .trim();


            const formData =
                buildSubmissionFormData(

                    photo,

                    photo.name,

                    photo.type,

                    currentLatitude,

                    currentLongitude,

                    currentAccuracy,

                    description
                );


            const data =
                await postComplaint(
                    formData
                );


            await renderServerResult(
                data
            );

        }

        catch (error) {

            console.error(
                error
            );


            // -------------------------------------------------
            // NETWORK FAILED DURING SUBMIT
            //
            // Browser may still report navigator.onLine=true
            // while server/network request itself fails.
            // Queue the report rather than losing it.
            // -------------------------------------------------

            const likelyNetworkFailure =
                !navigator.onLine

                ||

                error instanceof TypeError

                ||

                String(
                    error.message
                )
                .toLowerCase()
                .includes(
                    "fetch"
                );


            if (
                likelyNetworkFailure
            ) {

                try {

                    await queueComplaintOffline();


                    alert(
                        "Connection was lost. Your complaint was safely queued on this device and will sync automatically."
                    );

                }

                catch (
                    queueError
                ) {

                    console.error(
                        queueError
                    );


                    alert(
                        "Connection failed and the complaint could not be saved offline: " +
                        queueError.message
                    );
                }

            }

            else {

                alert(
                    "Submission failed: " +
                    error.message
                );
            }

        }

        finally {

            submitButton.textContent =
                "Analyse & Route Complaint";


            updateSubmitState();
        }
    }
);


// ============================================================
// NETWORK EVENTS
// ============================================================

window.addEventListener(
    "online",
    async () => {

        await updateNetworkBanner();

        await syncOfflineQueue();
    }
);


window.addEventListener(
    "offline",
    async () => {

        await updateNetworkBanner();
    }
);


// ============================================================
// PAGE STARTUP
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        await updateNetworkBanner();


        if (
            navigator.onLine
        ) {

            await syncOfflineQueue();
        }
    }
);


// ============================================================
// CLEANUP
// ============================================================

window.addEventListener(
    "beforeunload",
    () => {

        if (
            locationWatchId !==
            null
        ) {

            navigator.geolocation.clearWatch(
                locationWatchId
            );
        }


        if (
            photoObjectUrl
        ) {

            URL.revokeObjectURL(
                photoObjectUrl
            );
        }
    }
);