import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json
import login


access_token = login.get_access_token()
response_data = login.fetch_usage(access_token=access_token)

usage_data = response_data["usage"]
flattened_data = []

def save_usage_data(usage_data: json):
    for entry in usage_data:
        reading = entry["reading"]
        interval_read = reading["interval_read"]
        start_datetime = datetime.strptime(reading["read_start_date"], "%Y-%m-%d")

    # Generate timestamps for each 5-minute interval
        timestamps = [start_datetime + timedelta(minutes=5) + timedelta(minutes=i*5) for i in range(len(interval_read["interval_reads"]))]

    # Append data for each 5-minute interval
        for i, timestamp in enumerate(timestamps):
            flattened_data.append({
                "datetime": timestamp.strftime("%Y-%m-%d %H:%M"),
                "controlled_load": reading["controlled_load"],
                "service_point_id": reading["service_point_id"],
                "suffix": reading["register_suffix"],
                "interval_read": interval_read["interval_reads"][i]
            })

    # Create a DataFrame from the flattened data
        df = pd.DataFrame(flattened_data)
        df.sort_values(by='datetime', inplace=True)

    # Save the DataFrame to a CSV file
        df.to_csv("usage_data.csv", index=False)




