import os
from datetime import timezone, timedelta, datetime
from pathlib import Path
import contextily as ctx
import requests

from models import (
    engine,
    Session,
    WeatherStation,
    Weather,
    SailingTrackPoints,
    OWM_data,
    SailingTrackLine,
)
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


def save_track(track_df, name, post_gis=False, model=SailingTrackPoints):
    if post_gis:
        with Session() as session:
            record_exists = (
                session.query(model)
                .filter_by(track_id=str(track_df.track_id[0]))
                .first()
            )
            if record_exists:
                logging.warning(f"record already exists {record_exists.track_id}")
            else:
                logging.warning(
                    f"Sailing track is being saved with parameter 'if_exists=replace'"
                )
                track_df.to_postgis(
                    model.__tablename__,
                    engine,
                    if_exists="append",
                    index=False,
                    dtype={"geometry": Geometry(geometry_type="POINT", srid=4326)},
                )
                logging.warning(f"Sailing track saved: {track_df.track_id[0]}")
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
    track_df = track_df.drop("gpxtpx_TrackPointExtension", axis=1)
    save_track(
        track_df,
        name=f"{track_df.time[0].date().isoformat()}_{track_df.track_id[0]}_track_points",
        post_gis=True,
        model=SailingTrackPoints
    )
    trajectory = trajectory.to_line_gdf()
    trajectory = trajectory.drop("gpxtpx_TrackPointExtension", axis=1)
    trajectory.crs = track_df.crs
    save_track(
        track_df=trajectory,
        name=f"{trajectory.t[0].date().isoformat()}_{trajectory.track_id[0]}_trajectory",
        post_gis=True,
        model=SailingTrackLine
    )
    return track_df, trajectory


def get_unique_hours(track_df):
    return track_df.time.dt.strftime("%Y-%m-%d %H:00:00").unique()


# test from OpenWeatherMap
# len(track_df) // 20  # amount of data to be requested
# OWM_DATA = {"DateTime": [], "lon": [], "lat": [], "wind_speed": [], "wind_deg": []}


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


def process_OWM_data(track_df, step=1):
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
    owm_data.to_sql(OWM_data.__tablename__, engine, if_exists="append")
    logging.warning(f"OWM data saved")


def create_map(track, map_title="Regata", start=None, stop=None, weather=None):
    t = mpl.markers.MarkerStyle(marker="^")
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
    if weather_data is not None:
        for i, row in weather.iterrows():
            # i, row = list(weather_data.iterrows())[0]
            markersize = 25
            t._transform = t.get_transform().rotate_deg(row.wind_deg)
            # ax.scatter(row.lon, row.lat, marker=t, s=100)
            plt.plot(
                row.lon + 0.0005,
                row.lat + 0.0005,
                marker=(3, 0, row.wind_deg),
                c="k",
                markersize=15,
                linestyle="None",
                alpha=0.3,
            )
            plt.plot(
                row.lon + 0.0005,
                row.lat + 0.0005,
                marker=(2, 0, row.wind_deg),
                c="k",
                markersize=30,
                linestyle="None",
                alpha=0.3,
            )
            plt.plot(
                row.lon + 0.0005,
                row.lat + 0.0005,
                marker=(2, 0, row.wind_deg + 45),
                c="red",
                markersize=50,
                linestyle="None",
                alpha=0.3,
            )
            plt.plot(
                row.lon + 0.0005,
                row.lat + 0.0005,
                marker=(2, 0, row.wind_deg - 45),
                c="red",
                markersize=50,
                linestyle="None",
                alpha=0.3,
            )

    ctx.add_basemap(ax, crs=track.crs, source=ctx.providers.OpenStreetMap.get("Mapnik"))
    plt.title(map_title, fontdict={"size": 18})
    plt.savefig(
        fname=f"{track.time.iloc[0].date().isoformat()}_{map_title}.png",
        dpi="figure",
        format="png",
    )

    # plt.scatter((a1), (a2), marker=t, s=100)

    # ax.scatter(weather_data.lon, weather_data.lat, marker=(3, 0, weather_data.wind_deg), s=100, markersize=30)
    # weather_data.plot(marker=(3, 0, 'wind_deg'), s=100, markersize=30)
    # for marker, scale in weather_data.rotation:
    # plt.show()


def create_traj_map(traj, map_title="Traj", start=None, stop=None, attribute="speed"):
    traj = traj.copy()
    t = mpl.markers.MarkerStyle(marker="^")
    t2 = mpl.markers.MarkerStyle(marker="2")
    if start:
        traj.df = traj.df[start:]
    if stop:
        traj.df = traj.df[:stop]
    # getting bound and expanding to the plot
    aoi_bounds = traj.df.geometry.total_bounds
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

    # for i, row in weather_data.iterrows():
    #     markersize = 25
    #     t._transform = t.get_transform().rotate_deg(row.wind_deg)
    #     t2._transform = t2.get_transform().rotate_deg(row.wind_deg)
    #     ax.scatter(row.lon, row.lat, marker=t, s=100)
    # ax.plot(row.lon, row.lat, marker=t2, c='k', markersize=30, linestyle='None')

    ctx.add_basemap(ax, crs=traj.crs, source=ctx.providers.OpenStreetMap.get("Mapnik"))
    plt.title(map_title, fontdict={"size": 18})
    plt.savefig(
        fname=f"{attribute}_{map_title}.png",
        dpi="figure",
        format="png",
    )


# merge GPX and weather data
# gpx = pd.merge(gpx, met, on="hora", how="left")
# gpx = gpx.dropna(axis=1)
