#only for feb data

import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

def parse_xml_file(file_path):
    """Parse an XML file and extract specific parameters as a dictionary."""
    params = {}
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Define namespace map
        ns = {'isda': 'https://isda.issdc.gov.in/pds4/isda/v1'}

        # Extract time coordinates
        time_coords = root.find('.//Time_Coordinates')
        if time_coords is not None:
            params['start_date_time'] = time_coords.findtext('start_date_time')
            params['stop_date_time'] = time_coords.findtext('stop_date_time')

        # Extract coordinates using proper namespace
        coord_paths = {
            'upper_left_latitude': './/isda:System_Level_Coordinates/isda:upper_left_latitude',
            'upper_left_longitude': './/isda:System_Level_Coordinates/isda:upper_left_longitude',
            'upper_right_latitude': './/isda:System_Level_Coordinates/isda:upper_right_latitude',
            'upper_right_longitude': './/isda:System_Level_Coordinates/isda:upper_right_longitude',
            'lower_left_latitude': './/isda:System_Level_Coordinates/isda:lower_left_latitude',
            'lower_left_longitude': './/isda:System_Level_Coordinates/isda:lower_left_longitude',
            'lower_right_latitude': './/isda:System_Level_Coordinates/isda:lower_right_latitude',
            'lower_right_longitude': './/isda:System_Level_Coordinates/isda:lower_right_longitude'
        }

        for param, path in coord_paths.items():
            element = root.find(path, ns)
            if element is not None:
                value = element.text
                params[param] = value

    except ET.ParseError as e:
        print(f"Error parsing {file_path}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error processing {file_path}: {str(e)}")
        return None
    
    # Convert extracted text values to float where possible
    for key, value in params.items():
        try:
            if value is not None:
                value = value.split()[0] if isinstance(value, str) else value
                params[key] = float(value)
            else:
                params[key] = None
        except (ValueError, TypeError) as e:
            print(f"Error converting value for {key} in {file_path}: {str(e)}")
            params[key] = None
    
    return params

def get_parameter_ranges(directory):
    """Calculate min and max values for each parameter across all XML files."""
    param_ranges = defaultdict(lambda: {'min': float('inf'), 'max': float('-inf')})
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            file_path = os.path.join(directory, file_name)
            params = parse_xml_file(file_path)
            
            if params:
                for param, value in params.items():
                    if value is not None and isinstance(value, (int, float)):
                        param_ranges[param]['min'] = min(param_ranges[param]['min'], value)
                        param_ranges[param]['max'] = max(param_ranges[param]['max'], value)
    
    # Remove parameters that didn't have any valid values
    return {k: v for k, v in param_ranges.items() 
            if v['min'] != float('inf') and v['max'] != float('-inf')}

def initialize_batch_counts(param_ranges):
    """Initialize batch counts dictionary with dynamic ranges based on actual min/max values."""
    batch_counts = {}
    
    for param, ranges in param_ranges.items():
        min_val = ranges['min']
        max_val = ranges['max']
        batch_size = (max_val - min_val) / 10  # Divide range into 10 equal intervals
        
        batch_counts[param] = {}
        for i in range(10):
            start = min_val + (i * batch_size)
            end = min_val + ((i + 1) * batch_size)
            # Ensure the range values are properly formatted
            batch_name = f'Batch_{i+1}({start:.3f},{end:.3f})'
            batch_counts[param][batch_name] = 0
            
    return batch_counts

def assign_to_batch(value, param, batch_counts, param_ranges):
    """Assign a value to the correct batch for a parameter and increment the count."""
    min_val = param_ranges[param]['min']
    max_val = param_ranges[param]['max']
    batch_size = (max_val - min_val) / 10
    
    if min_val <= value <= max_val:
        batch_index = min(9, int((value - min_val) // batch_size))
        start = min_val + (batch_index * batch_size)
        end = min_val + ((batch_index + 1) * batch_size)
        # Ensure consistent batch name format
        batch_name = f'Batch_{batch_index + 1}({start:.3f},{end:.3f})'
        batch_counts[param][batch_name] += 1
    else:
        # Handle values outside the range
        if value < min_val:
            overflow_batch = f'Underflow_Batch (<{min_val:.3f})'
        else:
            overflow_batch = f'Overflow_Batch (>{max_val:.3f})'
            
        if overflow_batch not in batch_counts[param]:
            batch_counts[param][overflow_batch] = 0
        batch_counts[param][overflow_batch] += 1

def aggregate_parameters(directory):
    """Aggregate parameters across all XML files in a directory and calculate statistics."""
    param_values = defaultdict(list)
    total_files = 0
    processed_files = 0
    error_files = 0
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            total_files += 1
            file_path = os.path.join(directory, file_name)
            params = parse_xml_file(file_path)
            
            if params:
                processed_files += 1
                for key, value in params.items():
                    if value is not None:
                        param_values[key].append(value)
            else:
                error_files += 1
    
    statistics = {
        'file_counts': {
            'total': total_files,
            'processed': processed_files,
            'errors': error_files
        },
        'parameters': {}
    }
    
    for key, values in param_values.items():
        if values:
            statistics['parameters'][key] = {
                'count': len(values),
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values)
            }
        else:
            statistics['parameters'][key] = None
    
    return statistics

def batch_counter(directory):
    """Count occurrences of parameter values in dynamically determined ranges."""
    # First get the actual ranges for each parameter
    param_ranges = get_parameter_ranges(directory)
    
    # Initialize batch counts based on actual ranges
    batch_counts = initialize_batch_counts(param_ranges)
    
    total_files = 0
    processed_files = 0
    
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            total_files += 1
            file_path = os.path.join(directory, file_name)
            params = parse_xml_file(file_path)
            
            if params:
                processed_files += 1
                for param, value in params.items():
                    if value is not None and param in batch_counts:
                        assign_to_batch(value, param, batch_counts, param_ranges)
    
    return batch_counts, total_files, processed_files

# Main execution
directory = 'XML_FILES'
stats = aggregate_parameters(directory)
batch_counts, total_files, processed_files = batch_counter(directory)

# Display the file processing summary
print(f"\nFile Processing Summary:")
print(f"Total XML files found: {total_files}")
print(f"Successfully processed files: {processed_files}")
print(f"Files with errors: {total_files - processed_files}")

# Display the statistics
print("\nParameter Statistics:")
for param, stat in stats['parameters'].items():
    if stat:
        print(f"\n{param}:")
        print(f"  Count: {stat['count']} out of {total_files} files")
        print(f"  Average: {stat['average']:.2f}")
        print(f"  Min: {stat['min']}")
        print(f"  Max: {stat['max']}")
        print(f"  Range: {stat['range']}")
    else:
        print(f"\n{param}: No valid values found")

# Display the batch counts for each parameter
print("\nBatch Distribution:")
for param, batches in batch_counts.items():
    print(f"\nParameter: {param}")
    total_in_batches = sum(batches.values())
    print(f"Total values counted: {total_in_batches} out of {total_files} files")
    for batch_name, count in batches.items():
        if count > 0:  # Only show non-empty batches
            print(f"  {batch_name}: Count = {count}")
