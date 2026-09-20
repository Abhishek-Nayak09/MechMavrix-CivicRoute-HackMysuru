import os
import sqlite3
import secrets
import math

from datetime import (
    datetime,
    timezone,
    timedelta
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    BASE_DIR
)

DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "data"
)

UPLOAD_DIR = os.path.join(
    DATA_DIR,
    "uploads"
)

DATABASE_PATH = os.path.join(
    DATA_DIR,
    "civicroute.db"
)


# ============================================================
# VALID COMPLAINT STATUSES
# ============================================================

VALID_STATUSES = {
    "NEW",
    "ASSIGNED",
    "IN PROGRESS",
    "RESOLVED",
    "REJECTED",
    "REVIEW REQUIRED"
}


# ============================================================
# DIRECTORY SETUP
# ============================================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    return connection


# ============================================================
# DATABASE INITIALISATION
# ============================================================

def init_db():

    connection = (
        get_connection()
    )

    try:

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS complaints (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                complaint_id TEXT
                    NOT NULL
                    UNIQUE,

                created_at TEXT
                    NOT NULL,

                updated_at TEXT
                    NOT NULL,

                photo_path TEXT
                    NOT NULL,

                image_hash TEXT
                    NOT NULL,

                description TEXT,

                latitude REAL
                    NOT NULL,

                longitude REAL
                    NOT NULL,

                gps_accuracy REAL,

                detected_address TEXT,

                location_risk TEXT,

                location_score INTEGER,

                detected_issue TEXT,

                issue_confidence REAL,

                detected_severity TEXT,

                severity_confidence REAL,

                responsible_authority TEXT,

                jurisdiction TEXT,

                jurisdiction_confidence TEXT,

                jurisdiction_rule_id TEXT,

                department TEXT,

                priority TEXT,

                priority_score INTEGER,

                review_required INTEGER
                    NOT NULL
                    DEFAULT 0,

                status TEXT
                    NOT NULL
                    DEFAULT 'NEW',

                assigned_to TEXT,

                resolution_note TEXT,

                resolved_at TEXT
            );


            CREATE TABLE IF NOT EXISTS complaint_history (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                complaint_id TEXT
                    NOT NULL,

                timestamp TEXT
                    NOT NULL,

                event_type TEXT
                    NOT NULL,

                old_status TEXT,

                new_status TEXT,

                actor TEXT,

                note TEXT,

                FOREIGN KEY (
                    complaint_id
                )
                REFERENCES complaints (
                    complaint_id
                )
                ON DELETE CASCADE
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_status
            ON complaints (
                status
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_priority
            ON complaints (
                priority_score
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_created
            ON complaints (
                created_at
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_authority
            ON complaints (
                responsible_authority
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_location
            ON complaints (
                latitude,
                longitude
            );


            CREATE INDEX IF NOT EXISTS
                idx_complaints_image_hash
            ON complaints (
                image_hash
            );


            CREATE INDEX IF NOT EXISTS
                idx_history_complaint
            ON complaint_history (
                complaint_id
            );
            """
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# TIMESTAMP
# ============================================================

def current_timestamp():

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


# ============================================================
# GENERATE COMPLAINT ID
# ============================================================

def generate_complaint_id():

    date_part = (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y%m%d"
        )
    )

    while True:

        random_part = (
            secrets
            .token_hex(3)
            .upper()
        )

        complaint_id = (
            f"CR-{date_part}-{random_part}"
        )

        connection = (
            get_connection()
        )

        try:

            existing = (
                connection.execute(
                    """
                    SELECT complaint_id
                    FROM complaints
                    WHERE complaint_id = ?
                    """,
                    (
                        complaint_id,
                    )
                )
                .fetchone()
            )

        finally:

            connection.close()

        if existing is None:

            return complaint_id


# ============================================================
# HISTORY EVENT
# ============================================================

def add_history_event(
    connection,
    complaint_id,
    event_type,
    old_status=None,
    new_status=None,
    actor="System",
    note=None
):

    connection.execute(
        """
        INSERT INTO complaint_history (

            complaint_id,
            timestamp,
            event_type,
            old_status,
            new_status,
            actor,
            note

        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,

        (
            complaint_id,
            current_timestamp(),
            event_type,
            old_status,
            new_status,
            actor,
            note
        )
    )


# ============================================================
# DISTANCE HELPER
# ============================================================

def distance_in_metres(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2
):

    earth_radius = (
        6371000.0
    )

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
# EXACT PHOTO DUPLICATE CHECK
#
# Same image bytes + nearby location.
# This is strong evidence of an accidental/repeated submission.
# ============================================================

def find_exact_duplicate(
    image_hash,
    latitude,
    longitude,
    radius_metres=100
):

    connection = (
        get_connection()
    )

    try:

        rows = (
            connection.execute(
                """
                SELECT *
                FROM complaints

                WHERE image_hash = ?

                AND status NOT IN (
                    'REJECTED'
                )

                ORDER BY created_at DESC
                """,

                (
                    image_hash,
                )
            )
            .fetchall()
        )

    finally:

        connection.close()


    for row in rows:

        distance = (
            distance_in_metres(

                latitude,
                longitude,

                float(
                    row[
                        "latitude"
                    ]
                ),

                float(
                    row[
                        "longitude"
                    ]
                )
            )
        )


        if (
            distance <=
            radius_metres
        ):

            result = dict(
                row
            )

            result[
                "duplicate_distance_metres"
            ] = round(
                distance,
                1
            )

            result[
                "duplicate_reason"
            ] = (
                "Same photo evidence was already "
                "submitted from this area."
            )

            result[
                "duplicate_type"
            ] = (
                "EXACT_IMAGE"
            )

            return result


    return None


# ============================================================
# NEARBY RECENT DUPLICATE CHECK
#
# Same detected civic issue + very close location +
# recent unresolved complaint.
#
# It does NOT automatically prove fraud.
# It is used as duplicate-candidate protection.
# ============================================================

def find_nearby_duplicate(
    detected_issue,
    latitude,
    longitude,
    radius_metres=35,
    within_hours=24
):

    if not detected_issue:

        return None


    cutoff = (
        datetime.now(
            timezone.utc
        )
        -
        timedelta(
            hours=
                within_hours
        )
    ).isoformat()


    connection = (
        get_connection()
    )

    try:

        rows = (
            connection.execute(
                """
                SELECT *
                FROM complaints

                WHERE detected_issue = ?

                AND created_at >= ?

                AND status IN (
                    'NEW',
                    'ASSIGNED',
                    'IN PROGRESS',
                    'REVIEW REQUIRED'
                )

                ORDER BY created_at DESC
                """,

                (
                    detected_issue,
                    cutoff
                )
            )
            .fetchall()
        )

    finally:

        connection.close()


    for row in rows:

        distance = (
            distance_in_metres(

                latitude,
                longitude,

                float(
                    row[
                        "latitude"
                    ]
                ),

                float(
                    row[
                        "longitude"
                    ]
                )
            )
        )


        if (
            distance <=
            radius_metres
        ):

            result = dict(
                row
            )

            result[
                "duplicate_distance_metres"
            ] = round(
                distance,
                1
            )

            result[
                "duplicate_reason"
            ] = (
                "A recent unresolved complaint "
                "for the same detected issue exists nearby."
            )

            result[
                "duplicate_type"
            ] = (
                "NEARBY_RECENT"
            )

            return result


    return None


# ============================================================
# CREATE COMPLAINT
# ============================================================

def create_complaint(
    photo_path,
    image_hash,
    description,
    latitude,
    longitude,
    gps_accuracy,
    detected_address,
    location_risk,
    location_score,
    detected_issue,
    issue_confidence,
    detected_severity,
    severity_confidence,
    responsible_authority,
    jurisdiction,
    jurisdiction_confidence,
    jurisdiction_rule_id,
    department,
    priority,
    priority_score,
    review_required
):

    complaint_id = (
        generate_complaint_id()
    )

    timestamp = (
        current_timestamp()
    )


    status = (
        "REVIEW REQUIRED"

        if (
            review_required

            or

            responsible_authority ==
            "Jurisdiction Review Queue"
        )

        else
        "NEW"
    )


    connection = (
        get_connection()
    )

    try:

        connection.execute(
            """
            INSERT INTO complaints (

                complaint_id,
                created_at,
                updated_at,
                photo_path,
                image_hash,
                description,
                latitude,
                longitude,
                gps_accuracy,
                detected_address,
                location_risk,
                location_score,
                detected_issue,
                issue_confidence,
                detected_severity,
                severity_confidence,
                responsible_authority,
                jurisdiction,
                jurisdiction_confidence,
                jurisdiction_rule_id,
                department,
                priority,
                priority_score,
                review_required,
                status

            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,

            (
                complaint_id,
                timestamp,
                timestamp,
                photo_path,
                image_hash,
                description,
                latitude,
                longitude,
                gps_accuracy,
                detected_address,
                location_risk,
                location_score,
                detected_issue,
                issue_confidence,
                detected_severity,
                severity_confidence,
                responsible_authority,
                jurisdiction,
                jurisdiction_confidence,
                jurisdiction_rule_id,
                department,
                priority,
                priority_score,
                1 if review_required else 0,
                status
            )
        )


        add_history_event(

            connection=
                connection,

            complaint_id=
                complaint_id,

            event_type=
                "CREATED",

            old_status=
                None,

            new_status=
                status,

            actor=
                "CivicRoute System",

            note=(
                "Complaint received, analysed, "
                "prioritised and routed."
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()


    return complaint_id


# ============================================================
# GET COMPLAINT
# ============================================================

def get_complaint(
    complaint_id
):

    connection = (
        get_connection()
    )

    try:

        row = (
            connection.execute(
                """
                SELECT *
                FROM complaints
                WHERE complaint_id = ?
                """,

                (
                    complaint_id,
                )
            )
            .fetchone()
        )

        return row

    finally:

        connection.close()


# ============================================================
# GET HISTORY
# ============================================================

def get_complaint_history(
    complaint_id
):

    connection = (
        get_connection()
    )

    try:

        rows = (
            connection.execute(
                """
                SELECT *
                FROM complaint_history

                WHERE complaint_id = ?

                ORDER BY
                    id ASC
                """,

                (
                    complaint_id,
                )
            )
            .fetchall()
        )

        return rows

    finally:

        connection.close()


# ============================================================
# LIST COMPLAINTS
# ============================================================

def list_complaints(
    status=None,
    limit=200
):

    connection = (
        get_connection()
    )

    try:

        if status:

            rows = (
                connection.execute(
                    """
                    SELECT *
                    FROM complaints

                    WHERE status = ?

                    ORDER BY
                        priority_score DESC,
                        created_at DESC

                    LIMIT ?
                    """,

                    (
                        status,
                        limit
                    )
                )
                .fetchall()
            )

        else:

            rows = (
                connection.execute(
                    """
                    SELECT *
                    FROM complaints

                    ORDER BY
                        priority_score DESC,
                        created_at DESC

                    LIMIT ?
                    """,

                    (
                        limit,
                    )
                )
                .fetchall()
            )

        return rows

    finally:

        connection.close()


# ============================================================
# UPDATE STATUS
# ============================================================

def update_complaint_status(
    complaint_id,
    new_status,
    actor="Civic Staff",
    note=None
):

    new_status = (
        new_status
        .strip()
        .upper()
    )


    if (
        new_status
        not in VALID_STATUSES
    ):

        raise ValueError(
            f"Invalid status: {new_status}"
        )


    connection = (
        get_connection()
    )

    try:

        row = (
            connection.execute(
                """
                SELECT status
                FROM complaints
                WHERE complaint_id = ?
                """,

                (
                    complaint_id,
                )
            )
            .fetchone()
        )


        if row is None:

            return False


        old_status = (
            row[
                "status"
            ]
        )


        timestamp = (
            current_timestamp()
        )


        connection.execute(
            """
            UPDATE complaints

            SET
                status = ?,
                updated_at = ?

            WHERE complaint_id = ?
            """,

            (
                new_status,
                timestamp,
                complaint_id
            )
        )


        add_history_event(

            connection=
                connection,

            complaint_id=
                complaint_id,

            event_type=
                "STATUS UPDATED",

            old_status=
                old_status,

            new_status=
                new_status,

            actor=
                actor,

            note=
                note
        )


        connection.commit()

        return True


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()


# ============================================================
# ASSIGN COMPLAINT
# ============================================================

def assign_complaint(
    complaint_id,
    assigned_to,
    actor="Civic Staff"
):

    assigned_to = (
        assigned_to.strip()
    )


    if not assigned_to:

        raise ValueError(
            "Assigned officer/team is required."
        )


    connection = (
        get_connection()
    )

    try:

        row = (
            connection.execute(
                """
                SELECT status
                FROM complaints
                WHERE complaint_id = ?
                """,

                (
                    complaint_id,
                )
            )
            .fetchone()
        )


        if row is None:

            return False


        old_status = (
            row[
                "status"
            ]
        )


        timestamp = (
            current_timestamp()
        )


        connection.execute(
            """
            UPDATE complaints

            SET
                assigned_to = ?,
                status = 'ASSIGNED',
                updated_at = ?

            WHERE complaint_id = ?
            """,

            (
                assigned_to,
                timestamp,
                complaint_id
            )
        )


        add_history_event(

            connection=
                connection,

            complaint_id=
                complaint_id,

            event_type=
                "ASSIGNED",

            old_status=
                old_status,

            new_status=
                "ASSIGNED",

            actor=
                actor,

            note=(
                f"Assigned to "
                f"{assigned_to}."
            )
        )


        connection.commit()

        return True


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()


# ============================================================
# RESOLVE COMPLAINT
# ============================================================

def resolve_complaint(
    complaint_id,
    resolution_note,
    actor="Civic Staff"
):

    resolution_note = (
        resolution_note.strip()
    )


    if not resolution_note:

        raise ValueError(
            "Resolution note is required."
        )


    connection = (
        get_connection()
    )

    try:

        row = (
            connection.execute(
                """
                SELECT status
                FROM complaints
                WHERE complaint_id = ?
                """,

                (
                    complaint_id,
                )
            )
            .fetchone()
        )


        if row is None:

            return False


        old_status = (
            row[
                "status"
            ]
        )


        timestamp = (
            current_timestamp()
        )


        connection.execute(
            """
            UPDATE complaints

            SET
                status = 'RESOLVED',
                resolution_note = ?,
                resolved_at = ?,
                updated_at = ?

            WHERE complaint_id = ?
            """,

            (
                resolution_note,
                timestamp,
                timestamp,
                complaint_id
            )
        )


        add_history_event(

            connection=
                connection,

            complaint_id=
                complaint_id,

            event_type=
                "RESOLVED",

            old_status=
                old_status,

            new_status=
                "RESOLVED",

            actor=
                actor,

            note=
                resolution_note
        )


        connection.commit()

        return True


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()


# ============================================================
# NEARBY COMPLAINTS
# ============================================================

def get_nearby_complaints(
    latitude,
    longitude,
    radius_metres=100,
    limit=100
):

    connection = (
        get_connection()
    )

    try:

        rows = (
            connection.execute(
                """
                SELECT *
                FROM complaints

                ORDER BY created_at DESC

                LIMIT ?
                """,

                (
                    limit,
                )
            )
            .fetchall()
        )

    finally:

        connection.close()


    nearby = []


    for row in rows:

        distance = (
            distance_in_metres(

                latitude,
                longitude,

                float(
                    row[
                        "latitude"
                    ]
                ),

                float(
                    row[
                        "longitude"
                    ]
                )
            )
        )


        if (
            distance <=
            radius_metres
        ):

            item = dict(
                row
            )

            item[
                "distance_metres"
            ] = round(
                distance,
                1
            )

            nearby.append(
                item
            )


    return nearby


# ============================================================
# DASHBOARD STATS
# ============================================================

def get_dashboard_stats():

    connection = (
        get_connection()
    )

    try:

        total = (
            connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM complaints
                """
            )
            .fetchone()[
                "count"
            ]
        )


        rows = (
            connection.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS count

                FROM complaints

                GROUP BY status
                """
            )
            .fetchall()
        )


        by_status = {
            row[
                "status"
            ]:
            row[
                "count"
            ]

            for row in rows
        }


        return {

            "total":
                total,

            "new":
                by_status.get(
                    "NEW",
                    0
                ),

            "assigned":
                by_status.get(
                    "ASSIGNED",
                    0
                ),

            "in_progress":
                by_status.get(
                    "IN PROGRESS",
                    0
                ),

            "resolved":
                by_status.get(
                    "RESOLVED",
                    0
                ),

            "review_required":
                by_status.get(
                    "REVIEW REQUIRED",
                    0
                )
        }


    finally:

        connection.close()


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    init_db()

    print(
        "CivicRoute database ready:"
    )

    print(
        DATABASE_PATH
    )

    print(
        "Upload directory:"
    )

    print(
        UPLOAD_DIR
    )