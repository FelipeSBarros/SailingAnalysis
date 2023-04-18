import os
from typing_extensions import Annotated

from sqlalchemy.schema import FetchedValue
from datetime import datetime
from sqlalchemy import func
from dotenv import load_dotenv
from sqlalchemy import String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)

load_dotenv()
# DB_NAME = os.getenv("DB_NAME")

engine = create_engine(os.getenv("DB_URL"), echo=True)

Session = sessionmaker(bind=engine)

timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Base(DeclarativeBase):  # todo Base = declarative_base()
    pass


class WeatherStation(Base):
    __tablename__ = "weather_station"

    id: Mapped[str] = mapped_column(
        primary_key=True, comment="The Meteostat ID of the weather station"
    )  # todo use uuri
    name: Mapped[str] = mapped_column(comment="The English name of the weather station")
    country: Mapped[str] = mapped_column(
        comment="The ISO 3166-1 alpha-2 country code of the weather station"
    )
    region: Mapped[str] = mapped_column(
        nullable=True,
        comment="The ISO 3166-2 state or region code of the weather station",
    )
    wmo: Mapped[str] = mapped_column(
        nullable=True, comment="The WMO ID of the weather station"
    )
    icao: Mapped[str] = mapped_column(
        nullable=True, comment="The ICAO ID of the weather station"
    )
    latitude: Mapped[float] = mapped_column(
        nullable=False, comment="The latitude of the weather station"
    )
    longitude: Mapped[float] = mapped_column(
        nullable=False, comment="The longitude of the weather station"
    )
    elevation: Mapped[float] = mapped_column(
        nullable=True,
        comment="The elevation of the weather station in meters above sea level",
    )
    timezone: Mapped[str] = mapped_column(
        nullable=True, comment="The time zone of the weather station	"
    )
    hourly_start: Mapped[datetime] = mapped_column(
        nullable=True, comment="The first day on record for hourly data"
    )
    hourly_end: Mapped[datetime] = mapped_column(
        nullable=True, comment="The last day on record for hourly data"
    )
    daily_start: Mapped[datetime] = mapped_column(
        nullable=True, comment="The first day on record for daily data"
    )
    daily_end: Mapped[datetime] = mapped_column(
        nullable=True, comment="The last day on record for daily data"
    )
    monthly_start: Mapped[datetime] = mapped_column(
        nullable=True, comment="The first day on record for monthly data"
    )
    monthly_end: Mapped[datetime] = mapped_column(
        nullable=True, comment="The last day on record for monthly data"
    )
    distance: Mapped[float] = mapped_column(
        nullable=True, comment="Distance. Comes from station.nearby function"
    )
    created_at: Mapped[timestamp]


class Weather(Base):
    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(primary_key=True)  # todo use uuri
    station: Mapped[str] = mapped_column(
        ForeignKey("weather_station.id"),
        comment="The Meteostat ID of the weather station (only if query refers to multiple stations)",
    )
    time: Mapped[datetime] = mapped_column(
        nullable=False, comment="The datetime of the observation	"
    )
    temp: Mapped[float] = mapped_column(
        nullable=False, comment="The air temperature in °C"
    )
    dwpt: Mapped[float] = mapped_column(nullable=True, comment="The dew point in °C")
    rhum: Mapped[float] = mapped_column(
        nullable=False, comment="The relative humidity in percent (%)"
    )
    prcp: Mapped[float] = mapped_column(
        nullable=False, comment="The one hour precipitation total in mm"
    )
    snow: Mapped[float] = mapped_column(nullable=True, comment="The snow depth in mm")
    wdir: Mapped[float] = mapped_column(
        nullable=False, comment="The average wind direction in degrees (°)"
    )
    wspd: Mapped[float] = mapped_column(
        nullable=False, comment="The average wind speed in km/h"
    )
    wpgt: Mapped[float] = mapped_column(
        nullable=True, comment="The peak wind gust in km/h"
    )
    pres: Mapped[float] = mapped_column(
        nullable=True, comment="The average sea-level air pressure in hPa"
    )
    tsun: Mapped[float] = mapped_column(
        nullable=True, comment="The one hour sunshine total in minutes (m)"
    )
    coco: Mapped[float] = mapped_column(
        nullable=True, comment="The weather condition code"
    )
    created_at: Mapped[timestamp]
