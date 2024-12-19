
import pandas as pd
import re

# Load data from the CSV file
csv_file_path = r"C:\Users\yusif\OneDrive\Desktop\iticket\regextest.csv"  # Replace with your actual file path
df = pd.read_csv(csv_file_path)

# Step 1: Extract and clean Language and Age from the Name column
def extract_and_clean(name):
    if not isinstance(name, str):
        return name, None, None  # Skip if Name is not a string
    
    # Extract Language and Age
    language_match = re.search(r'\(Language: (.*?)\)', name)
    age_match = re.search(r'\((\d+\+)\)', name)
    
    # Extract values if matched
    language = language_match.group(1) if language_match else None
    age = age_match.group(1) if age_match else None
    
    # Remove the matched parts from the name
    cleaned_name = re.sub(r'\(Language: .*?\)', '', name)  # Remove Language
    cleaned_name = re.sub(r'\(\d+\+\)', '', cleaned_name)  # Remove Age
    cleaned_name = cleaned_name.strip()  # Remove extra spaces
    
    return cleaned_name, language, age

# Apply the function to process the Name column
df[['Name', 'Language', 'Age']] = df['Name'].apply(lambda x: pd.Series(extract_and_clean(x)))

# Step 2: Split Date and Time into separate columns
def split_date_and_time(date_time):
    if not isinstance(date_time, str):
        return None, None, None  # Skip if the value is not a string
    
    # Use regex to extract the date, start time, and end time
    match = re.match(r'\w{3} (\d{2}\.\d{2}\.\d{4}) (\d{2}:\d{2}) - (\d{2}:\d{2})', date_time)
    if match:
        date, start_time, end_time = match.groups()
        return date, start_time, end_time
    else:
        return None, None, None

# Apply the function to process the Date and Time column
df[['Date', 'Start Time', 'End Time']] = df['Date and Time'].apply(lambda x: pd.Series(split_date_and_time(x)))

# Drop the original "Date and Time" column
df = df.drop(columns=['Date and Time'])

# Rearrange the columns
columns_order = ['Name', 'Language', 'Age', 'Date', 'Start Time', 'End Time', 'Venue', 'Price', 'Location', 'Link']
df = df[columns_order]

# Save the final DataFrame to a new CSV file
output_file_path = "scraped_data.csv"
df.to_csv(output_file_path, index=False, encoding="utf-8-sig")

print(f"Processing complete. The final file is saved as '{output_file_path}'.")
