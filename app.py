from flask import Flask, jsonify
import requests
import re

app = Flask(__name__)

DEV = "@ALFA_X_1801"


@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "api": "ALFA X PIN CODE LOOKUP API",
        "message": "API is running successfully",
        "developer": DEV
    })


@app.route("/api/pincode/<pincode>")
def pincode_lookup(pincode):

    # Check 6-digit Indian PIN
    if not re.fullmatch(r"\d{6}", pincode):
        return jsonify({
            "status": "error",
            "message": "Invalid PIN code. PIN must contain exactly 6 digits.",
            "pincode": pincode,
            "dev": DEV
        }), 400

    try:
        api_url = f"https://api.postalpincode.in/pincode/{pincode}"

        response = requests.get(
            api_url,
            timeout=10
        )

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "PIN service is temporarily unavailable.",
                "dev": DEV
            }), 503

        data = response.json()

        if not data or data[0].get("Status") != "Success":
            return jsonify({
                "status": "error",
                "message": "PIN code not found.",
                "pincode": pincode,
                "dev": DEV
            }), 404

        post_offices = []

        for office in data[0].get("PostOffice", []):
            post_offices.append({
                "name": office.get("Name"),
                "branch_type": office.get("BranchType"),
                "delivery_status": office.get("DeliveryStatus"),
                "division": office.get("Division"),
                "region": office.get("Region"),
                "circle": office.get("Circle"),
                "district": office.get("District"),
                "state": office.get("State"),
                "country": office.get("Country")
            })

        return jsonify({
            "status": "success",
            "pincode": pincode,
            "post_offices": post_offices,
            "dev": DEV
        })

    except requests.RequestException:
        return jsonify({
            "status": "error",
            "message": "Unable to connect to PIN service.",
            "dev": DEV
        }), 503

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Internal server error.",
            "dev": DEV
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
