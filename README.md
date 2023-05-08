# Sailing Analysis

Package under construction to automate data analysis from sailing boats.

## Functionalities:
- Get sailing track from GPX and save it on a spatially enabled database (using [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/en/latest/):
  - [ ] [SpatialLite](https://live.osgeo.org/es/overview/spatialite_overview.html)
  - [ ] [PostGIS](https://postgis.net/);
  - [X] [Geopackage](https://www.geopackage.org/);
- For each track segment, use [MovingPandas](https://movingpandas.github.io/movingpandas/) to calculate:
  - [X] [Boat acceleration](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_acceleration);
  - [X] [Boat angular difference](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_angular_difference);
  - [X] [Boat speed](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_speed);
  - [X] [Time delta](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_timedelta);
  - [X] [Boat distance](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.distance);
  - [X] [Boat direction](https://movingpandas.readthedocs.io/en/main/trajectory.html#movingpandas.Trajectory.add_direction);
- Get weather forecast for the sailing date:
  - [X] Get Weather Station data and Weather data using [meteostat](https://meteostat.net/en/station/87178) [Python API](https://dev.meteostat.net/guide.html#our-services)
  - [X] [Open Weather Map](https://openweathermap.org/api/one-call-3#history)
- Generate automatic analysis (weather data?):
  - Identifying `No-Go Zone` (45° from wind direction on both directions); 
  - Identifying the [Upwind, Beam Reaching and Downwind](https://www.nmma.org/lib/img/gallery/img13319214254.jpg) sailing segments of the trajectory;
- Generate sailing report with:
  - Trajectory segment for a specific date and time (start and end);
  - Identify `OK` and `not OK` tacks;
  - Trajectory for each boat information;

- Generate sailing report with:
  - General overview about:
  - [ ] Weather conditions;
  - [ ] Sailing;
  - [ ] Maps;