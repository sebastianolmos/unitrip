import osmnx as ox
import pandas as pd
import geopandas as gpd
import h3

def shift(df):
    origin = df.rename({'geometry': 'o_point','h3_cell':'o_h3_cell','datetime':'o_time'}, axis=1)[['user_id', 'o_point', 'o_h3_cell', 'o_time']].shift()
    destination = df.rename({'user_id': 'user_id_d', 'geometry': 'd_point','h3_cell':'d_h3_cell','datetime':'d_time'}, axis=1)[['user_id_d', 'd_point', 'd_h3_cell', 'd_time']]
    trips = (origin.join(destination)
             .dropna()
             .pipe(lambda x: x[x.user_id == x.user_id_d])
            )
    return trips

def foursquare_to_unitrip(raw_pois, raw_checkins, municipalities, output_name, h3_resolution=12):
    print("Retrieving municipalities data from Open Street Maps ...")
    amb = ox.geocoder.geocode_to_gdf(municipalities)

    bbox = amb.total_bounds
    pois_in_bbox = raw_pois[raw_pois.lon.between(bbox[0], bbox[2]) & raw_pois.lat.between(bbox[1], bbox[3])]
    print("There are", pois_in_bbox.shape[0], "POIs in the area bounding box")

    pois_gdf = gpd.GeoDataFrame(pois_in_bbox[['venue_id', 'category']],
                            geometry=gpd.points_from_xy(pois_in_bbox.lon, pois_in_bbox.lat),
                            crs='EPSG:4326')
    
    pois_grid = gpd.sjoin(pois_gdf, amb[['geometry']], predicate='within', how='inner')
    pois_in_grid = pois_grid.groupby('venue_id', group_keys=False).first().reset_index()
    print("There are", pois_in_grid.shape[0], "POIs in the municipalities")

    print("Gathering checkins that are inside the municipalities...")
    amb_check_ins = raw_checkins[raw_checkins.venue_id.isin(pois_in_grid.venue_id)]
    print("There are", amb_check_ins.shape[0], "Check-ins in the municipalities")

    print("Crossing check-ins data with POIs location data...")
    check_ins_points = amb_check_ins.merge(pois_in_grid, left_on='venue_id', right_on='venue_id', how='left') 
    check_ins_points = check_ins_points.drop(columns=['utc_offset', 'category', 'index_right']) 
    
    print("Calculating the h3 cell index per check-in...")
    check_ins_points['h3_cell'] = check_ins_points['geometry'].apply(lambda point: h3.latlng_to_cell(point.y, point.x, h3_resolution))

    print("Sorting the table per user and datetime...")
    check_ins_points.index.name = 'checkin_id'
    checkins_sorted = check_ins_points.sort_values(by=['user_id', 'datetime'], ascending=[True, True])

    print("Building origin-destination pairs with each user's movements ...")
    user_trip_counts = shift(checkins_sorted).reset_index()
    user_trip_counts.index.name="trip_id"
    print("There are", user_trip_counts.shape[0], "trips")

    trips = user_trip_counts.drop("checkin_id", axis=1)

    print("Building trips with the Unitrip format ...")
    trips['o_lon'] = trips['o_point'].apply(lambda point: point.x)
    trips['o_lat'] = trips['o_point'].apply(lambda point: point.y)
    trips['d_lon'] = trips['d_point'].apply(lambda point: point.x)
    trips['d_lat'] = trips['d_point'].apply(lambda point: point.y)
    trips_file = trips.drop(["o_point", "d_point"], axis=1)
    trips_to_file = trips_file[['user_id', 'o_lon', 'o_lat', 'd_lon', 'd_lat', 'o_h3_cell', 'd_h3_cell', 'o_time', 'd_time']]
    print("Dataframe ready to store")

    trips_to_file.to_parquet(output_name, engine='pyarrow', compression='snappy')
    print("File stored at", output_name)