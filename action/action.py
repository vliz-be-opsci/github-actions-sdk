import logging
import os
import pandas as pd
import requests
from pathlib import Path

GITHUB_WORKSPACE = Path(os.getenv("GITHUB_WORKSPACE", "/github/workspace"))
API_ENDPOINT = os.getenv("API_ENDPOINT")
FILE_FORMAT = os.getenv("FILE_FORMAT").lower()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

stations = []
temperatures = []
wind_speeds = []
barometric_pressures = []
relative_humidities = []

# request data from API_ENDPOINT
for station in pd.read_csv(GITHUB_WORKSPACE / "stations.csv")["station"]:
    logger.debug(f"requesting observations for station {station}")
    observations = requests.get(f"{API_ENDPOINT}/stations/{station}/observations").json()
    for i in range(len(observations["features"])):
        stations.append(station)
        temperatures.append(observations["features"][i]["properties"]["temperature"]["value"])
        wind_speeds.append(observations["features"][i]["properties"]["windSpeed"]["value"])
        barometric_pressures.append(observations["features"][i]["properties"]["barometricPressure"]["value"])
        relative_humidities.append(observations["features"][i]["properties"]["relativeHumidity"]["value"])

# construct pandas dataframe
df = pd.DataFrame(
    {
        "station": stations,
        "temperature": temperatures,
        "wind_speed": wind_speeds,
        "barometric_pressure": barometric_pressures,
        "relative_humidity": relative_humidities
    }
)

# write dataframe to file according to FILE_FORMAT
df.__getattr__(f"to_{FILE_FORMAT}")(GITHUB_WORKSPACE / f"weather_observations.{FILE_FORMAT}")
