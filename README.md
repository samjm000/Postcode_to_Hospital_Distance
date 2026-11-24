# Postcode to Hospital Distance Calculator

A web-based tool that calculates travel distances from UK postcodes to NHS hospitals using the Google Maps Distance Matrix API.

> **Important — secure environment and prior approval required:** Download or clone this repository into an organisation-approved secure environment and run the application locally. Obtain explicit permission from your organisation's information governance/data controller team before processing any postcodes through the Google Maps API. Local hosting does not prevent external data transfer: postcodes and destination addresses are sent to Google.

## Features

- Upload a CSV file containing postcodes
- Calculate driving distances and travel times to selected hospitals
- Download results as a new CSV with distance columns added
- NHS-style design for professional appearance
- User-supplied Google Maps API key

## Pre-configured Hospitals

- **Glasgow Royal Infirmary** - 84 Castle St, Glasgow G4 0SF
- **Beatson West of Scotland Cancer Centre** - 1053 Great Western Rd, Glasgow G12 0YN

## Requirements

- Python 3.11+
- Google Maps API key with Distance Matrix API enabled

## Setup

### Option 1: Using Conda (Recommended)

```bash
# Create the conda environment
conda env create -f environment.yml

# Activate the environment
conda activate postcode_hospital

# Run the application
python app.py
```

### Option 2: Using pip

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## Usage

1. Open http://localhost:5000 in your browser
2. Confirm that you are in an approved secure environment and have explicit permission to process postcodes using the Google Maps API
3. Enter your Google Maps API key
4. Upload a CSV file with a `postcode` column
5. Select the destination hospitals
6. Click "Calculate Distances"
7. Download the results CSV

## Getting a Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Distance Matrix API**
4. Go to Credentials and create an API key
5. (Recommended) Restrict the API key to the Distance Matrix API only

For detailed instructions, see [Google's documentation](https://developers.google.com/maps/documentation/distance-matrix/get-api-key).

## CSV Format

Your input CSV must contain a column named `postcode` (case-insensitive). Example:

```csv
id,name,postcode
1,Patient A,G1 1AA
2,Patient B,G2 2BB
3,Patient C,G3 3CC
```

The output CSV will include additional columns:
- `Distance to GRI (km)`
- `Travel Time to GRI (mins)`
- `Distance to Beatson (km)`
- `Travel Time to Beatson (mins)`

## Data Protection

- Download or clone the application into an organisation-approved secure environment (such as an approved NHS secure environment) and run it locally. Do not deploy it to a public or unapproved server.
- Obtain explicit organisational information governance/data controller approval before processing any postcodes using the Google Maps API. Approval must cover the external transfer to Google, the intended purpose and applicable data protection requirements.
- Full postcodes, destination addresses, travel modes and the API key are transmitted to Google. Other spreadsheet columns are not intentionally sent to Google. Local hosting alone does not ensure that all data remains within the secure environment.
- Do not process patient-derived postcodes or identifiable patient information without specific approval covering that data and its external transfer. Minimise input data and keep source files and downloaded results within the approved environment.
- For demonstrations, use synthetic or publicly available non-patient-derived postcode data only, subject to organisational permission before using the API.

The API key is supplied at runtime and is not intentionally persisted by the application. This prototype has not been formally approved for clinical deployment; users must follow their local governance and security requirements.

## Security and operational limitations

- Localhost only; do not expose the Flask development server to other users or networks.
- All three governance acknowledgements are required by the interface and server. They do not replace formal approval.
- Uploads are limited to 5 MiB and 5,000 rows; invalid or missing postcode formats are rejected before external requests. Format checking does not establish that a postcode exists or is non-personal.
- Use a restricted API key and appropriate Google Cloud quotas and budget controls. A file of 5,000 rows and three hospitals can generate up to 30,000 billable origin-destination elements (driving and transit).
- Keep patient data outside the repository. Git ignore rules are a safeguard, not a substitute for checking staged files.
- Journey distances and times are estimates, not formally validated clinical or transport measures. Check the applicable Google Maps terms before retaining, reusing or publishing results.
- Confirm permission to distribute the DTC branding and clarify software ownership/licensing before wider redistribution.

## Troubleshooting

### "All distance calculations failed"
- Check your API key is valid
- Ensure the Distance Matrix API is enabled in Google Cloud Console
- Check your API key has not exceeded its quota

### Invalid postcodes
- Postcodes that cannot be geocoded will show `null` in the distance columns
- Ensure postcodes are in valid UK format (e.g., "G1 1AA", "EH1 1BB")

## License

For NHS use only. Not for redistribution.
