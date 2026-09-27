import os
import re
import sqlite3
import logging
from flask import Flask, jsonify, request

# ============================================================
# ALFA X PIN CODE LOOKUP API
# Developer: ADITYA SINGH RAJPUT
# Username : @ALFA_X_1801
# Channel  : @ALFAXMODES0118
# ============================================================

app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "alfa_x_pincode.db"
)

API_NAME = "ALFA X PIN CODE LOOKUP API"

DEVELOPER_NAME = "ADITYA SINGH RAJPUT"
DEVELOPER_USERNAME = "@ALFA_X_1801"
CHANNEL_USERNAME = "@ALFAXMODES0118"
POWERED_BY = "ALFA X MODES"

COUNTRY = "India"

# Create database directory
os.makedirs(DATABASE_DIR, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("alfa_x_pincode")


# ============================================================
# DATABASE
# ============================================================

def get_db():
    """
    Open SQLite database connection.
    """

    conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():
    """
    Create all required tables and indexes.
    """

    conn = get_db()

    cursor = conn.cursor()

    # --------------------------------------------------------
    # PINCODE MASTER TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pincodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pincode TEXT NOT NULL UNIQUE,

            state TEXT,
            district TEXT,
            region TEXT,
            circle TEXT,
            division TEXT,
            country TEXT DEFAULT 'India',

            source TEXT,
            source_updated_at TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------------
    # POST OFFICES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_offices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pincode TEXT NOT NULL,

            office_name TEXT,
            office_type TEXT,
            branch_type TEXT,
            delivery_status TEXT,

            division TEXT,
            region TEXT,
            circle TEXT,

            district TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',

            source TEXT,
            source_updated_at TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (pincode)
                REFERENCES pincodes(pincode)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # LOCALITIES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS localities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pincode TEXT NOT NULL,

            locality TEXT,
            village TEXT,
            sub_district TEXT,
            tehsil TEXT,
            taluk TEXT,
            block TEXT,

            district TEXT,
            state TEXT,

            latitude REAL,
            longitude REAL,

            source TEXT,
            source_updated_at TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (pincode)
                REFERENCES pincodes(pincode)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # POLICE STATIONS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS police_stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pincode TEXT NOT NULL,

            police_station TEXT,
            police_station_code TEXT,

            district TEXT,
            state TEXT,

            latitude REAL,
            longitude REAL,

            source TEXT,
            source_updated_at TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (pincode)
                REFERENCES pincodes(pincode)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------------
    # SEARCH INDEXES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pincodes_pincode
        ON pincodes(pincode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_post_offices_pincode
        ON post_offices(pincode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_localities_pincode
        ON localities(pincode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_police_pincode
        ON police_stations(pincode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_post_office_name
        ON post_offices(office_name)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_locality_name
        ON localities(locality)
    """)

    conn.commit()
    conn.close()

    logger.info("Database initialized: %s", DATABASE_FILE)


# Initialize database when application starts
initialize_database()


# ============================================================
# COMMON RESPONSE
# ============================================================

def branding():
    return {
        "developer": {
            "name": DEVELOPER_NAME,
            "username": DEVELOPER_USERNAME
        },
        "channel": CHANNEL_USERNAME,
        "powered_by": POWERED_BY
    }


def success_response(data):
    response = {
        "status": "success",
        "api": API_NAME,
        **data,
        **branding()
    }

    return jsonify(response)


def error_response(
    message,
    status_code=400,
    pincode=None
):

    response = {
        "status": "error",
        "api": API_NAME,
        "message": message
    }

    if pincode is not None:
        response["pincode"] = pincode

    response.update(branding())

    return jsonify(response), status_code


# ============================================================
# VALIDATE PIN
# ============================================================

def valid_pincode(pincode):

    if not pincode:
        return False

    return bool(
        re.fullmatch(
            r"[0-9]{6}",
            str(pincode)
        )
    )


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return success_response({

        "message": "API is running successfully",

        "documentation": {
            "lookup": "/api/pincode/<6_digit_pincode>",
            "search": "/api/search?q=<query>",
            "health": "/health"
        },

        "example": (
            "/api/pincode/823001"
        )
    })


# ============================================================
# HEALTH
# ============================================================

@app.route("/health", methods=["GET"])
def health():

    try:

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) AS total FROM pincodes"
        )

        total_pincodes = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM post_offices"
        )

        total_offices = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM localities"
        )

        total_localities = cursor.fetchone()["total"]

        conn.close()

        return success_response({

            "service": "online",

            "database": {
                "status": "connected",
                "pincodes": total_pincodes,
                "post_offices": total_offices,
                "localities": total_localities
            }

        })

    except Exception as e:

        logger.exception(
            "Health check failed"
        )

        return error_response(
            "Database unavailable.",
            503
        )


# ============================================================
# PINCODE LOOKUP
# ============================================================

@app.route(
    "/api/pincode/<pincode>",
    methods=["GET"]
)
def pincode_lookup(pincode):

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    pincode = str(pincode).strip()

    if not valid_pincode(pincode):

        return error_response(
            "Invalid PIN code. PIN must contain exactly 6 digits.",
            400,
            pincode
        )

    conn = None

    try:

        conn = get_db()

        cursor = conn.cursor()

        # ----------------------------------------------------
        # PIN MASTER
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                pincode,
                state,
                district,
                region,
                circle,
                division,
                country,
                source,
                source_updated_at
            FROM pincodes
            WHERE pincode = ?
        """, (pincode,))

        pin_row = cursor.fetchone()

        if not pin_row:

            return error_response(
                "PIN code not found in the database.",
                404,
                pincode
            )

        # ----------------------------------------------------
        # POST OFFICES
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                office_name,
                office_type,
                branch_type,
                delivery_status,
                division,
                region,
                circle,
                district,
                state,
                country,
                source,
                source_updated_at
            FROM post_offices
            WHERE pincode = ?
            ORDER BY office_name
        """, (pincode,))

        post_office_rows = cursor.fetchall()

        post_offices = []

        for row in post_office_rows:

            post_offices.append({

                "name": row["office_name"],

                "office_type": row["office_type"],

                "branch_type": row["branch_type"],

                "delivery_status": row["delivery_status"],

                "division": row["division"],

                "region": row["region"],

                "circle": row["circle"],

                "district": row["district"],

                "state": row["state"],

                "country": row["country"]

            })

        # ----------------------------------------------------
        # LOCALITIES
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                locality,
                village,
                sub_district,
                tehsil,
                taluk,
                block,
                district,
                state,
                latitude,
                longitude,
                source,
                source_updated_at
            FROM localities
            WHERE pincode = ?
            ORDER BY locality, village
        """, (pincode,))

        locality_rows = cursor.fetchall()

        localities = []

        for row in locality_rows:

            localities.append({

                "locality": row["locality"],

                "village": row["village"],

                "sub_district": row["sub_district"],

                "tehsil": row["tehsil"],

                "taluk": row["taluk"],

                "block": row["block"],

                "district": row["district"],

                "state": row["state"],

                "coordinates": {

                    "latitude": row["latitude"],

                    "longitude": row["longitude"]

                }

                if (
                    row["latitude"] is not None
                    and row["longitude"] is not None
                )

                else None

            })

        # ----------------------------------------------------
        # POLICE STATIONS
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                police_station,
                police_station_code,
                district,
                state,
                latitude,
                longitude,
                source,
                source_updated_at
            FROM police_stations
            WHERE pincode = ?
            ORDER BY police_station
        """, (pincode,))

        police_rows = cursor.fetchall()

        police_stations = []

        for row in police_rows:

            police_stations.append({

                "name": row["police_station"],

                "code": row["police_station_code"],

                "district": row["district"],

                "state": row["state"],

                "coordinates": {

                    "latitude": row["latitude"],

                    "longitude": row["longitude"]

                }

                if (
                    row["latitude"] is not None
                    and row["longitude"] is not None
                )

                else None

            })

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        response_data = {

            "pincode": pin_row["pincode"],

            "location": {

                "state": pin_row["state"],

                "district": pin_row["district"],

                "region": pin_row["region"],

                "circle": pin_row["circle"],

                "division": pin_row["division"],

                "country": pin_row["country"]

            },

            "post_offices": post_offices,

            "localities": localities,

            "police_stations": police_stations,

            "statistics": {

                "post_offices":
                    len(post_offices),

                "localities":
                    len(localities),

                "police_stations":
                    len(police_stations)

            },

            "data_source": {

                "source": pin_row["source"],

                "last_updated":
                    pin_row["source_updated_at"]

            }

        }

        return success_response(
            response_data
        )

    except sqlite3.Error:

        logger.exception(
            "SQLite error"
        )

        return error_response(
            "Database error.",
            500,
            pincode
        )

    except Exception:

        logger.exception(
            "Unexpected lookup error"
        )

        return error_response(
            "Internal server error.",
            500,
            pincode
        )

    finally:

        if conn:

            conn.close()


# ============================================================
# SEARCH
# ============================================================

@app.route(
    "/api/search",
    methods=["GET"]
)
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return error_response(
            "Search query is required. Example: /api/search?q=Patna",
            400
        )

    if len(query) < 2:

        return error_response(
            "Search query must contain at least 2 characters.",
            400
        )

    # Prevent extremely large queries
    query = query[:100]

    conn = None

    try:

        conn = get_db()

        cursor = conn.cursor()

        pattern = f"%{query}%"

        cursor.execute("""
            SELECT DISTINCT
                pincode,
                office_name,
                district,
                state,
                division,
                region,
                circle
            FROM post_offices
            WHERE
                office_name LIKE ?
                OR district LIKE ?
                OR state LIKE ?
                OR division LIKE ?
                OR region LIKE ?
                OR circle LIKE ?
            ORDER BY
                state,
                district,
                office_name
            LIMIT 50
        """, (
            pattern,
            pattern,
            pattern,
            pattern,
            pattern,
            pattern
        ))

        rows = cursor.fetchall()

        results = []

        for row in rows:

            results.append({

                "pincode": row["pincode"],

                "post_office":
                    row["office_name"],

                "district":
                    row["district"],

                "state":
                    row["state"],

                "division":
                    row["division"],

                "region":
                    row["region"],

                "circle":
                    row["circle"]

            })

        return success_response({

            "query": query,

            "count": len(results),

            "results": results

        })

    except Exception:

        logger.exception(
            "Search failed"
        )

        return error_response(
            "Search service unavailable.",
            500
        )

    finally:

        if conn:

            conn.close()


# ============================================================
# API 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return error_response(
        "Endpoint not found.",
        404
    )


# ============================================================
# API 405
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return error_response(
        "HTTP method not allowed.",
        405
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
        )
