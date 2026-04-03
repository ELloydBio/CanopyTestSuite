import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
from time import sleep
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui as pya
import os
import labs
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from collections import defaultdict

# Section 1: Config
# Define objects and functions and settings.

debug = False # Enables verbose output for debugging purposes. Set to False for production use.
testing = False # Enables custom chrome options for testing. Currently not working. Does not appear to affect normal functionality.
if testing == True: # Experimenting with chrome options to enable pesistence and headless PDF downloading. Currently NOT working.
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.getcwd(), # Set download directory to current working directory
        "download.prompt_for_download": False, # Prevents download pop-up
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
else:
    driver = webdriver.Chrome()

class patient: #Patient data class
    def __init__(self, patient_id, name="", time=""):
        self.patient_id = patient_id
        self.name = name
        self.time = time
        self.labs = []
        self.note = ""
    
    def __repr__(self):
        return f"{self.time} {self.name} (ID: {self.patient_id})"
    
class LabResult: #Lab data class
    def __init__(self, name, shortened_name, value, date):
        self.name = name
        self.shortened_name = shortened_name
        self.value = value
        self.date = date

    def __repr__(self):
        return f"Lab(Name='{self.shortened_name}', Value={self.value}, Date={self.date})"

    
def login(): #Initialize Canopy. Required once each time the script is run. User must manually log in. 
    driver.get("https://onecanopy.oakstreethealth.com/#/tracker")  # Opens canopy tracker page
    sleep(3)  # Wait for page to load
    try:
        WebDriverWait(driver, 60).until(
            EC.title_contains("Canopy") # Replace with a relevant title or element on the logged-in page
        )
        print("Login successful!")
    except Exception as e:
        print(f"Login failed: {e}")
        raise Exception("Login failed. Please check your credentials or the page structure.")
    sleep(5)
    
def get_schedule(provider): #Scrapes appointment data from the main tracker page. Returns raw text data for parsing.
    try:
        TO = 10  # int timeout in seconds, higher for debugging lower for production
        # Gets raw schedule data from the main canopy tracker page
        schedule_data = ""
        try:
            driver.get("https://onecanopy.oakstreethealth.com/#/tracker")
            WebDriverWait(driver, TO).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div/main/div/div/div[2]/header/div/button[1]"))
            )

            sleep(5) #Allow time for user input

            button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/main/div/div/div[2]/header/div/button[1]")
            button.click()

            WebDriverWait(driver, TO).until(
                EC.presence_of_element_located((By.ID, "provider-filter-autocomplete"))
            )
            provider_field = driver.find_element(By.ID, "provider-filter-autocomplete")
            provider_field.send_keys(provider)  # Set the provider field
            sleep(3)  # Wait for the input to be processed
            #suboptimal, better to wait for provider name to appear in the dropdown
            keyboard.send(keyboard.KEY_DOWN)
            keyboard.send('enter')  # Simulate pressing Enter to apply the filter

            WebDriverWait(driver, TO).until(
                EC.presence_of_element_located((By.CLASS_NAME, "schedule-view-default-tr"))
            )
            schedule_data = driver.find_element(By.TAG_NAME, "body").text
            print("Data retreived from canopy")
        except Exception as e:
            print(f"Error getting schedule data: {e}")
        return schedule_data
    except Exception as e:
        print(f"Error getting schedule data: {e}")
        return None

def parse_appointment_data(data_string):
    """
    Parses a multiline string containing appointment information
    and extracts time, name (last two words), and ID.

    Args:
        data_string (str): The raw text data of appointments.

    Returns:
        list of dict: A list where each dictionary represents an appointment
                      with 'Time', 'Name', and 'ID' keys.
    """
    pt_list = []
    # Regular expression to find blocks of appointment data based on time
    appointment_blocks = re.split(r'(\d{1,2}:\d{2}\s(?:AM|PM))', data_string)


    for i in range(1, len(appointment_blocks), 2):
        time_str = appointment_blocks[i].strip()
        content_str = appointment_blocks[i+1].strip()

        # Regular expression to find the name and ID within the content block.
        # It looks for any characters (including newlines and leading/trailing spaces around the ID)
        # that are not part of a "time" pattern, followed by a name, then the ID in parentheses.
        name_id_match = re.search(r'([\w\s\.]+?)\s*\((\d+)\)', content_str, re.DOTALL)

        if name_id_match:
            full_extracted_name = name_id_match.group(1).strip().replace('\n', ' ')

            # --- NEW LOGIC TO GET ONLY THE LAST TWO WORDS OF THE NAME ---
            # Split the name by spaces and filter out empty strings
            name_parts = [part for part in full_extracted_name.split(' ') if part]

            # Special handling for "Pooja Jaisingh..." if it's at the beginning of the extracted name
            if name_parts and name_parts[0] == 'Pooja' and len(name_parts) > 1 and name_parts[1].startswith('Jaisingh'):
                # If "Pooja Jaisingh..." is detected, we'll try to find the actual patient name after it.
                # This is a heuristic based on your provided data structure.
                # We'll skip "Pooja Jaisingh..." and then take the last two words.
                # Find the index where the actual patient name likely starts
                try:
                    jaisingh_index = name_parts.index('Jaisingh...') # Adjust if 'Jaisingh' only
                    if jaisingh_index + 1 < len(name_parts):
                        name_parts = name_parts[jaisingh_index + 1:] # Slice from after "Jaisingh..."
                    else:
                        name_parts = [] # No patient name found after "Pooja Jaisingh..."
                except ValueError:
                    # 'Jaisingh...' not found, proceed with original name_parts
                    pass

            # If after cleanup, there are still parts, take the last two
            if len(name_parts) >= 2:
                final_name = ' '.join(name_parts[-2:])
            elif len(name_parts) == 1:
                final_name = name_parts[0]
            else:
                final_name = "" # No valid name parts found

            # Clean up the name for common suffixes/ellipses if they are the last "words"
            # This is done *after* taking the last two words to ensure they aren't incorrectly included
            if final_name.lower().endswith('sr'):
                final_name = final_name[:-2].strip() + ' SR'
            if final_name.endswith('...'):
                final_name = final_name[:-3].strip()

            patient_id = name_id_match.group(2).strip()

            pt = patient(patient_id, final_name, time_str)
            pt_list.append(pt)
    return pt_list
    


def get_most_recent_labs(patient_id):
    """
    Scrapes lab results. Scans columns left-to-right. 
    Returns the first non-empty value found and attempts to get the date 
    from the cell's tooltip, ignoring table headers.
    """
    
    url = f"https://onecanopy.oakstreethealth.com/#/charts/{patient_id}/labs"
    print(f"Navigating to: {url}")
    driver.get(url)

    try:
        # 1. Wait for the main container to ensure the view has loaded.
        # Waiting for 'tr' can be flaky if the table is empty or reloading.
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".labs-card"))
        )
        # Small buffer to allow the table rows to settle after the container appears
        sleep(2) 
    except Exception as e:
        print(f"Failed to load patient labs page for {patient_id}: {e}")
        return []

    lab_objects = []

    # 2. Find Data Rows
    # We use a loop with a fresh find inside to handle potential DOM updates (Staleness)
    try:
        rows = driver.find_elements(By.XPATH, "//tr[contains(@data-cy, 'labs-data-row')]")
    except Exception:
        rows = []

    if not rows:
        print(f"No lab rows found for {patient_id}")
        return []

    print(f"Found {len(rows)} lab rows. Processing...")

    for row in rows:
        try:
            # --- NAME EXTRACTION (Column 0) ---
            # We re-find the element to avoid StaleElementReferenceException
            name_element = row.find_element(By.XPATH, "./td[1]//span")
            full_name = name_element.text.strip()
            
            # Cleanup name: Remove units inside () and split by comma
            short_name = re.sub(r'\(.*?\)', '', full_name).split(',')[0].strip()

            # --- VALUE & DATE SEARCH (Scan all columns) ---
            cells = row.find_elements(By.TAG_NAME, "td")
            
            found_value = None
            found_date = None

            # Skip index 0 (Name column). Check columns 1, 2, 3...
            for i in range(1, len(cells)):
                cell_text = cells[i].text.strip()
                
                # If we find a value, this is the "Most Recent" available for this row
                if cell_text:
                    found_value = cell_text
                    
                    # --- DATE STRATEGY (TOOLTIP ONLY) ---
                    # Instead of checking headers, we look for a tooltip on this specific cell
                    try:
                        # Value is usually wrapped in a <span> or <div> with aria-describedby
                        # We try to find that child element
                        child_elements = cells[i].find_elements(By.XPATH, ".//*[@aria-describedby]")
                        
                        if child_elements:
                            tooltip_id = child_elements[0].get_attribute("aria-describedby")
                            
                            if tooltip_id:
                                # Tooltips are often at the bottom of the DOM, hidden
                                tooltip_elem = driver.find_element(By.ID, tooltip_id)
                                tooltip_text = tooltip_elem.get_attribute("textContent")
                                
                                # Regex looks for date pattern: (MM/DD/YYYY)
                                date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", tooltip_text)
                                if date_match:
                                    found_date = date_match.group(1)
                    except (NoSuchElementException, NoSuchElementException):
                        # If we can't find the tooltip date, we still keep the value
                        pass

                    # We found the most recent value, stop checking older columns
                    break 

            # Only create object if we actually found a value
            if found_value:
                lab_obj = LabResult(
                    name=full_name,
                    shortened_name=short_name,
                    value=found_value,
                    date=found_date
                )
                lab_objects.append(lab_obj)

        except NoSuchElementException:
            # If a row updates while we are reading it, we skip it to prevent crash
            print("Row became stale during processing, skipping...")
            continue
        except Exception as e:
            # Catch other errors but keep going
            # print(f"Error processing row: {e}") 
            continue

    print(f"Successfully scraped {len(lab_objects)} labs.")
    return lab_objects

def format_labs_to_panels(lab_objects):
    """
    Takes a list of LabResult objects and formats them into grouped, 
    human-readable text panels sorted by date.
    """
    
    # --- 1. CONFIGURATION ---
    # Map specific text found in LabResult.name to a clean output label.
    # Order matters: more specific matches should be higher if there's overlap.
    NAME_MAPPINGS = {
        'Cholesterol, Total': 'Chol',
        'Triglycerides': 'TGC',
        'HDL': 'HDL',
        'LDL': 'LDL',
        'Sodium': 'Na',
        'Potassium': 'K',
        'Glucose': 'Glu',
        'Creatinine': 'Creat',
        'eGFR': 'GFR',
        'WBC': 'WBC',
        'Hemoglobin': 'HGB', # Watch out for 'Hemoglobin A1c' matching this
        'Hematocrit': 'HCT',
        'PLATELET': 'Plts',
        'MCV': 'MCV',
        'Hemoglobin A1c': 'A1c',
        'TSH': 'TSH',
        'PSA': 'PSA',
        'Vitamin D': 'Vit D',
        'AST - Aspartate Aminotransferase': 'AST',
        'ALT - Alanine Aminotransferase': 'ALT',
        'Alkaline Phosphatase': 'Alk Phos',
    }

    # Define what constitutes a "Panel" and the order of fields
    PANEL_DEFINITIONS = {
        "Lipid Panel": ["Chol", "HDL", "LDL", "TGC"],
        "BMP": ["Na", "K", "Glu"],
        "Kidney function tests": ["Creat", "GFR"],
        "CBC": ["WBC", "HGB", "MCV", "Plts"],
        "Diabetes labs": ["A1c"],
        "Thyroid labs": ["TSH"],
        "LFTs": ["AST", "ALT", "Alk Phos"],
        "PSA": ["PSA"],
        "Other": ["Vit D"]
    }

    # --- 2. GROUPING DATA ---
    # Structure: data_by_date['11/13/2025']['Na'] = "138.0"
    data_by_date = defaultdict(dict)

    for lab in lab_objects:
        # Determine the label
        label = None
        #Check for special cases first
        #i.e. Special check for A1c to prevent it matching generic "Hemoglobin"
        if "Hemoglobin A1c" in lab.name:
            label = "A1c"
        elif "BUN/" in lab.name:
            label = "BUN/Cr ratio"
        elif "Albumin/" in lab.name:
            label = "Alb/Cr ratio"
        elif "urine" in lab.name or ", Ur" in lab.name or "Urine" in lab.name:
            for key, mapped_label in NAME_MAPPINGS.items():
                if key in lab.name:
                    label = mapped_label + " (urine)"
                    break
        else:
            for key, mapped_label in NAME_MAPPINGS.items():
                if key in lab.name:
                    label = mapped_label
                    break
        
        if label and lab.date:
            data_by_date[lab.date][label] = lab.value

    # --- 3. BUILDING OUTPUT ---
    output_lines = []

    # Sort dates descending (newest first)
    sorted_dates = sorted(data_by_date.keys(), reverse=True)

    for date in sorted_dates:
        labs_for_date = data_by_date[date]
        
        # We track which keys we have used to avoid duplicates if you have 'Misc' handling
        used_keys = set()

        for panel_name, fields in PANEL_DEFINITIONS.items():
            # Find which fields for this panel actually exist for this date
            found_values = []
            for field in fields:
                if field in labs_for_date:
                    found_values.append(f"{field} {labs_for_date[field]}")
                    used_keys.add(field)
            
            # Only add the line if we found at least one value for this panel
            if found_values:
                # Format: "- Panel Name (Date): Val 1, Val 2..."
                line = f"\t\t- {panel_name} ({date}): " + ", ".join(found_values)
                output_lines.append(line)

    return "\n".join(output_lines)

def get_last_note(patient_id):
    url = f"https://onecanopy.oakstreethealth.com/#/charts/{patient_id}/documents"
    driver.get(url)
    sleep(3)  # Wait for page to load
    try:
        WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.TAG_NAME, "tr"))    
    )
    except Exception as e:
        print(f"Failed to load patient documents page for {patient_id}: {e}")
        return ""
    rows = driver.find_elements(By.TAG_NAME, "tr")
    pdf_url = None
    for row in rows:
        try:
            # Get all text from the row at once
            row_content = row.text
            
            # Search for your keywords anywhere in the row string
            if "History and Physical" in row_content or "Progress Note" in row_content:
                # Find all cells in THIS row
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 3:
                    # Capture the date before clicking
                    date = cells[0].text
                    
                    # Click the cell that contains the document link (usually cells[2])
                    cells[2].click()
                    sleep(2)  # Wait for document to load
                    
                    iframe_element = driver.find_element(By.TAG_NAME, 'iframe')
                    pdf_url = iframe_element.get_attribute("src")
                    print(f"Found PDF URL: {pdf_url} (Date: {date})")
                    break # Stop searching once we find the first match
        except Exception as e:
            print(f"Error processing a row for patient {patient_id}: {e}")
            continue
    try:
            if pdf_url: #Logic to extract text from PDF via clipboard
                driver.get(pdf_url)
                sleep(2)  # Wait for PDF to load
                pya.click(x=400, y=300)  # Click to focus on the PDF viewer
                sleep(0.5)  # Wait for focus
                keyboard.press_and_release('ctrl+a')
                sleep(0.5)  # Wait for selection to complete
                keyboard.press('ctrl+c')
                sleep(0.5)  # Wait for clipboard to update
                keyboard.release('ctrl+c')
                sleep(0.5)
                pdf_text = pyperclip.paste()
                formatted_text = "\t\t" + pdf_text.replace("\n", "\n\t\t")
                print(f"Extracted PDF text for patient {patient_id}:\n{pdf_text[:150]}\n")
                return formatted_text 
            else:
                print(f"No matching document found for patient {patient_id}.")
                return ""
    except Exception as e:
        print(f"Error extracting text from PDF for patient {patient_id}: {e}")
        return ""

if __name__ == "__main__":
    provider = tk.simpledialog.askstring("Input", "Enter provider name (e.g. 'Smith J'):")
    login()
    schedule_data = get_schedule(provider)
    pts = parse_appointment_data(schedule_data)
    debug = True
    paste_data = ""
    for pt in pts:
        labs = get_most_recent_labs(pt.patient_id)
        if debug == True:
            print(labs)
        labs_text = format_labs_to_panels(labs)
        pt.labs = labs_text
        pt.note = get_last_note(pt.patient_id)
        if debug == True:
            print(f"labs_text: \n{labs_text}")
        paste_data += "- [ ] " + pt.__repr__() + "\n\t- [ ] labs \n"
        if labs_text:
            paste_data += labs_text + "\n"
        if pt.note:
            paste_data += "\t- [ ] Note:\n" + pt.note + "\n\n"
    pyperclip.copy(paste_data)
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(paste_data)
    print("Final clipboard data:\n" + paste_data)