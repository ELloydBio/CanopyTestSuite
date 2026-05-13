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