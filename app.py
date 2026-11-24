"""
Postcode to Hospital Distance Calculator

A Flask web application that calculates travel distances from postcodes
to NHS hospitals using the Google Maps Distance Matrix API.
"""

import io
import json
import os
import re
import time
from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
MAX_ROWS = 5000
POSTCODE_RE = re.compile(r'(?:GIR0AA|[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2})', re.ASCII)


def normalize_postcode(value):
    compact = re.sub(r'\s+', '', str(value).upper())
    if not POSTCODE_RE.fullmatch(compact):
        return None
    return compact[:-3] + ' ' + compact[-3:]


@app.errorhandler(413)
def upload_too_large(_error):
    return jsonify({'error': 'Upload exceeds the 5 MiB limit.'}), 413


@app.before_request
def restrict_local_requests():
    if request.host not in ('localhost:5000', '127.0.0.1:5000', '[::1]:5000', 'localhost', '127.0.0.1', '[::1]'):
        return jsonify({'error': 'Local access only.'}), 403
    if request.method in ('POST', 'PUT', 'DELETE'):
        origin = request.headers.get('Origin')
        if origin and origin != request.host_url.rstrip('/'):
            return jsonify({'error': 'Cross-origin requests are not permitted.'}), 403


@app.after_request
def security_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return response

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
    # Acknowledgement is a safeguard, not evidence of governance approval.
    if any(request.form.get(field) != 'yes' for field in ('secure_environment', 'permission', 'external_transfer')):
        return jsonify({'error': 'All data protection confirmations are required.'}), 400

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
        # Read file based on extension (preserve original data types and formatting)
        if filename.endswith(".csv"):
            df = pd.read_csv(file, dtype=str, keep_default_na=False, nrows=MAX_ROWS + 1)
        else:
            # Excel file (.xlsx or .xls)
            df = pd.read_excel(file, dtype=str, keep_default_na=False, nrows=MAX_ROWS + 1)

        if len(df) > MAX_ROWS:
            return jsonify({'error': f'File exceeds the {MAX_ROWS} row limit.'}), 400
        if df.empty:
            return jsonify({'error': 'File has no data rows.'}), 400

        # Find postcode column (case-insensitive, matches columns containing 'postcode')
        postcode_col = None
        for col in df.columns:
            if "postcode" in col.lower():
                postcode_col = col
                break

        if postcode_col is None:
            return jsonify({"error": "File must contain a column with 'postcode' in the name"}), 400

        # Clean postcodes for API calls (normalize to uppercase, but keep originals unchanged in dataframe)
        # This handles any capitalization: "G1 1AA", "g1 1aa", "G1 1aa" all work
        postcodes = [normalize_postcode(value) for value in df[postcode_col]]
        invalid_count = sum(value is None for value in postcodes)
        if invalid_count:
            return jsonify({'error': f'{invalid_count} invalid or missing postcode(s). Correct these before processing.'}), 400

        # Store original column order
        original_columns = df.columns.tolist()

        # Calculate distances for each selected destination
        for dest_id in selected_destinations:
            dest = destinations[dest_id]
            short_name = dest["short_name"]

            # Calculate driving times and distances
            distances, driving_durations, errors = calculate_distances(
                postcodes, dest["address"], api_key, mode="driving"
            )

            # Calculate public transport times
            _, transit_durations, transit_errors = calculate_distances(
                postcodes, dest["address"], api_key, mode="transit"
            )

            # Add columns to dataframe
            df[f"Distance to {short_name} (km)"] = distances
            df[f"Drive Time to {short_name} (mins)"] = driving_durations
            df[f"Public Transport to {short_name} (mins)"] = transit_durations

            # Check for errors
            if any(errors):
                error_count = sum(1 for e in errors if e)
                if error_count == len(errors):
                    return jsonify({
                        "error": f"All distance calculations failed for {dest['name']}. "
                                 "Please check your API key and ensure the Distance Matrix API is enabled."
                    }), 400

        # Reorder columns: original columns first, then new calculated columns
        new_columns = [col for col in df.columns if col not in original_columns]
        df = df[original_columns + new_columns]

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
        return jsonify({"error": "Unable to process file. Check file format and try again."}), 500


def calculate_distances(postcodes, destination, api_key, mode="driving"):
    """
    Calculate distances from postcodes to a destination using Google Maps API.

    Args:
        postcodes: List of UK postcodes
        destination: Destination address string
        api_key: Google Maps API key
        mode: Travel mode - 'driving' or 'transit'

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
                    "mode": mode,
                    "units": "metric",
                    "key": api_key
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                error_msg = "Google Maps request failed"
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

        except (requests.RequestException, ValueError):
            for _ in batch:
                distances.append(None)
                durations.append(None)
                errors.append("Google Maps request failed")

    return distances, durations, errors


if __name__ == "__main__":
    print("=" * 60)
    print("Postcode to Hospital Distance Calculator")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("\nIMPORTANT: This tool requires a Google Maps API key with")
    print("the Distance Matrix API enabled.")
    print("\nPress Ctrl+C to stop the server.\n")
    app.run(debug=False, host="localhost", port=5000)
