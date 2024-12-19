from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

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
            # Count the number of events currently loaded
            event_elements = driver.find_elements(By.CLASS_NAME, "event-list-item")
            initial_count = len(event_elements)
            print(f"Currently loaded events: {initial_count}")

            # Attempt to click the "Load More" button
            try:
                load_more_button = driver.find_element(By.XPATH, "//span[@class='content-around mx-auto btn cursor-pointer']")
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)  # Ensure it's in view
                load_more_button.click()
                time.sleep(8)  # Wait for new events to load
            except NoSuchElementException:
                print("No more 'Load More' button found.")
                break

            # Recheck event count after clicking
            event_elements = driver.find_elements(By.CLASS_NAME, "event-list-item")
            new_count = len(event_elements)
            print(f"Events after loading more: {new_count}")

            # Break the loop if no new events are loaded
            if new_count <= initial_count:
                print("No new events loaded. Stopping.")
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
        df.to_csv("iticket_events.csv", index=False, encoding="utf-8-sig")
        print("Scraping completed. Data saved to iticket_events.csv.")
    else:
        print("No data scraped. Please check the script or website structure.")

# Run the scraper
scrape_events()

# Close the browser
driver.quit()
