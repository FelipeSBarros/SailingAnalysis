from spatial_tools import process_OWM_data, create_traj_map, export_gpx
from datetime import datetime

track_df, trajectory = export_gpx(
    gpx_path="/mnt/Trabalho/DonCarlos_Tracks/Track_23-ABR-23 132017.gpx",
    layer="track_points",
)

weather_data = process_OWM_data(track_df)

create_traj_map(
    traj=trajectory,
    map_title="Largada",
    start=datetime(2023, 4, 23, 10, 5),
    stop=datetime(2023, 4, 23, 10, 30),
)
create_traj_map(
    traj=trajectory,
    map_title="Senida",
    start=datetime(2023, 4, 23, 10, 20),
    stop=datetime(2023, 4, 23, 12, 0),
)
create_traj_map(
    traj=trajectory,
    map_title="Popa",
    start=datetime(2023, 4, 23, 12),
    stop=datetime(2023, 4, 23, 12, 55),
)
create_traj_map(
    traj=trajectory,
    map_title="Toda regata",
    start=datetime(2023, 4, 23, 10, 5),
    stop=datetime(2023, 4, 23, 12, 55),
)


create_traj_map(
    traj=trajectory,
    map_title="Senida",
    start=datetime(2023, 4, 23, 12, 38),
    stop=datetime(2023, 4, 23, 13, 0),
)

weather_data[["wind_deg", 'wind_speed', 'time']]