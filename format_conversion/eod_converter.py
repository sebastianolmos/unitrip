import pandas as pd
import geopandas as gpd
import h3
from datetime import datetime, timedelta

# Helping function to create origin datetime object from origin column (H:m) with dummy year, month,day
def set_origin_time(hour_origin):
    dt1 = datetime.strptime(hour_origin, '%H:%M').replace(year=2012, month=1, day=1) # Set dummy date(year, month,day)
    return dt1

# Helping function to create destination datetime object from destination column (H:m) with dummy year, month,day
# also correct the arrival time if necessary
def set_destination_time(row):
    hour_origin = row['HoraIni']
    hour_destination = row['HoraFin']
    dt1 = datetime.strptime(hour_origin, '%H:%M').replace(year=2012, month=1, day=1) # Set dummy date(year, month,day)
    dt2 = datetime.strptime(hour_destination, '%H:%M').replace(year=2012, month=1, day=1) # Set dummy date(year, month,day)
    time_difference = dt2 - dt1
    if time_difference.total_seconds() < 0:
        return dt2 + timedelta(days=1)
    else:
        return dt2


def eod_to_unitrip(trips_file, output_name, h3_res=12):
    # Delete NaN values in trips
    trips_cleaned = trips_file.dropna()
    # Fix time formats
    print("Fixing origin and destination time formats ...")
    pd.options.mode.chained_assignment = None
    trips_cleaned['o_time'] = trips_cleaned['HoraIni'].apply(set_origin_time)
    trips_cleaned['d_time'] = trips_cleaned.apply(set_destination_time, axis=1)
    # Delete trips with null origin or destination
    trips_cleaned = (trips_cleaned
                 .pipe(lambda x: x[x.OrigenCoordX != '0'])
                 .pipe(lambda x: x[x.DestinoCoordX != '0'])
                 .pipe(lambda x: x[x.OrigenCoordY != '0'])
                 .pipe(lambda x: x[x.DestinoCoordY != '0'])
                 )
    print("There are", trips_cleaned.shape[0], "correct trips")
    # Fix the coord format and the geographic coordinate system code, also the h3 cells are included
    print("Calculating h3 cells to origin and destination coords ...")
    trips_cleaned['OrigenCoordX'] = trips_cleaned['OrigenCoordX'].apply(lambda x: x.replace(",", "."))
    trips_cleaned['OrigenCoordY'] = trips_cleaned['OrigenCoordY'].apply(lambda x: x.replace(",", "."))
    trips_cleaned['DestinoCoordX'] = trips_cleaned['DestinoCoordX'].apply(lambda x: x.replace(",", "."))
    trips_cleaned['DestinoCoordY'] = trips_cleaned['DestinoCoordY'].apply(lambda x: x.replace(",", "."))
    
    current_crs = 'EPSG:5361'
    target_crs = 'EPSG:4326'

    origin_points = gpd.points_from_xy(trips_cleaned.OrigenCoordX, trips_cleaned.OrigenCoordY, crs=current_crs).to_crs(target_crs)
    dest_points = gpd.points_from_xy(trips_cleaned.DestinoCoordX, trips_cleaned.DestinoCoordY, crs=current_crs).to_crs(target_crs)

    trips_cleaned['o_lat'] = [p.y for p in origin_points]
    trips_cleaned['o_lon'] = [p.x for p in origin_points]
    trips_cleaned['d_lat'] = [p.y for p in dest_points]
    trips_cleaned['d_lon'] = [p.x for p in dest_points]
    trips_cleaned['o_h3_cell'] = [h3.latlng_to_cell(p.y, p.x, h3_res) for p in origin_points]
    trips_cleaned['d_h3_cell'] = [h3.latlng_to_cell(p.y, p.x, h3_res) for p in dest_points]

    # Column names and column order are rearranged.
    trips_cleaned = trips_cleaned.drop(['OrigenCoordX', 'OrigenCoordY', 'DestinoCoordX', 'DestinoCoordY','HoraIni', 'HoraFin', 'Viaje'], axis=1)
    trips_cleaned = trips_cleaned.rename({'Persona': 'user_id'}, axis=1)
    trips_to_file = trips_cleaned[['user_id', 'o_lon', 'o_lat', 'd_lon', 'd_lat', 'o_h3_cell', 'd_h3_cell', 'o_time', 'd_time']]
    trips_to_file.index.name="trip_id"

    print("Dataframe ready to store")
    trips_to_file.to_parquet(output_name, engine='pyarrow', compression='snappy')
    print("File stored at", output_name)