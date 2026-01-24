"""
Postcode to Hospital Distance Calculator

A Flask web application that calculates travel distances from postcodes
to NHS hospitals using the Google Maps Distance Matrix API.
"""

import io
import json
import os
import time
from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# Path to destinations file
DESTINATIONS_FILE = os.path.join(os.path.dirname(__file__), "destinations.json")


def load_destinations():
    """Load destinations from JSON file."""
    if os.path.exists(DESTINATIONS_FILE):
        with open(DESTINATIONS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_destinations(destinations):
    """Save destinations to JSON file."""
    with open(DESTINATIONS_FILE, "w") as f:
        json.dump(destinations, f, indent=4)

# Google Maps Distance Matrix API endpoint
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

# Batch size for API requests (Google allows up to 25 origins per request)
BATCH_SIZE = 25


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/destinations")
def get_destinations():
    """Return list of available hospital destinations."""
    return jsonify(load_destinations())


@app.route("/api/destinations", methods=["POST"])
def add_destination():
    """Add a new destination."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["id", "name", "address", "short_name"]
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({"error": f"Missing required field: {field}"}), 400

    destinations = load_destinations()
    dest_id = data["id"].lower().replace(" ", "_")

    if dest_id in destinations:
        return jsonify({"error": "A destination with this ID already exists"}), 400

    destinations[dest_id] = {
        "name": data["name"].strip(),
        "address": data["address"].strip(),
        "short_name": data["short_name"].strip()
    }

    save_destinations(destinations)
    return jsonify({"success": True, "id": dest_id})


@app.route("/api/destinations/<dest_id>", methods=["PUT"])
def update_destination(dest_id):
    """Update an existing destination."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    destinations = load_destinations()

    if dest_id not in destinations:
        return jsonify({"error": "Destination not found"}), 404

    if "name" in data:
        destinations[dest_id]["name"] = data["name"].strip()
    if "address" in data:
        destinations[dest_id]["address"] = data["address"].strip()
    if "short_name" in data:
        destinations[dest_id]["short_name"] = data["short_name"].strip()

    save_destinations(destinations)
    return jsonify({"success": True})


@app.route("/api/destinations/<dest_id>", methods=["DELETE"])
def delete_destination(dest_id):
    """Delete a destination."""
    destinations = load_destinations()

    if dest_id not in destinations:
        return jsonify({"error": "Destination not found"}), 404

    del destinations[dest_id]
    save_destinations(destinations)
    return jsonify({"success": True})


@app.route("/api/process", methods=["POST"])
def process_csv():
    """
    Process uploaded CSV file and calculate distances to selected hospitals.

    Expects:
    - CSV file with a 'postcode' column
    - Google Maps API key in X-API-Key header
    - Selected destination IDs in form data
    """
    # Validate API key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({"error": "Google Maps API key is required"}), 400

    # Validate file upload
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Check file extension
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        return jsonify({"error": "File must be CSV or Excel (.csv, .xlsx, .xls)"}), 400

    # Get selected destinations
    selected_destinations = request.form.getlist("destinations")
    if not selected_destinations:
        return jsonify({"error": "At least one destination must be selected"}), 400

    # Load destinations and validate IDs
    destinations = load_destinations()
    for dest_id in selected_destinations:
        if dest_id not in destinations:
            return jsonify({"error": f"Invalid destination: {dest_id}"}), 400

    try:
        # Read file based on extension
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            # Excel file (.xlsx or .xls)
            df = pd.read_excel(file)

        # Find postcode column (case-insensitive, matches columns containing 'postcode')
        postcode_col = None
        for col in df.columns:
            if "postcode" in col.lower():
                postcode_col = col
                break

        if postcode_col is None:
            return jsonify({"error": "File must contain a column with 'postcode' in the name"}), 400

        # Clean postcodes
        postcodes = df[postcode_col].astype(str).str.strip().str.upper().tolist()

        # Calculate distances for each selected destination
        for dest_id in selected_destinations:
            dest = destinations[dest_id]
            short_name = dest["short_name"]

            distances, durations, errors = calculate_distances(
                postcodes, dest["address"], api_key
            )

            # Add columns to dataframe
            df[f"Distance to {short_name} (km)"] = distances
            df[f"Travel Time to {short_name} (mins)"] = durations

            # Check for errors
            if any(errors):
                error_count = sum(1 for e in errors if e)
                if error_count == len(errors):
                    return jsonify({
                        "error": f"All distance calculations failed for {dest['name']}. "
                                 "Please check your API key and ensure the Distance Matrix API is enabled."
                    }), 400

        # Convert dataframe to CSV string
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return jsonify({
            "success": True,
            "csv": output.getvalue(),
            "rows_processed": len(df)
        })

    except pd.errors.EmptyDataError:
        return jsonify({"error": "The uploaded CSV file is empty"}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500


def calculate_distances(postcodes, destination, api_key):
    """
    Calculate distances from postcodes to a destination using Google Maps API.

    Args:
        postcodes: List of UK postcodes
        destination: Destination address string
        api_key: Google Maps API key

    Returns:
        Tuple of (distances_km, durations_mins, errors)
    """
    distances = []
    durations = []
    errors = []

    # Process in batches to respect API limits
    for i in range(0, len(postcodes), BATCH_SIZE):
        batch = postcodes[i:i + BATCH_SIZE]

        # Format postcodes as origins (append UK for better geocoding)
        origins = [f"{pc}, UK" for pc in batch]

        try:
            response = requests.get(
                GOOGLE_MAPS_API_URL,
                params={
                    "origins": "|".join(origins),
                    "destinations": destination,
                    "mode": "driving",
                    "units": "metric",
                    "key": api_key
                },
                timeout=30
            )

            data = response.json()

            # Log the response for debugging
            print(f"API Response status: {data.get('status')}")
            if data.get("error_message"):
                print(f"API Error: {data.get('error_message')}")

            if data.get("status") != "OK":
                error_msg = data.get("error_message", data.get("status", "Unknown error"))
                print(f"Full API response: {data}")
                for _ in batch:
                    distances.append(None)
                    durations.append(None)
                    errors.append(error_msg)
                continue

            # Process each result
            for row in data.get("rows", []):
                elements = row.get("elements", [{}])
                element = elements[0] if elements else {}

                if element.get("status") == "OK":
                    # Distance in km (API returns meters)
                    dist_m = element.get("distance", {}).get("value", 0)
                    distances.append(round(dist_m / 1000, 1))

                    # Duration in minutes (API returns seconds)
                    dur_s = element.get("duration", {}).get("value", 0)
                    durations.append(round(dur_s / 60))

                    errors.append(None)
                else:
                    distances.append(None)
                    durations.append(None)
                    errors.append(element.get("status", "Unknown error"))

            # Small delay between batches to respect rate limits
            if i + BATCH_SIZE < len(postcodes):
                time.sleep(0.1)

        except requests.RequestException as e:
            for _ in batch:
                distances.append(None)
                durations.append(None)
                errors.append(str(e))

    return distances, durations, errors


if __name__ == "__main__":
    print("=" * 60)
    print("Postcode to Hospital Distance Calculator")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("\nIMPORTANT: This tool requires a Google Maps API key with")
    print("the Distance Matrix API enabled.")
    print("\nPress Ctrl+C to stop the server.\n")
    app.run(debug=True, host="localhost", port=5000)
