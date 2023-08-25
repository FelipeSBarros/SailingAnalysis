from datetime import datetime, timezone, timedelta

from spatial_tools import process_OWM_data, create_traj_map, export_gpx, save_OWM_data

BAIRES_TZ = timezone(timedelta(hours=-3))
track_df, trajectory = export_gpx(
    gpx_path="/mnt/Trabalho/DonCarlos_Tracks/Track_23-ABR-23 132017.gpx",
    layer="track_points",
)

weather_data = process_OWM_data(track_df)
save_OWM_data(weather_data)
create_traj_map(
    traj=trajectory,
    map_title="Largada",
    start=datetime(2023, 4, 23, 10, 5),
    stop=datetime(2023, 4, 23, 10, 30),
    weather=weather_data,
)
create_traj_map(
    traj=trajectory,
    map_title="primeira perna",
    start=datetime(2023, 4, 23, 10, 20),
    stop=datetime(2023, 4, 23, 12, 0),
    weather=weather_data,
)
create_traj_map(
    traj=trajectory,
    map_title="segunda perna (Popa-través)",
    start=datetime(2023, 4, 23, 12),
    stop=datetime(2023, 4, 23, 12, 55),
    weather=weather_data,
)
create_traj_map(
    traj=trajectory,
    map_title="Toda regata",
    start=datetime(2023, 4, 23, 10, 5),
    stop=datetime(2023, 4, 23, 12, 55),
    weather=weather_data,
)
