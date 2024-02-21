import streamlit as st
import pandas as pd 
import paramiko
from time import sleep
from datetime import datetime
from random import uniform
from collections import deque

def parse_real_time_data(data, historic_data):
    lines = data.strip().split('\n')
    table_data = []
    trend = deque()
    symbol = None
    last_price = 0
    change = 0
    for line in lines:
        if line.startswith('!'):
            _, timestamp = line.split(',')
        else:
            line_parts = line.split(',')
            if len(line_parts) >= 3:
                symbol, last_price, _ = line.split(',')
                change = 0
            
            if symbol in historic_data:
                trend = historic_data[symbol]
                change = float(last_price) - trend[-1]
                trend.append(float(last_price))
                if len(trend) > 25:
                    trend.popleft()

                historic_data[symbol] = trend
            else: 
                historic_data[symbol] = deque([float(last_price)])

            # Avoid division by zero
            percent_change = (change / float(last_price)) * 100 if float(last_price) != 0 else 0
            
            table_data.append({
                    'Symbol' : symbol,
                    'Price' : float(last_price),
                    'Change': change,
                    '% Change': percent_change,
                    'Trend': list(trend),
                })
    return table_data

def connect_ssh_agent(): 
    hostname = "rt1.olsendata.com"
    port = 22103
    username = "aarsh"
    password = "aar5hvya5"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)
    
    return ssh.invoke_shell()

def get_real_time_data(channel, historic_data):
    data = channel.recv(1024).decode('ascii')

    table_data = parse_real_time_data(data, historic_data)

    return table_data

# Other functions remain the same...

def main():

    unique_symbols = set()

    channel = connect_ssh_agent()
    st.title("Real Time Prices")

    container = st.empty()

    while True:
        new_data = get_real_time_data(channel, st.session_state)
        #new_data = get_dummy_real_time_data(st.session_state)

        if new_data:
            table_data = pd.DataFrame(new_data) 

            if 'Trend' in table_data.columns:

                unique_symbols.update(table_data['Symbol'].tolist())
                unique_symbols_list = list(unique_symbols)

                fixed_symbols_df = pd.DataFrame({'Symbol': unique_symbols_list})
                merged_data = pd.merge(fixed_symbols_df, table_data, on='Symbol', how='left')
                
                container.data_editor(
                     merged_data[['Symbol', 'Trend', 'Price', 'Change', '% Change']].drop_duplicates(subset=['Symbol']),
                     column_config={
                         "Symbol": st.column_config.TextColumn("Symbol"),
                         "Trend": st.column_config.LineChartColumn(
                             "Trend",
                             width="medium",
                             ),
                               "Price": st.column_config.NumberColumn("Price"),
                               "Change": st.column_config.NumberColumn("Change"),
                               "% Change": st.column_config.NumberColumn("% Change"),
                    },
                    hide_index=True,
                    use_container_width = True
                )
        sleep(1)

if __name__ == "__main__":
    main()
