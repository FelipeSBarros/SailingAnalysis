from movingpandas.trajectory_utils import convert_time_ranges_to_segments

# Sailing Analysis

Package under construction to automate data analysis from sailing boats.

## Functionalities:
- Get sailing track from GPX and save it on a spatially enabled database (using [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/en/latest/):
  - [X] [PostGIS](https://postgis.net/);
  - [X] [Geopackage](https://www.geopackage.org/);
- For each sailing track, use [MovingPandas](https://movingpandas.github.io/movingpandas/) to calculate:
  - [X] [Boat acceleration](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_acceleration);
  - [X] [Boat angular difference](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_angular_difference);
  - [X] [Boat speed](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_speed);
  - [X] [Time delta](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_timedelta);
  - [X] [Boat distance](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.distance);
  - [X] [Boat direction](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_direction);
- Get weather forecast from the sailing date and save on the database:
  - [X] Get Weather Station and Weather data using [meteostat](https://meteostat.net/en/station/87178) [Python API](https://dev.meteostat.net/guide.html#our-services)
  - [X] [Open Weather Map](https://openweathermap.org/api/one-call-3#history)
- Generate automatic analysis (weather data?):
  - [ ] Identifying `No-Go Zone` (45° from wind direction on both directions); 
  - [ ] Identifying the [Upwind, Beam Reaching and Downwind](https://www.nmma.org/lib/img/gallery/img13319214254.jpg) sailing segments of the trajectory;
- Generate sailing map with:
  - [X] Trajectory segment for a specific date and time (start and end);
  - [X] Trajectory and wind conditions using [wind brabs](#wind-barbs) [more info here](https://www.weather.gov/hfo/windbarbinfo);
  - [ ] Identify `OK` and `not OK` tacks;

- Generate sailing report with:
  - General overview about:
  - [ ] Weather conditions;
  - [ ] Sailing;
  - [X] Maps;

# TODOs:

- [ ] Join weather data on traj dataframe;

# Using:

## Configuring the environment variables

In order to use sailing data analysis it is necessary to have set a `.env` file:
```commandline
# .env
OPENWEATHER_KEY='<your_key>'
DB_URL='postgresql+psycopg2://<user>:<password>@172.17.0.2/<db_name>'
```
if necessary, take a look on [.env-example](.env-example) file.

## Applying migrations
The following comando shound apply all migrations using alembic
```commandline
alembic upgrade head
```

## Exporting GPX to database

Use [export_gpx](spatial_tools.py#81) function to export a gpx file to the database: 
```python
from spatial_tools import export_gpx

track_df, trajectory = export_gpx(
    gpx_path="path_to_the.gpx",
    layer="track_points",
)
```

This function will get the track_point from gpx, convert datetime data to Buenos Aires timezone, calculate a acceleration, angular difference, direction, distance and speed for each track segment, save as point and linestring geometries in the data base and return both as GeoDataFrame.

## Exporting GPX to database
[todo](https://geopandas.org/en/stable/docs/reference/api/geopandas.read_postgis.html)

## Weather data:

### retriving and processing weather data from Open Weather Map
Use [process_OWM_data](spatial_tools.py#162) function to process weather data from Opwn Weather Map. This function will call [get_OWM_data](spatial_tools.py#138) which, after confirming there is weather data already saved for that track, will get coordinates and datime for each `step` parameter and retrieve the data (using OpenWeatherMap API) appending it to a jsonline.
```python
from spatial_tools import process_OWM_data
owm_data = process_OWM_data(track_df)
```

### saving OWM data to database
Use [save_OWM_data](spatial_tools.py#198) to save Open Weather Map data in the data base using [pandas.to_sql](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html);
```python
from spatial_tools import save_OWM_data
save_OWM_data(owm_data)
```

### Creating maps

#### Trajectory maps
[create_traj_map](spatial_tools.py#262) creates the vizualization (A.K.A. map) of a [trajectory](https://movingpandas.readthedocs.io/en/main/trajectory.html) data
```python
from spatial_tools import create_traj_map
create_traj_map(
    traj=trajectory,
    map_title="REGATA INDEPENDENCIA: entire",
    save=True)
```

**Plot a section of a sailing track:**
```python
from datetime import datetime
create_traj_map(
    traj=trajectory,
    map_title="REGATA INDEPENDENCIA: 1ra boya",
    save=True,
    start=datetime(2023, 7, 30, 9, 30),
    stop=datetime(2023, 7, 30, 10, 41),
)
```


**Adding contra info**
```python
create_traj_map(
    traj=trajectory,
    map_title="REGATA INDEPENDENCIA: 1ra boya - contra",
    save=True,
    start=datetime(2023, 7, 30, 9, 30),
    stop=datetime(2023, 7, 30, 10, 41),
    contra=True
)
```

**Adding wind direction and speed info:**
```python
create_traj_map(
    traj=trajectory,
    map_title="REGATA INDEPENDENCIA: 1ra boya - contra",
    save=True,
    start=datetime(2023, 7, 30, 9, 30),
    stop=datetime(2023, 7, 30, 10, 41),
    contra=True,
    weather=owm_data
)
```
# Contributing

## Migrations:
When ever a change is done in [models.py](./models.py), a migrations should be created:

```commandline
alembic revision --autogenerate -m "msg"
```

After creating migration, make sure to review it as it is normal that it needs some improvements, like:
* **remove** a drop case is included for the table `ref_sys` on `upgrade()`;
* **remove** a create case is included for the table `ref_sys` on `downgrade()`;
* **remove** spatial indexes created on `upgrade()`;
* **import** `geoalchemy2` as it is used but not imported;

## Applying migrations
To persist the change done in the [models.py](./models.py) migrations should be applied:

```commandline
alembic upgrade head
```

## Wind barbs

![](https://www.metvuw.com/graphics/windsymbols.gif)
