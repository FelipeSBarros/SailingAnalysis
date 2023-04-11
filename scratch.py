import os
from datetime import timezone, timedelta
from pathlib import Path

import contextily as ctx
import fiona
import geopandas as gpd
import matplotlib.pyplot as plt
import movingpandas as mpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv
from plotly.subplots import make_subplots

load_dotenv()

OWM_KEY = os.getenv("OPENWEATHER_KEY")
GPX_FILE = Path("./data/SailingTrack.gpx")
TRACK_LAYER = "track_points"
WEATHER_FORECAST = "./data/weather.csv"

# list layers on a GPX
fiona.listlayers(GPX_FILE)
# from listed, get the track layer
gpx_original = fiona.open(GPX_FILE, layer=TRACK_LAYER)
# convert to geodataframe
gpx_original = gpd.GeoDataFrame.from_features(
    [feature for feature in gpx_original], crs=gpx_original.crs
)
# Copy to a version to be changed
gpx = gpx_original

# getting bound and expanding to the plot
aoi_bounds = gpx.geometry.total_bounds
xlim = [aoi_bounds[0] - 0.05, aoi_bounds[2] + 0.05]
ylim = [aoi_bounds[1] - 0.05, aoi_bounds[3] + 0.05]

# defining local timezone
BAIRES_TZ = timezone(timedelta(hours=-3))
# convert the date time column to local timezone
gpx.time = pd.to_datetime(gpx.time, utc=True).dt.tz_convert(tz=BAIRES_TZ)


# getting meteorological forecast
# identifying unique hours
hours = gpx.time.dt.strftime("%Y-%m-%d %H:00:00").unique()
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

# conversion to a movingpandas' track
traj = mpd.Trajectory(gpx, traj_id="track_seg_point_id", t="time")
# calculate few track attributes
traj.add_direction(overwrite=True)
traj.add_distance(overwrite=True)  #  in meters
traj.add_speed(overwrite=True)  # in meters per second
traj.add_timedelta(overwrite=True)
traj.df.direction = round(traj.df.direction, 1)

# algunos resultados
print("Dirección desde el princípio hasta el final: ", traj.get_direction())
print("Duracción: ", traj.get_duration())
print("Tota percorrido: ", round(traj.get_length() / 1000, 2), "km")

# map
f, ax = plt.subplots(figsize=(15, 20))
ax.set_xlim(xlim)
ax.set_ylim(ylim)
gpx.plot(ax=ax)
plt.title("Regata travesia Posadas - Ombu", fontdict={"size": 18})
ctx.add_basemap(ax, crs=gpx.crs)
plt.show()

# estimating about wind and boat direction
wind_dir = traj.df.groupby(by=["wdir"]).size().sort_values(ascending=False)
boat_dir = traj.df.groupby(by=["direction"]).size().sort_values(ascending=False)
boat_dir = pd.DataFrame(boat_dir)
boat_dir.reset_index(inplace=True)
boat_dir = boat_dir.rename({0: "frequency"}, axis="columns")

wind_dir = pd.DataFrame(wind_dir)
wind_dir.reset_index(inplace=True)
wind_dir.rename({0: "frequency"}, axis="columns", inplace=True)

# plots about weather
fig = make_subplots(rows=1, cols=2, specs=[[{"type": "polar"}] * 2])
fig.update_layout(template="plotly_dark")

fig.add_trace(
    go.Scatterpolar(
        name="Wind Direction",
        r=traj.df.index,
        theta=traj.df.wdir,
        mode="markers",
        marker_color=traj.df.wspd,
    ),
    1,
    1,
)
fig.add_trace(
    go.Scatterpolar(
        name="Boat Direction",
        r=traj.df.index,
        theta=traj.df.direction,
        mode="markers",
        marker_color=traj.df.speed,
    ),
    1,
    2,
)

fig.update_layout(
    polar=dict(
        angularaxis=dict(
            direction="clockwise",
        )
    ),
    polar2=dict(
        angularaxis=dict(
            direction="clockwise",
        )
    ),
)

fig.show()


# more plots
# fig = px.line_polar(wind_dir, r="frequency", theta="wdir", #color="strength",
#                    line_close=False,
#                    color_discrete_sequence=px.colors.sequential.Plasma_r,
#                    template="plotly_dark",)
# fig = px.scatter_polar(wind_dir, r="frequency", theta="wdir", #color="strength",
#                    color_discrete_sequence=px.colors.sequential.Plasma_r,
#                    template="plotly_dark",)
fig = px.scatter_polar(
    traj.df,
    r=traj.df.index,
    theta=traj.df.wdir,  # color="strength",
    color=traj.df.wspd,
    template="plotly_dark",
)
fig.show()

# Ahora que tenemos algunos valores calculados, necesito confirmar algunas suposiciones:
#
# El GPS crea el track o por tiempo o por distancia; Necesitamos saber como lo está armado para poder analizar los datos; El grafico que sigo deja claro que la diferencia de tiempo a cada punto crado del track tiene el valor exacto y constante de 5 segundos (eje Y).
# [ ]
traj.df["timedelta"].plot()
traj.df["distance"].plot()
# fig = px.line(traj.df, x=traj.df.index, y='distance', title='Distancia percorrida a cada 5 segundos')
# fig.show()


# Maps
# speed
f, ax = plt.subplots(figsize=(15, 20))
ax.set_xlim(xlim)
ax.set_ylim(ylim)
traj.plot(
    "speed", linewidth=3, legend=True, legend_kwds={"shrink": 0.3}, ax=ax, cmap="Reds"
)
plt.title("Velocidad en m/s")
ctx.add_basemap(ax, crs=traj.crs)

# distance
f, ax = plt.subplots(figsize=(15, 20))
ax.set_xlim(xlim)
ax.set_ylim(ylim)
traj.plot("distance", legend=True, legend_kwds={"shrink": 0.3}, ax=ax, cmap="Reds")
ctx.add_basemap(ax, crs=traj.crs)

# directions
f, ax = plt.subplots(figsize=(15, 20))
ax.set_xlim(xlim)
ax.set_ylim(ylim)
traj.plot("direction", legend=True, legend_kwds={"shrink": 0.3}, ax=ax, cmap="Reds")
ctx.add_basemap(ax, crs=traj.crs)

# No idea
# traj.hvplot(line_width=7.0, geo=False)

# Extract the time component
# traj.df["time"] = pd.to_datetime(traj.df.index).dt.strftime("%H:%M")
traj.df.head()
# Plot the trajectory in space-time cube
fig = px.line_3d(traj.df, x=traj.df.geometry.x, y=traj.df.geometry.y, z=traj.df.speed)
fig.update_traces(line=dict(width=5))
# Want to get background map as well? It is possible:
# https://chart-studio.plotly.com/~empet/14397/plotly-plot-of-a-map-from-data-available/#/
fig.show()


# test from OpenWeatherMap
STEP = len(gpx) // 20
weather = {"DateTime": [], "lon": [], "lat": [], "wind_speed": [], "wind_deg": []}

for ind in range(gpx.index.start, gpx.index.stop, STEP):
    # ind = gpx.index[0]
    lat = gpx.geometry.y[ind]
    lon = gpx.geometry.x[ind]
    time = int(gpx.time[ind].timestamp())
    # url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&mode=metric&exclude=[current, minutely, daily, alerts]&lang=es&appid={OWM_KEY}"
    url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&units=metric&dt={time}&lang=es&appid={OWM_KEY}"
    # url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat=39.099724&lon=-94.578331&units=metric&dt=1643803200&appid={OWM_KEY}"
    resp = requests.get(url=url)
    data = resp.json()
    # data.keys()
    # data.get("current").get("wind_speed")
    # data.get("current").get("wind_deg")
    weather.get("DateTime").append(gpx.time[ind])
    weather.get("lat").append(gpx.geometry[ind].y)
    weather.get("lon").append(gpx.geometry[ind].x)
    weather.get("wind_speed").append(data.get("current").get("wind_speed"))
    weather.get("wind_deg").append(data.get("current").get("wind_deg"))

weather_ = pd.DataFrame(weather)
weather_.iloc[0]
weather_.to_csv("./data/OpenWeatherMap.csv")
