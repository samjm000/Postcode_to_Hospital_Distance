# Postcode to Hospital Distance Calculator

A web-based tool that calculates travel distances from UK postcodes to NHS hospitals using the Google Maps Distance Matrix API.

## Features

- Upload a CSV file containing postcodes
- Calculate driving distances and travel times to selected hospitals
- Download results as a new CSV with distance columns added
- NHS-style design for professional appearance
- Secure API key handling (never stored, only held in memory during request)

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
2. Acknowledge the data protection disclaimer
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

**Important:** This tool must not be used with patient identifiable data unless:
- Downloaded and run locally on a secure NHS network
- All data remains within the secure network
- Appropriate data governance approvals are in place

The API key is:
- Never stored on disk
- Never logged
- Only held in memory for the duration of each request

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
