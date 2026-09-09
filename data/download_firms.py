import os
import requests

MAP_KEY = os.getenv("FIRMS_MAP_KEY")

if not MAP_KEY:
    raise RuntimeError("FIRMS_MAP_KEY is not set")

# India bounding box
west = 68
south = 6
east = 98
north = 36

days = 5

sources = {
    "VIIRS_NOAA20_NRT": "data/raw/firms/viirs_noaa20/india_7days.csv",
    "VIIRS_NOAA21_NRT": "data/raw/firms/viirs_noaa21/india_7days.csv",
}

for source, output_file in sources.items():

    url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        f"{MAP_KEY}/{source}/{west},{south},{east},{north}/{days}"
    )

    print(f"Downloading {source}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    print(f"Saved: {output_file}")

print("FIRMS download completed.")