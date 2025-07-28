import pandas as pd
import geopandas as gpd
import h3

def unitrip_to_uniflow(unitrip, output_name, flow_res=8, minimun_trips=5):
    print("Set the h3 cell columns to a parent resolution ...")
    unitrip['o_h3_cell'] = unitrip['o_h3_cell'].apply(lambda cell: h3.cell_to_parent(cell, flow_res))
    unitrip['d_h3_cell'] = unitrip['d_h3_cell'].apply(lambda cell: h3.cell_to_parent(cell, flow_res))

    print("Trips from one cell to the same cell are deleted, and the same OD trips made by a user are grouped together. ...")
    filtered_unitrip = (unitrip
                    .pipe(lambda x: x[x.o_h3_cell != x.d_h3_cell])
                    .groupby(['user_id', 'o_h3_cell', 'd_h3_cell'])
                    .size()
                    )
    filtered_unitrip.name = 'n_trips'
    filtered_unitrip = filtered_unitrip.reset_index()
    filtered_unitrip.index.name="trip_id"
    print("There are", filtered_unitrip.shape[0], "unique trips")

    print("Aggregating trips of the same OD and with a minimun number of trips ...")
    flows = (filtered_unitrip
         [filtered_unitrip.o_h3_cell != filtered_unitrip.d_h3_cell]
         .groupby(['o_h3_cell', 'd_h3_cell'])
         ['n_trips']
         .sum()
         .reset_index()
         .pipe(lambda x: x[x.n_trips > minimun_trips])
         .rename({'n_trips': 'count'}, axis=1)
        )
    print("There are", flows.shape[0], "flows")
    
    flows.to_parquet(output_name, engine='pyarrow', compression='snappy')
    print("File stored at", output_name)