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
import datetime
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from collections import defaultdict
import argparse
import csv


parser = argparse.ArgumentParser(description= "A simple script to setup a markdown notes file with a patients retreived from Canopy.")
parser.add_argument("-v", "--verbose", action="store_true", help="Increase output shell for debugging.")
parser.add_argument("-z", "--zwanger", action="store_true", help="Include Zwanger data in the output.")
args = parser.parse_args()

class patient: #Patient data class
    def __init__(self, patient_id, name=""):
        self.patient_id = patient_id
        self.name = name
        self.DOB = datetime.date(1900, 1, 1)  # Default DOB, replace with actual DOB if available
        self.labs = "True"
        self.quest = "False"
        self.rad = "False"
        self.zwanger = "False"

    def __repr__(self):
        return f"{self.name} (ID: {self.patient_id})"


def debug(message):
    if args.verbose:
        print(f"DEBUG: {message}")

def start():
    print("Starting WRV Prep...")
    with open('wrvprep.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        if args.verbose == True:
            for row in reader:
                print(row)
        patient_data = []
        for row in reader:
            if len(row) < 2:
                print(f"Skipping invalid row: {row}")
                continue
            patient_id= row[1]
            patient_obj = patient(patient_id)
            patient_data.append(patient_obj)
        debug(f"Loaded patient data: \n {patient_data}")
        csvfile.close()
    return patient_data

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
    sleep(2)

def get_patient_name(patient_data): 
    wait = WebDriverWait(driver, 15)
    
    for patient in patient_data:
        print(f"Retrieving name and DOB for patient ID: {patient.patient_id}")
        driver.get(f"https://onecanopy.oakstreethealth.com/#/charts/{patient.patient_id}/labs")
        sleep(3)
        try:
            # Wait for and extract patient full name
            wait.until(EC.presence_of_element_located([By.CLASS_NAME, "patient-full-name"]))
            name_element = driver.find_element(By.CLASS_NAME, "patient-full-name")
            patient.name = name_element.text.strip()
            
            # Wait for and extract patient date of birth
            wait.until(EC.presence_of_element_located([By.CSS_SELECTOR, "[data-cy='patient-date-of-birth']"]))
            dob_element = driver.find_element(By.CSS_SELECTOR, "[data-cy='patient-date-of-birth']")
            dob_text = dob_element.text.strip()
            patient.DOB = datetime.datetime.strptime(dob_text, "%m/%d/%Y").date()
            if "No results found" in driver.page_source:
                print("No labs found.")
                patient.labs = "False"
            print(f"  Name: {patient.name}, DOB: {patient.DOB}, Labs: {patient.labs}")
        except Exception as e:
            print(f"  Error retrieving data for patient {patient.patient_id}: {e}")
            continue
    
    print(f"\nPatient data retrieved: {patient_data}")


if __name__ == "__main__":
    ptdata = start()
    for p in ptdata:
        print(p.patient_id)
    driver = webdriver.Chrome()
    login()
    print(ptdata)
    get_patient_name(ptdata)
    with open('wrvprep_output.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Patient ID', 'Name', 'DOB', 'Labs'])
        for patient in ptdata:
            writer.writerow([patient.patient_id, patient.name, patient.DOB.strftime("%m/%d/%Y"), patient.labs])