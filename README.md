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

* Configuring the environment

In order to use sailing data analysis it is nacessary to have set a `.env` file:
```commandline
# .env
OPENWEATHER_KEY='<your_key>'
DB_URL='postgresql+psycopg2://<user>:<password>@172.17.0.2/<db_name>'
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
