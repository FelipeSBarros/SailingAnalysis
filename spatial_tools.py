import os
from datetime import timezone, timedelta, datetime
from pathlib import Path
import contextily as ctx
import requests

from models import engine, Session, WeatherStation, Weather, SailingTrack
import fiona
import geopandas as gpd
import movingpandas as mpd
import pandas as pd
from dotenv import load_dotenv
import uuid
import logging
from geoalchemy2 import WKTElement, Geometry
import jsonlines
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
load_dotenv()

OWM_KEY = os.getenv("OPENWEATHER_KEY")
GPX_FILE = Path("./data/SailingTrack.gpx")
GPX_FILE = Path("/mnt/Trabalho/DonCarlos_Tracks/Track_21-JUL-22 171218.gpx")
TRACK_LAYER = "track_points"
WEATHER_FORECAST = "./data/weather.csv"
# defining local timezone
BAIRES_TZ = timezone(timedelta(hours=-3))

def create_id(track_df):
    return uuid.uuid5(uuid.NAMESPACE_DNS, track_df.time.iloc[0].isoformat())

def save_track(track_df, post_gis=False):
    if post_gis:
        with Session() as session:
            record_exists = (
                session.query(SailingTrack).filter_by(track_id=str(track_df.track_id[0])).first()
            )
            if record_exists:
                logging.warning(f"record already exists {record_exists.id}")
            else:
                logging.warning(f"Sailing track is being saved with parameter 'if_exists=replace'")
                track_df.to_postgis(SailingTrack.__tablename__, engine, if_exists="replace", index=False, dtype={'geometry': Geometry(geometry_type='POINT', srid= 4326)})
                logging.warning(f"Sailing track saved: {track_df.track_id[0]}")
    else:
        track_df['track_id'] = str(track_df['track_id'][0])
        track_df.to_file("SailingAnalysis.gpkg", layer=f'{track_df.time[0].date().isoformat()}_{track_df.track_id[0]}', driver="GPKG")
        logging.warning(f"Sailing track {track_df.track_id[0]} saved on SailingAnalysis.gpkg")

def export_gpx(gpx_path="/mnt/Trabalho/DonCarlos_Tracks/Track_23-ABR-23 132017.gpx", layer="track_points"):
    gpx_path = Path(gpx_path)
    gpx_original = fiona.open(gpx_path, layer=layer)
    # convert to geodataframe
    track_df = gpd.GeoDataFrame.from_features(
        [feature for feature in gpx_original], crs=gpx_original.crs
    )

    # convert the date time column to local timezone
    track_df.time = pd.to_datetime(track_df.time, utc=True).dt.tz_convert(tz=BAIRES_TZ)

    # create track_id
    track_df['track_id'] = create_id(track_df)

    # persist on database
    save_track(track_df)


def get_unique_hours(track_df):
    return track_df.time.dt.strftime("%Y-%m-%d %H:00:00").unique()

# test from OpenWeatherMap
STEP = len(track_df) // 20  # amount of data to be requested
# OWM_DATA = {"DateTime": [], "lon": [], "lat": [], "wind_speed": [], "wind_deg": []}

def get_OWM_data(track_df, step=STEP):
    jsonl_path = Path(f'./data/{track_df.track_id[0]}_OWM_weather.jsonl')
    if jsonl_path.exists():
        logging.warning(f'{jsonl_path} already exists')
    else:
        logging.warning(f'Getting weather data from Open Weather Map')
        weather_lines = []
        for ind in range(track_df.index.start, track_df.index.stop, step):
            # ind = track_df.index[0]
            lat = track_df.geometry.y[ind]
            lon = track_df.geometry.x[ind]
            timestamp = int(track_df.time[ind].timestamp())
            url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&units=metric&dt={timestamp}&lang=es&appid={OWM_KEY}"
            resp = requests.get(url=url)
            data = resp.json()
            weather_lines.append(data)
            time.sleep(5)
        with jsonlines.open(f'./data/{track_df.track_id.iloc[0]}_OWM_weather.jsonl', 'w') as writer:
            writer.write_all(weather_lines)
    return jsonl_path


weather_lines = get_OWM_data(track_df=track_df, step=STEP)
weather_data = pd.read_json(weather_lines, lines=True)
weather_data = pd.concat([weather_data.drop(['current'], axis=1), weather_data['current'].apply(pd.Series)], axis=1)
weather_data.drop(['timezone', 'timezone_offset', 'hourly', 'dt', 'sunrise', 'sunset', 'feels_like', 'dew_point', 'uvi', 'visibility', 'weather'], axis=1, inplace=True)




# weather_data.columns


# weather_data["temp"] = weather_data.current
# weather.get("DateTime").append(gpx.time[ind])
# weather.get("lat").append(gpx.geometry[ind].y)
# weather.get("lon").append(gpx.geometry[ind].x)
# weather.get("wind_speed").append(data.get("current").get("wind_speed"))
# weather.get("wind_deg").append(data.get("current").get("wind_deg"))
# weather_ = pd.DataFrame(weather)
# weather_.iloc[0]
# weather_.to_csv("./data/OpenWeatherMap.csv")



# reading weather conditions
met = pd.read_csv(
    WEATHER_FORECAST
)  # source https://meteostat.net/en/station/87178?t=2023-04-04/2023-04-10
# filtering columns
met = met[["time", "temp", "wdir", "wspd", "pres"]]
# filtering row considering hour of the sailing track
met = met[met.time.isin(hours)]
# met.time = pd.to_datetime(met.time, utc=True).dt.tz_convert(tz=BAIRES_TZ)
met["hora"] = pd.to_datetime(met.time, utc=False)
met = met.drop("time", axis=1)

# todo descobrir o que estou fazendo
gpx = gpx.assign(hora=gpx.time.dt.strftime("%Y-%m-%d %H:00:00"))
gpx.hora = pd.to_datetime(gpx.hora, utc=False)

# merge GPX and weather data
gpx = pd.merge(gpx, met, on="hora", how="left")
gpx = gpx.dropna(axis=1)


# import numpy as np

# import matplotlib.pyplot as plt
# def gen_arrow_head_marker(rot):
#     """generate a marker to plot with matplotlib scatter, plot, ...
#
#     https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
#
#     rot=0: positive x direction
#     Parameters
#     ----------
#     rot : float
#         rotation in degree
#         0 is positive x direction
#
#     Returns
#     -------
#     arrow_head_marker : Path
#         use this path for marker argument of plt.scatter
#     scale : float
#         multiply a argument of plt.scatter with this factor got get markers
#         with the same size independent of their rotation.
#         Paths are autoscaled to a box of size -1 <= x, y <= 1 by plt.scatter
#     """
#     arr = np.array([[.1, .3], [.1, -.3], [1, 0], [.1, .3]])  # arrow shape
#     angle = rot.wind_deg / 180 * np.pi
#     rot_mat = np.array([
#         [np.cos(angle), np.sin(angle)],
#         [-np.sin(angle), np.cos(angle)]
#         ])
#     arr = np.matmul(arr, rot_mat)  # rotates the arrow
#
#     # scale
#     x0 = np.amin(arr[:, 0])
#     x1 = np.amax(arr[:, 0])
#     y0 = np.amin(arr[:, 1])
#     y1 = np.amax(arr[:, 1])
#     scale = np.amax(np.abs([x0, x1, y0, y1]))
#     codes = [mpl.path.Path.MOVETO, mpl.path.Path.LINETO,mpl.path.Path.LINETO, mpl.path.Path.CLOSEPOLY]
#     arrow_head_marker = mpl.path.Path(arr, codes)
#     return arrow_head_marker, scale
#
# gen_arrow_head_marker(0.3)
# weather_data['rotation'] = weather_data.apply(gen_arrow_head_marker, axis=1)

t = mpl.markers.MarkerStyle(marker='^')

def create_map(track = track_df, map_title="Regata", start=None, stop=None):
    if start:
        track = track[(track.time > start)]
    if stop:
        track = track[(track.time < stop)]
    # getting bound and expanding to the plot
    aoi_bounds = track.geometry.total_bounds
    xlim = [aoi_bounds[0] - 0.0025, aoi_bounds[2] + 0.0025]
    ylim = [aoi_bounds[1] - 0.0025, aoi_bounds[3] + 0.0025]

    f, ax = plt.subplots(figsize=(15, 20))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    track.plot(ax=ax)
    # for i, row in weather_data.iterrows():
    #     markersize = 25
    #     t._transform = t.get_transform().rotate_deg(row.wind_deg)
    #     ax.scatter(row.lon, -27.345, marker=t, s=100)
    ctx.add_basemap(ax, crs=track.crs, source=ctx.providers.OpenStreetMap.get('Mapnik'))
    plt.title(map_title, fontdict={"size": 18})
    plt.savefig(
        fname=f"{track.time.iloc[0].date().isoformat()}_{map_title}.png",
        dpi='figure',
        format='png')

        # plt.scatter((a1), (a2), marker=t, s=100)

    # ax.scatter(weather_data.lon, weather_data.lat, marker=(3, 0, weather_data.wind_deg), s=100, markersize=30)
    # weather_data.plot(marker=(3, 0, 'wind_deg'), s=100, markersize=30)
    # for marker, scale in weather_data.rotation:
    # plt.show()

create_map(track=track_df,
           map_title='FULL')

start_time=datetime(2023, 4, 23, 9, tzinfo=BAIRES_TZ)
stop_time=datetime(2023, 4, 23, 11, tzinfo=BAIRES_TZ)
create_map(track=track_df,
           map_title='inicio',
           start=start_time,
           stop=stop_time,
           )
# conversion to a movingpandas' track
traj = mpd.Trajectory(gpx, traj_id="track_seg_point_id", t="time")
# calculate few track attributes
traj.add_direction(overwrite=True)
traj.add_distance(overwrite=True)  #  in meters
traj.add_speed(overwrite=True)  # in meters per second
traj.add_timedelta(overwrite=True)
traj.df.direction = round(traj.df.direction, 1)

