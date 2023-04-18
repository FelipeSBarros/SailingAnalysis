import logging

from meteostat import Stations, Hourly

from models import engine, Session, WeatherStation, Weather


def get_nearby_weather_station(lon, lat):
    """
    Use meteostat API to identify nearby stations
    """
    station = Stations()
    station = station.nearby(lat, lon)
    station = station.fetch(1)
    return station


def save_weather_station(station):
    with Session() as session:
        record_exists = (
            session.query(WeatherStation).filter_by(id=station.index[0]).first()
        )
        if record_exists:
            logging.warning(f"record already exists {record_exists.id}")
        else:
            station.to_sql(WeatherStation.__tablename__, engine, if_exists="append")
            logging.warning(f"Station saved {station.index[0]}")


def get_weather_from_dates(datetime_start, datetime_end, station_index):
    data = Hourly(station_index, datetime_start, datetime_end)
    # check coverage
    coverage = data.coverage()
    if not coverage:
        logging.warning(f"Converage not complete. Using normalize to fill gaps.")
        data = data.normalize()

    data = data.fetch()
    return data


def save_weather_data(weather_data, station_id):
    weather_data["station"] = station_id
    with Session() as session:
        record_exists = (
            session.query(Weather).filter_by(station=station_id).first()
        )  # todo pensar em como colocar restricao
        if record_exists:
            logging.warning(f"record already exists {record_exists.id}")
        else:
            weather_data.to_sql(Weather.__tablename__, engine, if_exists="append")
            logging.warning(f"Station saved {weather_data.index[0]}")
