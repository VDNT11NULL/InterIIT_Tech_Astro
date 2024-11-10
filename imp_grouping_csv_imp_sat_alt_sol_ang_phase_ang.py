import os
import csv
import numpy as np
from datetime import datetime, timedelta
from astropy.io import fits
from collections import defaultdict

# Directory containing your FITS files
source_dir = 'C:/Users/hp/Desktop/FITS FILE/POST_OD/isda_archive/ch2_bundle/cho_bundle/nop/cla_collection/cla/data/calibrated/2020/02/01/'
output_csv = 'C:/Users/hp/Desktop/INTER IIT TECH MEET HP-4/output.csv'

# 96-second interval
interval = timedelta(seconds=96)
current_time_window = timedelta(seconds=96)

# Initialize variables
grouped_files = []
group_start_time = None
group_end_time = None
group_count = 0

# Initialize variables to track the least and highest values for latitude and longitude
min_lat, max_lat = float('inf'), float('-inf')
min_lon, max_lon = float('inf'), float('-inf')

def parse_start_timestamp(filename):
    """Extracts the start timestamp from the FITS filename."""
    core_name = filename.split('_')[-2]
    start_timestamp_str = core_name.split('_')[0]
    start_timestamp = datetime.strptime(start_timestamp_str, '%Y%m%dT%H%M%S%f')
    return start_timestamp

def get_interval_start(timestamp, interval):
    epoch = datetime(1970, 1, 1)
    elapsed = timestamp - epoch
    interval_start = epoch + (elapsed // interval) * interval
    return interval_start

def calculate_average_of_key(grouped_files, key):
    """Calculates the average of a given key (e.g., SAT_ALT, SOLARANG, PHASEANG, EMISNANG) across grouped FITS files."""
    values = []
    for fits_file in grouped_files:
        with fits.open(fits_file) as hdul:
            header = hdul[1].header
            value = header.get(key)
            if value is not None:
                values.append(float(value))  # Convert to native float immediately
    if values:
        return round(np.mean(values), 3)
    return None

fits_files = sorted([os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.fits')], 
                    key=lambda f: parse_start_timestamp(os.path.basename(f)))

# Open CSV file for output
with open(output_csv, mode='w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Group Start Time', 'Group End Time', 'V0 Lon', 'V1 Lon', 'V0 Lat', 'V1 Lat', 'Summed Counts', 
                         'Channels', 'Energy', 'Avg SAT_ALT', 'Avg SOLARANG', 'Avg PHASEANG', 'Avg EMISNANG'])

    for fits_file in fits_files:
        filename = os.path.basename(fits_file)
        start_time = parse_start_timestamp(filename)
        
        # Initialize the first group
        if group_count == 0:
            group_start_time = start_time
            group_end_time = start_time + current_time_window

        if group_count < 12 and start_time <= group_end_time:
            grouped_files.append(fits_file)
            group_count += 1
        else:
            # Calculate averages for SAT_ALT, SOLARANG, PHASEANG, EMISNANG
            avg_sat_alt = calculate_average_of_key(grouped_files, 'SAT_ALT')
            avg_solarang = calculate_average_of_key(grouped_files, 'SOLARANG')
            avg_phaseang = calculate_average_of_key(grouped_files, 'PHASEANG')
            avg_emisnang = calculate_average_of_key(grouped_files, 'EMISNANG')
            
            # Sum counts for each channel in the group
            total_counts_by_channel = defaultdict(float)
            
            for fits_file_in_group in grouped_files:
                with fits.open(fits_file_in_group) as hdul:
                    data = hdul[1].data
                    if data is not None:
                        counts_data = data['COUNTS']
                        channel_data = data['CHANNEL']
                        for channel, count in zip(channel_data, counts_data):
                            total_counts_by_channel[channel] += float(count)

                        # Collect latitudes and longitudes for bounding box calculation
                        latitudes = [
                            hdul[1].header.get('V0_LAT'),
                            hdul[1].header.get('V1_LAT'),
                            hdul[1].header.get('V2_LAT'),
                            hdul[1].header.get('V3_LAT')
                        ]
                        longitudes = [
                            hdul[1].header.get('V0_LON'),
                            hdul[1].header.get('V1_LON'),
                            hdul[1].header.get('V2_LON'),
                            hdul[1].header.get('V3_LON')
                        ]
                        min_lat = min(min_lat, *map(float, latitudes))
                        max_lat = max(max_lat, *map(float, latitudes))
                        min_lon = min(min_lon, *map(float, longitudes))
                        max_lon = max(max_lon, *map(float, longitudes))
            
            # Convert accumulated counts to a list to store in CSV
            summed_counts_list = list(map(float, total_counts_by_channel.values()))
            channels = list(range(len(summed_counts_list)))

            # Calculate energy for each channel by multiplying channel value by 0.0135
            energy_list = [channel * 0.0135 for channel in channels]

            # Write group data to CSV
            csv_writer.writerow([
                group_start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                group_end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                float(min_lon), float(max_lon), float(min_lat), float(max_lat),
                summed_counts_list, channels, energy_list,
                avg_sat_alt, avg_solarang, avg_phaseang, avg_emisnang
            ])

            # Reset counters and data for the next group
            grouped_files = [fits_file]
            group_start_time = start_time
            group_end_time = start_time + current_time_window
            group_count = 1
            min_lat, max_lat = float('inf'), float('-inf')
            min_lon, max_lon = float('inf'), float('-inf')

    # Process remaining files in the last group
    if grouped_files:
        avg_sat_alt = calculate_average_of_key(grouped_files, 'SAT_ALT')
        avg_solarang = calculate_average_of_key(grouped_files, 'SOLARANG')
        avg_phaseang = calculate_average_of_key(grouped_files, 'PHASEANG')
        avg_emisnang = calculate_average_of_key(grouped_files, 'EMISNANG')

        total_counts_by_channel = defaultdict(float)
        
        for fits_file_in_group in grouped_files:
            with fits.open(fits_file_in_group) as hdul:
                data = hdul[1].data
                if data is not None:
                    counts_data = data['COUNTS']
                    channel_data = data['CHANNEL']
                    for channel, count in zip(channel_data, counts_data):
                        total_counts_by_channel[channel] += float(count)

                    latitudes = [
                        hdul[1].header.get('V0_LAT'),
                        hdul[1].header.get('V1_LAT'),
                        hdul[1].header.get('V2_LAT'),
                        hdul[1].header.get('V3_LAT')
                    ]
                    longitudes = [
                        hdul[1].header.get('V0_LON'),
                        hdul[1].header.get('V1_LON'),
                        hdul[1].header.get('V2_LON'),
                        hdul[1].header.get('V3_LON')
                    ]
                    min_lat = min(min_lat, *map(float, latitudes))
                    max_lat = max(max_lat, *map(float, latitudes))
                    min_lon = min(min_lon, *map(float, longitudes))
                    max_lon = max(max_lon, *map(float, longitudes))

        summed_counts_list = list(map(float, total_counts_by_channel.values()))
        channels = list(range(len(summed_counts_list)))
        energy_list = [channel * 0.0135 for channel in channels]

        csv_writer.writerow([
            group_start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            group_end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            float(min_lon), float(max_lon), float(min_lat), float(max_lat),
            summed_counts_list, channels, energy_list,
            avg_sat_alt, avg_solarang, avg_phaseang, avg_emisnang
        ])

print("Processing complete. Group data with cumulative counts and averages saved to CSV.")
