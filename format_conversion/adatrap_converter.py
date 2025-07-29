import pandas as pd
import geopandas as gpd
import h3
import unicodedata

# Function to fix the format of the stops (those ending with letters after the hyphen)
def fix_station(station):
    result_list = station.split('-')
    if len(result_list) < 2:
        return station
    if not(result_list[-1].isdigit()):
        result_list[-1], result_list[-2] = result_list[-2], result_list[-1]
        result_string = "-".join(result_list)
        return result_string
    else:
        return station
    
# Function to fix the format of subway station names
def standardize_spanish_station(text):
    result_list = text.split('-')
    if len(result_list) < 2:
        # Normalize the string to NFKD form (separates base characters from diacritics)
        normalized_text = unicodedata.normalize('NFKD', text)
        # Filter out combining characters (diacritics)
        standardized_text = ''.join([
            c for c in normalized_text if not unicodedata.combining(c)
        ])
        standardized_text = standardized_text.replace('`', "").upper()
        return standardized_text
    else:
        return text

def adatrap_to_unitrip(trips_file, stations_file, output_name, h3_res=12):
    # A table is created with correct trips, from the first stop to the first depature at stations.
    trips_station_1 = trips_file[['id', 'paraderosubida_1era', 'paraderobajada_1era', 'tiemposubida_1era', 'tiempobajada_1era']]
    trips_station_1_filtered = trips_station_1[trips_station_1['paraderosubida_1era'] != '-']
    trips_station_1_filtered_bajada = trips_station_1_filtered[trips_station_1_filtered['paraderobajada_1era'] != '-']
    trips_station_1_filtered_bajada = trips_station_1_filtered_bajada.rename({'id': 'user_id', 'paraderosubida_1era':'subida', 'paraderobajada_1era':'bajada',
                                                                            'tiemposubida_1era':'o_time', 'tiempobajada_1era':'d_time'}, axis=1)
    print("There are", trips_station_1_filtered_bajada.shape[0], "trips from the first stop to the first depature")
    
    # Another table is created with correct trips, from the second stop to the second departure at bus stations.
    trips_station_2 = trips_file[['id', 'paraderosubida_2da', 'paraderobajada_2da', 'tiemposubida_2da', 'tiempobajada_2da']]
    trips_station_2_filtered = trips_station_2[trips_station_2['paraderosubida_2da'] != '-']
    trips_station_2_filtered_bajada = trips_station_2_filtered[trips_station_2_filtered['paraderobajada_2da'] != '-']
    trips_station_2_filtered_bajada = trips_station_2_filtered_bajada.rename({'id': 'user_id', 'paraderosubida_2da':'subida', 'paraderobajada_2da':'bajada',
                                                                            'tiemposubida_2da':'o_time', 'tiempobajada_2da':'d_time'}, axis=1)
    print("There are", trips_station_2_filtered_bajada.shape[0], "trips from the second stop to the second depature")
    
    # Another table is created with correct trips, from the third stop to the third departure at bus stations.
    trips_station_3 = trips_file[['id', 'paraderosubida_3era', 'paraderobajada_3era', 'tiemposubida_3era', 'tiempobajada_3era']]
    trips_station_3_filtered = trips_station_3[trips_station_3['paraderosubida_3era'] != '-']
    trips_station_3_filtered_bajada = trips_station_3_filtered[trips_station_3_filtered['paraderobajada_3era'] != '-']
    trips_station_3_filtered_bajada = trips_station_3_filtered_bajada.rename({'id': 'user_id', 'paraderosubida_3era':'subida', 'paraderobajada_3era':'bajada',
                                                                            'tiemposubida_3era':'o_time', 'tiempobajada_3era':'d_time'}, axis=1)
    print("There are", trips_station_3_filtered_bajada.shape[0], "trips from the third stop to the third depature")
    
    # Another table is created with correct trips, from the fourth stop to the fourth departure at bus stations.
    trips_station_4 = trips_file[['id', 'paraderosubida_4ta', 'paraderobajada_4ta', 'tiemposubida_4ta', 'tiempobajada_4ta']]
    trips_station_4_filtered = trips_station_4[trips_station_4['paraderosubida_4ta'] != '-']
    trips_station_4_filtered_bajada = trips_station_4_filtered[trips_station_4_filtered['paraderobajada_4ta'] != '-']
    trips_station_4_filtered_bajada = trips_station_4_filtered_bajada.rename({'id': 'user_id', 'paraderosubida_4ta':'subida', 'paraderobajada_4ta':'bajada',
                                                                            'tiemposubida_4ta':'o_time', 'tiempobajada_4ta':'d_time'}, axis=1)
    print("There are", trips_station_4_filtered_bajada.shape[0], "trips from the fourth stop to the fourth depature")
    # All trips tables between stations are concatenated
    trips_station = pd.concat([trips_station_1_filtered_bajada, trips_station_2_filtered_bajada, trips_station_3_filtered_bajada, trips_station_4_filtered_bajada])
    print("There are", trips_station.shape[0], "trips in total")

    # Fix stop station format
    print("Fixing stations name format ...")
    trips_station['subida'] = trips_station['subida'].apply(fix_station)
    trips_station['bajada'] = trips_station['bajada'].apply(fix_station)


    stations_table = stations_file.rename({'parada/est.metro': 'parada'}, axis=1)
    # Fix subway stations names
    stations_table['parada'] = stations_table['parada'].apply(standardize_spanish_station)

    trips_station.index.name = "trajectory_id"
    trips_station = trips_station.reset_index()
    trips_station.index.name = "trip_id"
    trips_station = trips_station.reset_index()

    # The first merge is to obtain the coordinates of the stop stations
    trips_stations_coords = trips_station.merge(stations_table, how='inner', left_on='subida', right_on='parada')
    trips_stations_coords = trips_stations_coords.groupby('trip_id', group_keys=False).first().reset_index()
    trips_stations_coords = trips_stations_coords.drop(['subida', 'parada', 'trip_id'], axis=1)
    trips_stations_coords = trips_stations_coords.rename({'x': 'o_x', 'y':'o_y'}, axis=1)
    trips_stations_coords.index.name = "trip_id"
    trips_stations_coords = trips_stations_coords.reset_index()

    # The second merge is to obtain the coordinates of the departure stations
    trips_stations_d = trips_stations_coords.merge(stations_table, how='inner', left_on='bajada', right_on='parada')
    trips_stations_d = trips_stations_d.groupby('trip_id', group_keys=False).first().reset_index()
    trips_stations_d = trips_stations_d.drop(['bajada', 'parada'], axis=1)
    trips_stations_d = trips_stations_d.rename({'x': 'd_x', 'y':'d_y'}, axis=1)
    print("There are", trips_stations_d.shape[0], "trips with recognizable stations")

    print("Fixing crs coordinate system format and getting h3 cell per OD location ...")
    # Fix the coord format and the geographic coordinate system code, also the h3 cells are included
    current_crs = 'EPSG:5361'
    target_crs = 'EPSG:4326'

    origin_points = gpd.points_from_xy(trips_stations_d.o_x, trips_stations_d.o_y, crs=current_crs).to_crs(target_crs)
    dest_points = gpd.points_from_xy(trips_stations_d.d_x, trips_stations_d.d_y, crs=current_crs).to_crs(target_crs)

    trips_stations_d['o_lat'] = [p.y for p in origin_points]
    trips_stations_d['o_lon'] = [p.x for p in origin_points]
    trips_stations_d['d_lat'] = [p.y for p in dest_points]
    trips_stations_d['d_lon'] = [p.x for p in dest_points]
    trips_stations_d['o_h3_cell'] = [h3.latlng_to_cell(p.y, p.x, h3_res) for p in origin_points]
    trips_stations_d['d_h3_cell'] = [h3.latlng_to_cell(p.y, p.x, h3_res) for p in dest_points]

    # Column names and column order are rearranged.
    trips_stations_cleaned = trips_stations_d.drop(['o_x', 'o_y', 'd_x', 'd_y', 'trip_id', 'trajectory_id'], axis=1)
    trips_to_file = trips_stations_cleaned[['user_id', 'o_lon', 'o_lat', 'd_lon', 'd_lat', 'o_h3_cell', 'd_h3_cell', 'o_time', 'd_time']]
    trips_to_file.index.name="trip_id"

    # Save as a parquet file
    trips_to_file.to_parquet(output_name, engine='pyarrow', compression='snappy')
    print("File stored at", output_name)