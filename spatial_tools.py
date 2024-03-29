import logging
import os
import time
import uuid
from datetime import timezone, timedelta, datetime
from math import cos, sin, radians
from pathlib import Path

import contextily as ctx
import fiona
import geopandas as gpd
import jsonlines
import matplotlib.pyplot as plt
import movingpandas as mpd
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from geoalchemy2 import Geometry

from models import (
    engine,
    Session,
    SailingTrackPoints,
    OWM_data,
    SailingTrackLine,
)

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


def save_track(track_df, name, post_gis=False, model=SailingTrackPoints):
    if post_gis:
        with Session() as session:
            record_exists = (
                session.query(model)
                .filter_by(track_id=str(track_df.track_id[0]))
                .first()
            )
            if record_exists:
                logging.warning(
                    f"record already exists {record_exists.track_id} on {SailingTrackPoints.__tablename__}"
                )
            else:
                track_df.to_postgis(
                    model.__tablename__,
                    engine,
                    if_exists="append",
                    index=False,
                    dtype={"geometry": Geometry(geometry_type="POINT", srid=4326)},
                )
                logging.warning(f"{model.__tablename__} saved: {track_df.track_id[0]}")
    else:
        if name in fiona.listlayers("SailingAnalysis.gpkg"):
            logging.warning(f"{name} already exists")
        else:
            track_df.to_file(
                "SailingAnalysis.gpkg",
                layer=name,
                driver="GPKG",
            )
            logging.warning(f"Sailing track {name} saved on SailingAnalysis.gpkg")


def export_gpx(
    gpx_path="/mnt/Trabalho/DonCarlos_Tracks/Track_23-ABR-23 132017.gpx",
    layer="track_points",
    to_postgis=True,
):
    gpx_path = Path(gpx_path)
    gpx_original = fiona.open(gpx_path, layer=layer)
    # convert to geodataframe
    track_df = gpd.GeoDataFrame.from_features(
        [feature for feature in gpx_original], crs=gpx_original.crs
    )

    # convert the date time column to local timezone
    track_df.time = pd.to_datetime(track_df.time, utc=True).dt.tz_convert(tz=BAIRES_TZ)

    # create track_id
    track_df["track_id"] = create_id(track_df)
    track_df["track_id"] = str(track_df["track_id"][0])
    track_df = track_df.drop(
        "gpxtpx_TrackPointExtension", axis=1  # todo confirm necessity before drop
    )  # confirmar necessidade
    save_track(
        track_df,
        name=f"{track_df.time[0].date().isoformat()}_{track_df.track_id[0]}_track_points",
        post_gis=to_postgis,
        model=SailingTrackPoints,
    )

    # conversion to a movingpandas' track
    # test if track_seg_point_id column exist
    logging.warning(f"Creating trjectory from track points")
    trajectory = mpd.Trajectory(df=track_df, traj_id="track_seg_point_id", t="time")
    # calculate few track attributes
    trajectory.add_acceleration(overwrite=True)
    trajectory.add_angular_difference(overwrite=True)
    trajectory.add_direction(overwrite=True)
    trajectory.add_distance(overwrite=True)  # in meters
    trajectory.add_speed(overwrite=True)  # in meters per second
    trajectory.add_timedelta(overwrite=True)
    trajectory.df.timedelta = trajectory.df.timedelta.dt.total_seconds()
    trajectory.df.direction = round(trajectory.df.direction, 1)

    # persist on database
    trajectory = trajectory.to_line_gdf()
    # trajectory = trajectory.drop("gpxtpx_TrackPointExtension", axis=1)
    trajectory.crs = track_df.crs
    save_track(
        track_df=trajectory,
        name=f"{trajectory.t[0].date().isoformat()}_{trajectory.track_id[0]}_trajectory",
        post_gis=to_postgis,
        model=SailingTrackLine,
    )
    return track_df, trajectory


def get_unique_hours(track_df):
    return track_df.time.dt.strftime("%Y-%m-%d %H:00:00").unique()


def get_OWM_data(track_df, step=10):
    jsonl_path = Path(f"./data/{track_df.track_id[0]}_OWM_weather.jsonl")
    if jsonl_path.exists():
        logging.warning(f"{jsonl_path} already exists")
    else:
        logging.warning(f"Getting weather data from Open Weather Map")
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
        with jsonlines.open(
            f"./data/{track_df.track_id.iloc[0]}_OWM_weather.jsonl", "w"
        ) as writer:
            writer.write_all(weather_lines)
    return jsonl_path


def process_OWM_data(
    track_df, step=1
):  # todo rename lat and lon columns to latitude and longitude. # todo remove rename from save_owm  # todo change plot owm using longitud no lon anymore
    weather_lines = get_OWM_data(track_df, step=step)
    weather_data = pd.read_json(weather_lines, lines=True)
    weather_data = pd.concat(
        [
            weather_data.drop(["current"], axis=1),
            weather_data["current"].apply(pd.Series),
        ],
        axis=1,
    )
    weather_data["time"] = weather_data.dt.apply(datetime.fromtimestamp, tz=BAIRES_TZ)
    weather_data.drop(
        [
            "timezone",
            "timezone_offset",
            "hourly",
            "dt",
            "sunrise",
            "sunset",
            "feels_like",
            "dew_point",
            "uvi",
            "clouds",
            "visibility",
            "weather",
        ],
        axis=1,
        inplace=True,
    )
    return weather_data


def save_OWM_data(owm_data):
    col_names = [c for c in owm_data.columns]
    if "lat" in col_names or "lon" in col_names:
        owm_data.rename(columns={"lon": "longitude", "lat": "latitude"}, inplace=True)

    owm_data.rename({"lon": "longitude", "lat": "latitude"})
    owm_data.to_sql(OWM_data.__tablename__, engine, if_exists="append", index=False)
    logging.warning(f"OWM data saved")


def create_map(track, map_title="Regata", start=None, stop=None, weather=None):
    map_path = Path("./maps")
    if not map_path.exists():
        map_path.mkdir()
    if start:
        track = track[(track.time > start)]
        if weather is not None:
            weather = weather[(weather.time > start)]
    if stop:
        track = track[(track.time < stop)]
        if weather is not None:
            weather_data = weather[(weather.time < stop)]

    # getting bound and expanding to the plot
    aoi_bounds = track.geometry.total_bounds
    xlim = [aoi_bounds[0] - 0.0025, aoi_bounds[2] + 0.0025]
    ylim = [aoi_bounds[1] - 0.0025, aoi_bounds[3] + 0.0025]

    f, ax = plt.subplots(figsize=(15, 20))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    track.plot(ax=ax)
    if weather is not None:
        weather = weather.copy()
        weather.set_index("time", inplace=True)
        weather.index = weather.index.tz_localize(None)
        if start:
            weather = weather[start:]
        if stop:
            weather = weather[:stop]
        ax.barbs(
            weather["lon"] + 0.0005,
            weather["lat"] + 0.0005,
            weather["wind_speed"]
            * (270 - weather["wind_deg"]).astype(float).apply(radians).apply(cos),
            weather["wind_speed"]
            * (270 - weather["wind_deg"]).astype(float).apply(radians).apply(sin),
        )
    ctx.add_basemap(ax, crs=track.crs, source=ctx.providers.OpenStreetMap.get("Mapnik"))
    plt.title(map_title, fontdict={"size": 18})
    plt.savefig(
        fname=f"{map_path}/{track.time.iloc[0].date().isoformat()}_{map_title}.png",
        dpi="figure",
        format="png",
    )

    # plt.scatter((a1), (a2), marker=t, s=100)

    # ax.scatter(weather_data.lon, weather_data.lat, marker=(3, 0, weather_data.wind_deg), s=100, markersize=30)
    # weather_data.plot(marker=(3, 0, 'wind_deg'), s=100, markersize=30)
    # for marker, scale in weather_data.rotation:
    # plt.show()


def create_traj_map(
    traj,
    map_title="Traj",
    start=None,
    stop=None,
    attribute="speed",
    weather=None,
    contra=None,
    save=None,
):
    map_path = Path("./maps")
    if not map_path.exists():
        map_path.mkdir()
    traj = traj.copy()
    traj.set_index("t", inplace=True)
    if start:
        traj = traj[start:]
    if stop:
        traj = traj[:stop]
    aoi_bounds = traj.geometry.total_bounds
    xlim = [aoi_bounds[0] - 0.0025, aoi_bounds[2] + 0.0025]
    ylim = [aoi_bounds[1] - 0.0025, aoi_bounds[3] + 0.0025]

    f, ax = plt.subplots(figsize=(15, 20))
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    traj.plot(
        attribute,
        linewidth=3,
        legend=True,
        legend_kwds={"shrink": 0.3},
        ax=ax,
        cmap="Reds",
    )
    if weather is not None:
        weather = weather.copy()
        weather.set_index("time", inplace=True)
        weather.index = weather.index.tz_localize(None)
        if start:
            weather = weather[start:]
        if stop:
            weather = weather[:stop]
        ax.barbs(
            weather["lon"],
            weather["lat"],
            weather["wind_speed"]
            * (270 - weather["wind_deg"]).astype(float).apply(radians).apply(cos),
            weather["wind_speed"]
            * (270 - weather["wind_deg"]).astype(float).apply(radians).apply(sin),
        )
    ctx.add_basemap(ax, crs=traj.crs, source=ctx.providers.OpenStreetMap.get("Mapnik"))
    plt.title(map_title, fontdict={"size": 18})
    if contra is not None:
        traj["tack.x"] = traj.apply(
            lambda x: [y for y in x.geometry.coords][0][0], axis=1
        )
        traj["tack.y"] = traj.apply(
            lambda x: [y for y in x.geometry.coords][0][1], axis=1
        )
        col = np.where(
            traj.angular_difference < 30,
            "r",
            np.where(traj.angular_difference > 100, "b", "r"),
        )
        ax.scatter(traj["tack.x"], traj["tack.y"], color=col)

    if save is not None:
        plt.savefig(
            fname=f"{map_path}/{attribute}_{map_title}.png",
            dpi="figure",
            format="png",
        )
