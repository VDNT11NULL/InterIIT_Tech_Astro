#feb data
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

def export_stats_to_xml(stats, batch_counts, output_dir):
    """
    Export statistics and batch counts to an XML file in the specified output directory.
    
    Parameters:
    stats (dict): Dictionary containing parameter statistics
    batch_counts (dict): Dictionary containing batch distribution counts
    output_dir (str): Directory where the XML file should be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename based on timestamp
    timestamp = stats.get('file_counts', {}).get('processed_date', 
                                                stats['parameters'].get('start_date_time', 
                                                                      'analysis_results'))
    output_file = os.path.join(output_dir, f"parameter_analysis_{timestamp}.xml")
    
    root = ET.Element("parameter_analysis")
    
    # Add file processing summary
    summary = ET.SubElement(root, "file_summary")
    ET.SubElement(summary, "total_files").text = str(stats['file_counts']['total'])
    ET.SubElement(summary, "processed_files").text = str(stats['file_counts']['processed'])
    ET.SubElement(summary, "error_files").text = str(stats['file_counts']['errors'])
    
    # Add parameter statistics
    parameters = ET.SubElement(root, "parameters")
    for param_name, param_stats in stats['parameters'].items():
        if param_stats:  # Only add parameters with valid statistics
            parameter = ET.SubElement(parameters, "parameter")
            parameter.set("name", param_name)
            
            ET.SubElement(parameter, "count").text = str(param_stats['count'])
            ET.SubElement(parameter, "average").text = f"{param_stats['average']:.6f}"
            ET.SubElement(parameter, "minimum").text = f"{param_stats['min']:.6f}"
            ET.SubElement(parameter, "maximum").text = f"{param_stats['max']:.6f}"
            ET.SubElement(parameter, "range").text = f"{param_stats['range']:.6f}"
    
    # Add batch distribution data
    distributions = ET.SubElement(root, "batch_distributions")
    for param_name, batches in batch_counts.items():
        parameter = ET.SubElement(distributions, "parameter")
        parameter.set("name", param_name)
        
        # Calculate total values in batches
        total_in_batches = sum(batches.values())
        ET.SubElement(parameter, "total_counted").text = str(total_in_batches)
        
        # Add individual batch counts
        batch_list = ET.SubElement(parameter, "batches")
        for batch_name, count in batches.items():
            if count > 0:  # Only include non-empty batches
                batch = ET.SubElement(batch_list, "batch")
                batch.set("name", batch_name)
                batch.text = str(count)
    
    # Create XML tree and write to file with proper formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    
    try:
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"\nStatistics successfully exported to {output_file}")
        return True
    except Exception as e:
        print(f"Error writing XML file: {str(e)}")
        return False

def analyze_and_export(input_dir, output_dir):
    """
    Analyze XML files in the input directory and export results to an XML file in the output directory.
    
    Parameters:
    input_dir (str): Directory containing XML files to analyze
    output_dir (str): Directory where the output XML file should be saved
    """
    # Get statistics and batch counts
    stats = aggregate_parameters(input_dir)
    batch_counts, total_files, processed_files = batch_counter(input_dir)
    
    # Update file counts in stats if needed
    stats['file_counts']['total'] = total_files
    stats['file_counts']['processed'] = processed_files
    stats['file_counts']['errors'] = total_files - processed_files
    
    # Export to XML
    return export_stats_to_xml(stats, batch_counts, output_dir)

if __name__ == "__main__":
    input_directory = "XML_FILES"
    output_directory = "Output"  # Your existing output directory
    analyze_and_export(input_directory, output_directory)
