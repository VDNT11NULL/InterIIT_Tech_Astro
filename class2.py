import os
from astropy.io import fits
import numpy as np
from datetime import datetime
from pathlib import Path

def convert_time_str_format(time_str):
    """Convert time string from YYYYMMDDTHHMMSSMMM to YYYY-MM-DDTHH:MM:SS.MMM format."""
    return f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]}T{time_str[9:11]}:{time_str[11:13]}:{time_str[13:15]}.{time_str[15:]}"

def utc_to_seconds(utc_time):
    """Convert UTC time to seconds since epoch (1970-01-01)."""
    utc_datetime = datetime.strptime(utc_time, '%Y-%m-%dT%H:%M:%S.%f')
    return int(utc_datetime.timestamp())

def write_summed_fits(output_filename, summed_data, input_filename, expotime, starttime, endtime, spice_values):
    """Write summed data to a FITS file with metadata headers."""
    hdu = fits.PrimaryHDU()
    hdu.header['DATE'] = datetime.utcnow().isoformat()
    hdu.header['EXPOSURE'] = expotime
    hdu.header['STARTIME'] = starttime
    hdu.header['ENDTIME'] = endtime
    hdu.header['TELESCOP'] = 'CHANDRAYAAN-2'
    hdu.header['INSTRUME'] = 'CLASS'
    hdu.header['PROGRAM'] = 'CLASS_add_scds_time'

    # SPICE parameters (example placeholders)
    for key, value in spice_values.items():
        hdu.header[key] = value

    # Create Binary Table
    col1 = fits.Column(name='CHANNEL', array=np.arange(len(summed_data)), format='J')
    col2 = fits.Column(name='COUNTS', array=summed_data, format='E')
    hdu_bt = fits.BinTableHDU.from_columns([col1, col2])
    
    hdul = fits.HDUList([hdu, hdu_bt])
    hdul.writeto(output_filename, overwrite=True)

def add_l1_files_time(input_dir, start_utc, end_utc, output_dir):
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert input start and end UTC to seconds
    start_utc_secs = utc_to_seconds(start_utc)
    end_utc_secs = utc_to_seconds(end_utc)
    
    # Read input files and select based on timestamp
    file_list = sorted(Path(input_dir).glob("*.fits"))
    summed_data = np.zeros(2048, dtype=np.float64)  # Array to store summed data
    
    selected_files = []
    for file in file_list:
        filename = file.name
        start_time_str = filename[11:29]
        end_time_str = filename[30:48]
        
        start_time_secs = utc_to_seconds(convert_time_str_format(start_time_str))
        end_time_secs = utc_to_seconds(convert_time_str_format(end_time_str))

        if start_time_secs >= start_utc_secs and end_time_secs <= end_utc_secs:
            with fits.open(file) as hdul:
                data = hdul[1].data['COUNTS']  # Assuming the counts are stored in the 1st extension
                summed_data += data
            selected_files.append(filename)
    
    # Calculate mean SPICE values (placeholders)
    spice_values = {
        'SAT_ALT': 100.0,  # Example values
        'SOLARANG': 10.0,
        'PHASEANG': 20.0,
        'EMISNANG': 30.0,
    }
    
    # Prepare output filename (remove colons from timestamps)
    clean_start = start_utc.replace(":", "-")
    clean_end = end_utc.replace(":", "-")
    output_filename = output_path / f"added_{clean_start}_{clean_end}.fits"
    
    # Write the output FITS file
    write_summed_fits(
        output_filename=output_filename,
        summed_data=summed_data,
        input_filename=", ".join(selected_files),
        expotime=(end_utc_secs - start_utc_secs),
        starttime=start_utc,
        endtime=end_utc,
        spice_values=spice_values
    )
    print(f"Summed FITS file written to {output_filename}")

# Usage example
input_dir = 'FITS_FILES'
output_dir = r'C:/Users/chand/OneDrive/Desktop/New/Inter_IIT/Output/L1_ADDED_FILES_TIME'
start_utc = '2020-02-01T00:00:00.114'
end_utc = '2020-02-01T00:45:12.114'
add_l1_files_time(input_dir, start_utc, end_utc, output_dir)
