from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import pandas as pd
import time
import re

# Initialize WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# URL of the main events page
main_page_url = "https://iticket.az/en/events"

# Function to scrape event details
def scrape_event_details():
    details = {
        "Name": "N/A",
        "Date and Time": "N/A",
        "Venue": "N/A",
        "Price": "N/A",
        "Location": "N/A",
        "Link": "N/A"
    }
    try:
        details["Name"] = driver.find_element(By.CLASS_NAME, 'session-name').text.strip() if driver.find_elements(By.CLASS_NAME, 'session-name') else 'N/A'
        details["Date and Time"] = driver.find_element(By.CLASS_NAME, 'value').text.strip() if driver.find_elements(By.CLASS_NAME, 'value') else 'N/A'
        details["Venue"] = driver.find_element(By.CLASS_NAME, 'venue-name').text.strip() if driver.find_elements(By.CLASS_NAME, 'venue-name') else 'N/A'
        details["Price"] = driver.find_element(By.CLASS_NAME, 'price').text.strip() if driver.find_elements(By.CLASS_NAME, 'price') else 'N/A'
        details["Location"] = driver.find_element(By.CLASS_NAME, 'venue-address').text.strip() if driver.find_elements(By.CLASS_NAME, 'venue-address') else 'N/A'
        details["Link"] = driver.current_url
    except Exception as e:
        print(f"Error scraping event details: {e}")
    return details

# Main scraping function
def scrape_events():
    driver.get(main_page_url)
    time.sleep(5)  # Wait for the page to load

    all_event_links = set()  # Use a set to avoid duplicate links
    events_data = []

    # Phase 1: Pagination
    while True:
        try:
            # Wait dynamically for the "Load More" button
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@class='content-around mx-auto btn cursor-pointer']"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)  # Ensure it's in view
                load_more_button.click()
                print("Clicked 'Load More' button. Waiting for new events...")
                time.sleep(5)  # Allow time for new content to load
            except TimeoutException:
                print("No more 'Load More' button or timeout reached.")
                break

        except StaleElementReferenceException:
            print("Stale element reference. Retrying...")
            time.sleep(3)
        except Exception as e:
            print(f"Unexpected error during 'Load More' click: {e}")
            break

    # Collect all event links after pagination
    event_elements = driver.find_elements(By.CLASS_NAME, "event-list-item")
    for event_element in event_elements:
        href = event_element.get_attribute("href")
        if href and href not in all_event_links:
            all_event_links.add(href)

    print(f"Found {len(all_event_links)} valid event links.")

    # Phase 2: Scraping
    for index, event_link in enumerate(all_event_links):
        try:
            print(f"Processing event {index + 1}/{len(all_event_links)}: {event_link}")
            driver.get(event_link)
            time.sleep(3)  # Wait for the detail page to load

            # Scrape event details
            event_details = scrape_event_details()
            events_data.append(event_details)
        except Exception as e:
            print(f"Error processing event {index + 1}: {e}")

    # Save data to CSV
    if events_data:
        df = pd.DataFrame(events_data)

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
        output_file_path = "iticket_events_cleaned.csv"
        df.to_csv(output_file_path, index=False, encoding="utf-8-sig")
        print(f"Scraping and cleaning completed. Data saved to {output_file_path}.")
    else:
        print("No data scraped. Please check the script or website structure.")

# Run the scraper
scrape_events()

# Close the browser
driver.quit()
