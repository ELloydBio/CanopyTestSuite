import re
from tkinter import simpledialog
from datetime import datetime
import pyperclip 

#KNOWN ISSUE, ONLY CORRECTLY PULLS DATE FROM LIPID PANEL, MAY BE INCORRECT FOR OTHER LAB TYPES


def get_lab_results(raw_data, target_date):
    """
    Parses raw text data to extract lipid panel results for a specific date.
    """
    # Split data into lines
    lines = raw_data.strip().split('\n')
    
    # Configuration: Map the text found in the row to the label you want in output
    # The order here determines the search priority
    lab_mappings = {
        'Cholesterol, Total': 'Chol',
        'HDL (': 'HDL',
        'LDL (': 'LDL',
        'Triglycerides': 'TGC',
        'Sodium': 'Na',
        'Potassium': 'K',
        'Glucose': 'Glucose',
        'Creatinine': 'Creat',
        'eGFR': 'GFR',
        'WBC': 'WBC',
        'Hemoglobin': 'HGB',
        'MCV': 'MCV',
        'PLATELET': 'Plts',
        'Hemoglobin A1c': 'A1c',
        'Vitamin D,': 'Vit D'

    }
    
    extracted_values = {}
    target_index = -1
    
    # Step 1: Find the header row to determine the column index of the date
    for line in lines:
        if target_date in line and "Lab Type" in line:
            # Split by tab usually works best for copy-pasted web tables
            headers = line.split('\t')
            
            # If split by tab failed (length 1), try splitting by multiple spaces
            if len(headers) == 1:
                headers = re.split(r'\s{2,}', line)
            
            try:
                # Find which column number holds our date
                target_index = headers.index(target_date)
            except ValueError:
                return f"Error: Date {target_date} not found in header."
            break
    
    if target_index == -1:
        return "Error: Could not find a header row with the target date."

    # Step 2: Extract data from rows based on the column index
    for line in lines:
        for key, output_label in lab_mappings.items():
            # Check if this line is one of our target labs (and not already found)
            if key in line and output_label not in extracted_values:
                
                # Split the line exactly as we did the header
                parts = line.split('\t')
                if len(parts) == 1:
                    parts = re.split(r'\s{2,}', line)
                
                # Ensure the row has enough columns to reach our target index
                if len(parts) > target_index:
                    val = parts[target_index].strip()
                    
                    # Clean the value: remove '.0' and ensure it's numeric
                    # This turns '90.0' into '90'
                    match = re.search(r'\d+', val)
                    if match:
                        extracted_values[output_label] = match.group(0)

    # Step 3: Format the output
    # Format date to remove leading zero if desired (03/11 -> 3/11)
    formatted_date = target_date.lstrip('0')
    
    try:
        output_string = (
            f"- Lipid panel ({formatted_date}): "
            f"Chol {extracted_values.get('Chol', 'N/A')}, "
            f"HDL {extracted_values.get('HDL', 'N/A')}, "
            f"LDL {extracted_values.get('LDL', 'N/A')}, "
            f"TGC {extracted_values.get('TGC', 'N/A')}\n"
            f"- Basic Metabolic Panel ({formatted_date}): "
            f"Na {extracted_values.get('Na', 'N/A')}, "
            f"K {extracted_values.get('K', 'N/A')}, "
            f"Glucose {extracted_values.get('Glucose', 'N/A')}, "
            f"Creat {extracted_values.get('Creat', 'N/A')}, "
            f"GFR {extracted_values.get('GFR', 'N/A')}\n"
            f"- CBC ({formatted_date}): "
            f"WBC {extracted_values.get('WBC', 'N/A')}, "
            f"HGB {extracted_values.get('HGB', 'N/A')}, "
            f"MCV {extracted_values.get('MCV', 'N/A')}, "
            f"Plts {extracted_values.get('Plts', 'N/A')}\n"
            f"- HbA1c ({formatted_date}): " 
            f"A1c {extracted_values.get('A1c', 'N/A')}\n"
            f"- Vitamin D ({formatted_date}): "
            f"Vit D {extracted_values.get('Vit D', 'N/A')}"

        )
        return output_string
    except Exception as e:
        return f"Error building output: {e}"

def find_latest_valid_date(raw_data):
    """
    Scans the raw data to find the most recent date column that contains 
    at least one non-empty lab value (Cholesterol or HDL).
    """
    lines = raw_data.strip().split('\n')
    
    # 1. Find the header line and extract all date strings
    header_line = ""
    for line in lines:
        if "Lab Type" in line:
            header_line = line
            break
    
    if not header_line:
        return None

    # Split the header line (assuming tab or large space separation)
    headers = header_line.split('\t')
    if len(headers) == 1:
        headers = re.split(r'\s{2,}', header_line)

    # Regex to find dates in MM/DD/YYYY format
    date_pattern = r'\d{2}/\d{2}/\d{4}'
    date_columns = {} # Stores {date_string: column_index}

    # 2. Map dates to their column indices
    for i, header_part in enumerate(headers):
        match = re.search(date_pattern, header_part)
        if match:
            date_columns[match.group(0)] = i

    if not date_columns:
        return None

    # 3. Check for data presence for each date, tracking the latest valid one
    latest_valid_date_obj = datetime.min
    latest_valid_date_string = None
    
    # Lines that contain the data we want to check (Cholesterol and HDL)
    data_lines = [line for line in lines if 'Cholesterol, Total' in line or 'HDL (' in line]
    
    # Iterate through all found dates
    for date_str, col_index in date_columns.items():
        has_valid_data = False
        
        # Check if any data line has a non-empty value in this date's column
        for data_line in data_lines:
            
            # Split the data line exactly as we did the header
            parts = data_line.split('\t')
            if len(parts) == 1:
                parts = re.split(r'\s{2,}', data_line)
            
            # Check if the column exists and the value is not just whitespace
            if len(parts) > col_index and parts[col_index].strip():
                has_valid_data = True
                break # Found one valid lab result for this date, so it's a "valid" date column

        # If data was found, compare it to the current latest valid date
        if has_valid_data:
            try:
                current_date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                
                if current_date_obj > latest_valid_date_obj:
                    latest_valid_date_obj = current_date_obj
                    latest_valid_date_string = date_str
            except ValueError:
                # Skip if the date string is malformed
                continue
                
    return latest_valid_date_string

def format_labs():
    raw_text_data = pyperclip.paste()
    target_date = find_latest_valid_date(raw_text_data)
    result = get_lab_results(raw_text_data, target_date)
    pyperclip.copy(result)
    print(result)

if __name__ == "__main__":
    raw_text_data = simpledialog.askstring("Input", "Please enter the labs data:")
    target_date = find_latest_valid_date(raw_text_data)
    result = get_lab_results(raw_text_data, target_date)
    pyperclip.copy(result)
    print(result)