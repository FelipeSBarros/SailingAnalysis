# Sailing Analysis

Package under construction to automate data analysis from sailing boats.

## Functionalities:
- Get sailing track from GPX and save it on a spatially enabled database:
  - [ ] [SpatialLite](https://live.osgeo.org/es/overview/spatialite_overview.html)
  - [ ] [PostGIS](https://postgis.net/);
- For each track segment, use [MovingPandas](https://movingpandas.github.io/movingpandas/) to calculate:
  - [ ] Boat direction;
  - [ ] Boat distance traveled;
  - [ ] Boat speed;
  - [ ] Time delta;
- Get weather forecast for the sailing date:
  - [ ] [Meteorological forecast](https://meteostat.net/en/station/87178);
    - [ ] Try [API](https://dev.meteostat.net/guide.html#our-services)
  - [ ] [Open Weather Map](https://openweathermap.org/api/one-call-3#history)
- Incorporate weather information to sailing track
- Generate sailing report with:
  - General overview about:
  - [ ] Weather conditions;
  - [ ] Sailing;
  - [ ] Maps;