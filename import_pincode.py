"""
ALFA X PIN CODE LOOKUP API
Official India Post / Government data importer

Developer:
ADITYA SINGH RAJPUT
@ALFA_X_1801
"""

import csv
import os
import sqlite3
from datetime import datetime


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_DIR = os.path.join(
    BASE_DIR,
    "database"
)

DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "alfa_x_pincode.db"
)

CSV_FILE = os.path.join(
    BASE_DIR,
    "pincode_data.csv"
)

SOURCE = "India Post / Government OGD"


def database():

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    conn = sqlite3.connect(
        DATABASE_FILE
    )

    return conn


def create_tables(conn):

    cursor = conn.cursor()

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_pincode
        ON pincodes(pincode)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_post_office_pincode
        ON post_offices(pincode)
    """)

    conn.commit()


def clean(value):

    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def import_csv():

    if not os.path.exists(CSV_FILE):

        print()
        print("======================================")
        print("PIN CODE CSV NOT FOUND")
        print("======================================")
        print()
        print(
            "Expected file:"
        )
        print(
            "pincode_data.csv"
        )
        print()
        print(
            "Put the official India Post"
        )
        print(
            "dataset in the project root."
        )
        print()

        return

    conn = database()

    create_tables(conn)

    cursor = conn.cursor()

    imported = 0

    skipped = 0

    now = datetime.utcnow().isoformat()

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            pincode = clean(
                row.get("Pincode")
                or row.get("PINCODE")
                or row.get("pincode")
                or row.get("PinCode")
            )

            if not pincode:
                skipped += 1
                continue

            pincode = pincode.zfill(6)

            if len(pincode) != 6:
                skipped += 1
                continue

            state = clean(
                row.get("StateName")
                or row.get("State Name")
                or row.get("State")
                or row.get("state")
            )

            district = clean(
                row.get("District")
                or row.get("district")
            )

            region = clean(
                row.get("RegionName")
                or row.get("Region Name")
                or row.get("Region")
            )

            circle = clean(
                row.get("CircleName")
                or row.get("Circle Name")
                or row.get("Circle")
            )

            division = clean(
                row.get("DivisionName")
                or row.get("Division Name")
                or row.get("Division")
            )

            office_name = clean(
                row.get("OfficeName")
                or row.get("Office Name")
                or row.get("Name")
            )

            office_type = clean(
                row.get("OfficeType")
                or row.get("Office Type")
            )

            delivery = clean(
                row.get("Delivery")
                or row.get("DeliveryStatus")
                or row.get("Delivery Status")
            )

            cursor.execute("""
                INSERT OR IGNORE INTO pincodes (
                    pincode,
                    state,
                    district,
                    region,
                    circle,
                    division,
                    country,
                    source,
                    source_updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pincode,
                state,
                district,
                region,
                circle,
                division,
                "India",
                SOURCE,
                now
            ))

            cursor.execute("""
                INSERT INTO post_offices (
                    pincode,
                    office_name,
                    office_type,
                    delivery_status,
                    division,
                    region,
                    circle,
                    district,
                    state,
                    country,
                    source,
                    source_updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pincode,
                office_name,
                office_type,
                delivery,
                division,
                region,
                circle,
                district,
                state,
                "India",
                SOURCE,
                now
            ))

            imported += 1

    conn.commit()

    conn.close()

    print()
    print("======================================")
    print("ALFA X PIN CODE IMPORT COMPLETE")
    print("======================================")
    print(
        f"Imported: {imported}"
    )
    print(
        f"Skipped: {skipped}"
    )
    print(
        f"Database: {DATABASE_FILE}"
    )
    print("======================================")


if __name__ == "__main__":

    import_csv()
