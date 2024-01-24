import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import subprocess
import tempfile
import re
import os
import shutil


st.title('PDF Processing and Information Extraction')

# Function to unlock a single PDF file using qpdf
def unlock_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input_pdf:
        # Write the uploaded file content to the temporary file
        temp_input_pdf.write(uploaded_file.getvalue())
        input_path = temp_input_pdf.name

    output_path = input_path.replace(".pdf", "_unlocked.pdf")

    try:
        # Run qpdf to unlock the PDF
        subprocess.run(['qpdf', '--decrypt', '--remove-restrictions', input_path, output_path], check=True)
    except subprocess.CalledProcessError as e:
        st.error(f'Error in unlocking PDF: {e}')
        return None
    finally:
        # Remove the original temporary file
        os.remove(input_path)

    return output_path

# Function to safely extract information using regex pattern
def safe_extraction(pattern, text):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None

# Function to extract dynamic information from PDF text
def extract_dynamic_info(text, field_patterns):
    info_dict = {field: None for field in field_patterns}
    for field, pattern in field_patterns.items():
        match = safe_extraction(pattern, text)
        if match:
            info_dict[field] = float(match) if match.replace('.', '', 1).isdigit() else match
    return info_dict

# Function to process and extract data from a single PDF file
def process_single_pdf(pdf_path, field_patterns):
    full_text = ""
    with fitz.open(pdf_path) as doc:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            full_text += page.get_text()
    return extract_dynamic_info(full_text, field_patterns)

# Upload multiple PDF files
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Define the regex patterns for fields to extract
field_patterns = {  
    "Address Line 1": r"Address line 1\n(.+?)\s*\n",
    "Address Line 2": r"Address line 2\n(.+?)\s*\n",
    "Address Line 3": r"Address line 3\n(.+?)\s*\n",
    "Dwelling Type": r"Dwelling Type\n(.+?)\s*\n",
    "Total Floor Area": r"Total Floor Area\n([\d.]+)",
    "BER Result": r"BER Result\n(\w+)\s*\n",
    "BER Number": r"BER Number\n(\d+)\s*\n",
    "EPC": r"EPC\n([\d.]+)",
    "CPC": r"CPC\n([\d.]+)",
    # Add additional patterns here as necessary
}

# if uploaded_files:
#     # Dataframe to store all extracted data
#     data = pd.DataFrame(columns=field_patterns.keys())

#     for uploaded_file in uploaded_files:
#         with st.spinner(f'Processing {uploaded_file.name}...'):
#             unlocked_pdf_path = unlock_pdf(uploaded_file)
#             if unlocked_pdf_path:
#                 extracted_info = process_single_pdf(unlocked_pdf_path, field_patterns)
#                 # Update this line to use pandas.concat
#                 data = pd.concat([data, pd.DataFrame([extracted_info])], ignore_index=True)
#                 os.remove(unlocked_pdf_path)  # Clean up the temporary unlocked file
#             else:
#                 st.error(f"Failed to process {uploaded_file.name}")


if uploaded_files:
    # Initialize progress bar
    progress_bar = st.progress(0)
    num_files = len(uploaded_files)
    data = pd.DataFrame(columns=field_patterns.keys())

    for i, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f'Processing {uploaded_file.name}...'):
            unlocked_pdf_path = unlock_pdf(uploaded_file)
            if unlocked_pdf_path:
                extracted_info = process_single_pdf(unlocked_pdf_path, field_patterns)
                data = pd.concat([data, pd.DataFrame([extracted_info])], ignore_index=True)
                os.remove(unlocked_pdf_path)  # Clean up the temporary unlocked file
            else:
                st.error(f"Failed to process {uploaded_file.name}")
        
        # Update progress bar
        progress_bar.progress((i + 1) / num_files)

    # Hide the progress bar after processing
    progress_bar.empty()
    
    # Convert the dataframe to CSV
    csv_data = data.to_csv(index=False).encode('utf-8')

    # Download button for the CSV file
    st.download_button(
        label="Download Extracted Data as CSV",
        data=csv_data,
        file_name='extracted_data.csv',
        mime='text/csv',
    )
