import pandas as pd
import geopandas as gpd
import h3

def generate_flows_locations(uniflow, output_flows_name, output_locations_name):
    unique_cells = pd.concat([uniflow['o_h3_cell'], uniflow['d_h3_cell']]).unique()
    cells_to_id = {cell : i for i, cell in enumerate(unique_cells)}
    
    uniflow['o_h3_cell'] = uniflow['o_h3_cell'].apply(lambda cell: cells_to_id[cell])
    uniflow['d_h3_cell'] = uniflow['d_h3_cell'].apply(lambda cell: cells_to_id[cell])

    uniflow_file = uniflow.rename({'o_h3_cell':'origin', 'd_h3_cell':'dest'}, axis=1)
    uniflow_file.to_csv(output_flows_name, index=False)
    print("flows file stored at", output_flows_name)

    uniflow_location = pd.DataFrame({'name': cells_to_id.values(), 
                                 'lat':[h3.cell_to_latlng(cell)[0] for cell in cells_to_id.keys()],
                                 'lon':[h3.cell_to_latlng(cell)[1] for cell in cells_to_id.keys()]})
    uniflow_location.index.name = 'id'
    uniflow_location.to_csv(output_locations_name)
    print("locations file stored at", output_locations_name)