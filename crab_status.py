import os
import subprocess
import csv
import re
import yaml
import pandas as pd
import sys

def get_crab_info(directory):
    try:
        # Run crab status command
        result = subprocess.run(['crab', 'status', '-d', directory], capture_output=True, text=True, check=True)
        output = result.stdout
        #Add error message of cmsenv and grid_certificate if not initiated already by the user
    except subprocess.CalledProcessError as e:
        output = e.stdout.decode('utf-8')

    # Extract relevant information from the output
    finished_values = re.findall(r'finished\s+(\d+\.\d+)%', output)
    jobs_status = float(finished_values[-1]) if finished_values else '0'
    output_dataset = next((line.split()[2] for line in output.splitlines() if 'Output dataset:' in line), 'N/A')

    return jobs_status, output_dataset

def modify_das_path(das_path):
    parts = das_path.split('/')
    if len(parts) >= 4:
        # Find the index of the first occurrence of "-"
        first_dash_index = parts[2].find("-")
        if first_dash_index != -1:
            parts[2] = parts[2][first_dash_index + 1:]
        substring_to_drop = "_BTV_Run3"
        start_index = parts[2].find(substring_to_drop)
        if start_index != -1:
            parts[2] = parts[2][:start_index]
        modified_path = modified_path = f'/{parts[1]}/{parts[2]}/MINIAODSIM'
        return modified_path
    

def main(base_path, output_path, yaml_path, csv_ext):
    # Specify the name of the CSV file
    csv_file = os.path.join(output_path, f'crab_info_{csv_ext}.csv')

    # Create the header in the consolidated CSV file
    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Dataset', 'Jobs Status', 'DAS Path'])

    # Load YAML data
    with open(yaml_path) as yaml_file:  
        yaml_data = yaml.safe_load(yaml_file)
    # Extract the list from the YAML file
    yaml_list_str = yaml_data['campaign']['datasets']
    yaml_list = [item.strip() for item in yaml_list_str.split('\n')] if isinstance(yaml_list_str, str) else []
    #print(yaml_list)
    # Generate a list of directories in the specified path
    directory_list = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and 'crab' in d]
    data_list = []
    # Loop through the directory list and get crab info for each directory
    for directory in directory_list:
        print(f"Running crab status for directory: {directory}")
        directory_path = os.path.join(base_path, directory)
        jobs_status, output_dataset = get_crab_info(directory_path)
        print(f"Job status: {jobs_status}")

        # Modify the DAS Path
        modified_das_path = modify_das_path(output_dataset)
        data_list.append(modified_das_path)
        # Append the information to the consolidated CSV file
        with open(csv_file, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([modified_das_path, jobs_status, output_dataset])
    print(f'csv file created and saved in the www eos area. Every execution will overwrite the previous csv.: {csv_file}')
    #print(data_list)
    # Find in YAML list that are missing in modified_das_path
    missing_samples = [yaml_value for yaml_value in yaml_list if yaml_value not in data_list]

    # Print missing samples
    if missing_samples:
        for missing_sample in missing_samples:
            print(f"Samples missing in CSV: {missing_sample}")
    else:
        print("You're great! Nothing is missing for production.")
        
if __name__ == "__main__":
    import sys

    # Check if base_path and yaml_path are provided as command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python crab_status.py <crab_dir_path> <crab_yml to compare>")
        sys.exit(1)

    base_path = sys.argv[1]
    csv_ext = os.path.basename(sys.argv[1])
    yaml_path = sys.argv[2]
    output_path = "/eos/user/u/usarkar/www/btvnano_prod/"  # Replace with your desired output path

    main(base_path, output_path,yaml_path,csv_ext)


    