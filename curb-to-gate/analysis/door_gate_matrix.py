# door to gate matrix

import pandas as pd
from postgres import query_postgres


data = query_postgres('dev', 'door_gate_matrix')  # query data
df = pd.DataFrame(data)  # convert to dataframe
df_reorder = df[['terminal', 'door', 'gate', 'dwell_time', 'travel_time']]
df_reorder.to_csv('data/%s.csv' % 'door_gate_matrix', index=False)  # output to csv
print('output to csv')
