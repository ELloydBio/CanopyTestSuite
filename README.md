# Canopy Test Suite

A Python-based automation tool for scraping and processing patient data from Oak Street Health's Canopy platform. This suite extracts patient schedules, lab results, and clinical notes, then formats them into a structured markdown checklist for efficient medical review workflows.

# Important
This documentation was automatically generated. Although it has been proofread, installation instructions have not been tested. This script is designed to work with internal company tools and cannot be tested on outside systems. It is available here to document the final design of the script and will be deprecated when Canopy is discontinued.

## Features

- **Manual Login**: Secure authentication to Canopy platform
- **Schedule Extraction**: Scrapes provider schedules and parses patient appointment data
- **Lab Results Processing**: Extracts and formats lab results from patient charts
- **Clinical Note Extraction**: Downloads and processes PDF clinical notes
- **Structured Output**: Generates markdown-formatted checklists with patient information, labs, and notes
- **Clipboard Integration**: Automatically copies formatted data to clipboard for easy pasting

## Prerequisites

### System Requirements
- Google Chrome browser
- Python 3.7+
- Windows operating system 
    - May function on Linux and Mac with filesystem tweaks but this is not tested.

### Python Dependencies
```
selenium
pyautogui
keyboard
pyperclip
tkinter (usually included with Python)
```

## Installation

1. **Clone or download** the project files to your local machine

2. **Install Python dependencies**:
   ```bash
   pip install selenium pyautogui keyboard pyperclip
   ```

3. **Install Chrome WebDriver**:
   - Download ChromeDriver from [https://chromedriver.chromium.org/](https://chromedriver.chromium.org/)
   - Ensure the version matches your Chrome browser version
   - Place chromedriver.exe in your system PATH or in the project directory

## Usage

### Main Workflow (MultiInit.py)

1. **Run the main script**:
   ```bash
   python MultiInit.py
   ```

2. **Enter provider name** when prompted (e.g., "Smith", "Doe", etc.)

3. **Manual login required**: The script will open Chrome and navigate to Canopy. You must manually log in with your credentials.

4. **Automated processing**: Once logged in, the script will:
   - Extract the provider's schedule
   - Parse patient appointments
   - Scrape lab results for each patient
   - Extract clinical notes from PDFs
   - Format everything into a markdown checklist

5. **Output**: The formatted data is automatically copied to your clipboard and saved to `output.md`

## Output Format

The script generates a markdown checklist with the following structure:

```
- [ ] 2:00 PM John Doe (ID: 12345)
    - [ ] labs
            - Lipid Panel (date of test...): Chol 180, HDL 45, LDL 120, TGC 150
            - BMP (date of test...): Na 140, K 4.2, Glu 95
    - [ ] Note:
            [Extracted PDF text content]
```
 Displayed testing values are strictly fictionalized

## Misc.

### Security & Compliance
- This tool requires manual login to maintain security.
- No data is transmitted to any outside servers.
- User *must* ensure compliance with HIPAA and institutional policies. Handle patient data appropriately and securely

### Known Issues
- PDF text extraction relies on clipboard operations and may require specific PDF viewer behavior
- Due to issues with internal software handling, this software manually uses mouse and keyboard to do manual inputs. This limits its ability to run in the background. It cannot run headlessly.
- Some lab date extraction may be inconsistent across different lab types

### Other requiremnts
- Requires active internet connection for Canopy access
- Chrome browser must be available and up-to-date

### Debug Mode
Enable debug mode by setting `debug = True` to see detailed processing information.

## Legal

This project is intended for use within Oak Street Health's Canopy platform. Ensure compliance with all applicable laws and institutional policies before use.