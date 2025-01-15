from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import csv
from PIL import Image
import pytesseract
import base64 
import re

pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)


def get_captcha_text():
    try:
        # Find the captcha image element
        captcha_img = wait.until(
            EC.presence_of_element_located((By.ID, "captcha_image"))
        )
        
        # Get image using JavaScript
        js_script = """
        var img = document.getElementById('captcha_image');
        var canvas = document.createElement('canvas');
        // Get the actual dimensions of the image
        var width = img.naturalWidth || img.width;
        var height = img.naturalHeight || img.height;
        
        // Set canvas size to match image
        canvas.width = width;
        canvas.height = height;
        
        var ctx = canvas.getContext('2d');
        
        // Clear the canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw image at proper scale
        ctx.drawImage(img, 0, 0, width, height);
        
        return canvas.toDataURL('image/png');
        """
        
        # Execute JavaScript to get base64 image
        img_base64 = driver.execute_script(js_script)
        
        # Remove the data URL prefix
        img_base64 = img_base64.replace('data:image/png;base64,', '')
        
        # Decode base64 to bytes
        img_bytes = base64.b64decode(img_base64)
        
        # Save bytes to file
        with open('captcha.png', 'wb') as f:
            f.write(img_bytes)
            
        # Open and process image
        image = Image.open('captcha.png')
        
        # Enhanced OCR configuration
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        captcha_text = pytesseract.image_to_string(image, config=custom_config)
        
        # Clean up text
        captcha_text = captcha_text.strip()
        print(f"Captcha text: {captcha_text}")
        return captcha_text
        
    except Exception as e:
        print(f"Failed to get captcha text: {str(e)}")
        print("Full error:")
        import traceback
        traceback.print_exc()
        return None

def check_and_close_modal():
    """
    Helper function to check for modal and close button.

    Parameters:
    driver (selenium.webdriver.Chrome): The Selenium WebDriver instance used to interact with the web page.
    wait (selenium.webdriver.support.ui.WebDriverWait): The WebDriverWait instance used to wait for specific conditions.

    Returns:
    bool: True if the modal is closed successfully, False otherwise.
    """
    try:
        # First check if modal exists
        modal = wait.until(
            EC.presence_of_element_located((By.ID, "validateError"))
        )

        if modal.is_displayed():
            print("Modal detected")
            # Check for close button
            try:
                close_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div[9]/div/div/div[1]/button"))
                )
                if close_button.is_displayed():
                    print("Close button found, clicking it")
                    time.sleep(1)
                    close_button.click()
                    time.sleep(1)
                    return True
                else:
                    print("Close button exists but is not displayed")
                    return False
            except (TimeoutException, NoSuchElementException):
                print("No close button found on modal")
                return False
    except (TimeoutException, NoSuchElementException):
        print("No modal detected")
        return False


def access_court_services(act_name="Indian Penal Code", section_number="376"):
    """
    Automates the process of accessing court services and searching for specific acts and sections.

    Parameters:
    act_name (str): Name of the act to search for (e.g., "Indian Penal Code")
    section_number (str): Section number to search for (e.g., "376")

    Returns:
    selenium.webdriver.Chrome: The Selenium WebDriver instance
    """

    

    try:
        # Initial page load and menu selection
        driver.get("https://services.ecourts.gov.in/")
        left_menu = wait.until(EC.element_to_be_clickable((By.ID, "leftPaneMenuCS")))
        left_menu.click()
        check_and_close_modal()

        # Select State and District
        try:
            # State selection
            select_state = wait.until(EC.presence_of_element_located((By.ID, "sess_state_code")))
            Select(select_state).select_by_value("18")
            time.sleep(1)
            check_and_close_modal()

            # District selection
            time.sleep(3)
            select_dist = wait.until(EC.presence_of_element_located((By.ID, "sess_dist_code")))
            Select(select_dist).select_by_value("3")
            time.sleep(1)
            check_and_close_modal()

            # Court complex selection
            select_court = wait.until(EC.presence_of_element_located((By.ID, "court_complex_code")))
            Select(select_court).select_by_value("1180029@1,2,10,11@Y")
            time.sleep(1)
            check_and_close_modal()

            # Court establishment selection
            select_court = wait.until(EC.presence_of_element_located((By.ID, "court_est_code")))
            Select(select_court).select_by_value("1")
            time.sleep(1)
            check_and_close_modal()

        except Exception as e:
            print(f"Error during location selection: {str(e)}")
            return driver

        # Click Act tab and handle modal
        try:
            act_button = wait.until(EC.element_to_be_clickable((By.ID, "act-tabMenu")))
            try:
                act_button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", act_button)
            time.sleep(3)
            check_and_close_modal()

        except Exception as e:
            print(f"Error clicking act tab: {str(e)}")
            return driver

        # Select Act and Section
        try:
            # Select Act
            select_act = wait.until(EC.presence_of_element_located((By.ID, "actcode")))
            Select(select_act).select_by_visible_text(act_name)
            time.sleep(1)
            check_and_close_modal()

            # Enter Section
            entersection = wait.until(EC.presence_of_element_located((By.ID, "under_sec")))
            entersection.clear()
            entersection.send_keys(section_number)
            time.sleep(1)
            check_and_close_modal()

        except Exception as e:
            print(f"Error selecting act or section: {str(e)}")
            return driver

        # Handle Captcha
        try:
            # Wait for the previous actions to complete
            time.sleep(2)
            
            # Try to get captcha multiple times if needed
            max_attempts = 3
            for attempt in range(max_attempts):
                print(f"Attempt {attempt + 1} to read captcha")
                captcha_text = get_captcha_text()
                if captcha_text:
                    print(f"Successfully extracted text: {captcha_text}")
                    # Try to find and fill captcha input
                    try:
                        captcha_input = wait.until(
                            EC.presence_of_element_located((By.ID, "act_captcha_code"))
                        )
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_text)
                        break
                    except Exception as e:
                        print(f"Error inputting captcha: {str(e)}")
                else:
                    print(f"Failed attempt {attempt + 1}")
                    time.sleep(2)  # Wait before next attempt
            
        except Exception as e:
            print(f"Error in captcha handling: {str(e)}")
        try:
            # Click Search button
            wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/main/div[2]/div/div/div[6]/div[1]/form/div[3]/div[2]/button')))
            search_button = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/main/div[2]/div/div/div[6]/div[1]/form/div[3]/div[2]/button')))
            print("Search button located.")
            driver.execute_script("arguments[0].click();", search_button)
            print("Search Button Clicked.")
            check_and_close_modal()
            try:
                wait.until(EC.presence_of_element_located((By.ID, "res_act")))
                print("Search results found")
            
            except TimeoutException:
                print("No search results found")
        except:
            print("Error clicking search button")
            
        # Wait for search results


    except Exception as e:
        print(f"An error occurred: {str(e)}")

    return driver


def process_search_results(case_status):
    """
    Process all search results, navigate to each "View" page, and scrape data.
    Only processes rows where the case year is 2024.
    """
    
    all_case_data = []

    try:
        # Locate all rows in the search results starting from the second row
        try:
            print("Waiting for rows to load...")
            rows=[]
            wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@id='dispTable']/tbody/tr[position() > 1]")))
            rows=driver.find_elements(By.XPATH, "//*[@id='dispTable']/tbody/tr[position() > 1]")
            print(rows)
        except Exception as e:
            print(f"Error finding rows: {str(e)}")

        for index, row in enumerate(rows):
            try:
                print(f"Processing row {index + 1}")

                # Extract the case number from the second <td> (index 1) element
                case_number_cell = row.find_elements(By.TAG_NAME, "td")[1].text
                print(f"Case Number: {case_number_cell}")

                # Check if the year at the end of the case number is 2024
                match = re.search(r'(\d{4})$', case_number_cell)
                if match and match.group(1) == "2024":
                    # If the year is 2024, click the "View" button (last <td> element)
                    view_button = row.find_elements(By.TAG_NAME, "td")[-1].find_element(By.TAG_NAME, "a")
                    print(f"Year is 2024, clicking 'View' button.")
                    driver.execute_script("arguments[0].click();", view_button)

                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[2]/div/div/div[6]/div[2]")))
                    # Scrape the data
                    case_details = scrape_case_details(case_status)
                    print("Scraped a row")
                    if case_details:
                        all_case_data.append(case_details)

                    try:
                        back_button = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/div[2]/div/div/div[6]/p/button")))
                        driver.execute_script("arguments[0].click();", back_button)
                        print("Back button clicked")
                        
                    except TimeoutException:
                        print("Unable to find back button")


                else:
                    print(f"Skipping row {index + 1}, year is not 2024.")

            except Exception as e:
                print(f"Error processing row {index + 1}: {str(e)}")
                try:
                    time.sleep(3)
                    back_button = wait.until(EC.presence_of_element_located((By.ID, "main_back_act")))
                    back_button.click()
                    print("Back button clicked")
                    
                except TimeoutException:
                    print("Unable to find back button")
                wait.until(EC.visibility_of_all_elements_located((By.XPATH, "//button[contains(text(), 'View')]")))
                

    except Exception as e:
        print(f"Error processing search results: {str(e)}")

    return all_case_data

def scrape_case_details(case_status):
    """
    Scrape details from the detailed case page.
    """
    print("Inside scrape_case_detail function")
    time.sleep(3)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "CSact")))
    table = driver.find_element(By.XPATH, '//*[@id="CSact"]/table[1]')
    print("extracting fields.")
    
    if case_status=="pending":
        print("pending cases")
        fields = {
        "Case Type": '//*[@id="CSact"]/table[1]/tbody/tr[1]/td[2]',
        "Filing Number": '//*[@id="CSact"]/table[1]/tbody/tr[2]/td[2]',
        "Filing Date": '//*[@id="CSact"]/table[1]/tbody/tr[2]/td[4]',
        "Registration Number": '//*[@id="CSact"]/table[1]/tbody/tr[3]/td[2]/label',
        "Registration Date": '//*[@id="CSact"]/table[1]/tbody/tr[3]/td[4]',
        "CNR Number": '//*[@id="CSact"]/table[1]/tbody/tr[4]/td[2]/span',
        "First Hearing Date": '//*[@id="CSact"]/table[2]/tbody/tr[1]/td[2]',
        "Next Hearing Date": '//*[@id="CSact"]/table[2]/tbody/tr[2]/td[2]/strong',
        "Case Stage": '//*[@id="CSact"]/table[2]/tbody/tr[3]/td[2]/label/strong',
        "Court Number and Judge": '//*[@id="CSact"]/table[2]/tbody/tr[4]/td[2]/label/strong',
        "Petitioner and Advocate": '//*[@id="CSact"]/table[3]/tbody/tr/td',
        "Respondent and Advocate": '//*[@id="CSact"]/table[4]/tbody/tr/td',
        "Police Station": '//*[@id="CSact"]/table[7]/tbody/tr[1]/td[2]',
        "FIR Number": '//*[@id="CSact"]/table[7]/tbody/tr[2]/td[2]',
        "Year": '//*[@id="CSact"]/table[7]/tbody/tr[3]/td[2]',
        "Case Transfer Date": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[2]',
        "From Court Number and Judge": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[3]',
        "To Court Number and Judge": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[4]'
        }
    elif case_status=="disposed":
        print("disposed cases")
        fields = {
        "Case Type": '//*[@id="CSact"]/table[1]/tbody/tr[1]/td[2]',
        "Filing Number": '//*[@id="CSact"]/table[1]/tbody/tr[2]/td[2]',
        "Filing Date": '//*[@id="CSact"]/table[1]/tbody/tr[2]/td[4]',
        "Registration Number": '//*[@id="CSact"]/table[1]/tbody/tr[3]/td[2]/label',
        "Registration Date": '//*[@id="CSact"]/table[1]/tbody/tr[3]/td[4]',
        "CNR Number": '//*[@id="CSact"]/table[1]/tbody/tr[4]/td[2]/span',
        "First Hearing Date": '//*[@id="CSact"]/table[2]/tbody/tr[1]/td[2]',
        "Decision Date": '//*[@id="CSact"]/table[2]/tbody/tr[2]/td[2]/strong',
        "Case Status": '//*[@id="CSact"]/table[2]/tbody/tr[3]/td[2]/strong,',
        "Nature of Disposal": '//*[@id="CSact"]/table[2]/tbody/tr[4]/td[2]/label/strong',
        "Court Number and Judge": '//*[@id="CSact"]/table[2]/tbody/tr[5]/td[2]/label/strong',
        "Petitioner and Advocate": '//*[@id="CSact"]/table[3]/tbody/tr/td',
        "Respondent and Advocate": '//*[@id="CSact"]/table[4]/tbody/tr/td',
        "Police Station": '//*[@id="CSact"]/table[7]/tbody/tr[1]/td[2]',
        "FIR Number": '//*[@id="CSact"]/table[7]/tbody/tr[2]/td[2]',
        "Year": '//*[@id="CSact"]/table[7]/tbody/tr[3]/td[2]',
        "Case Transfer Date": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[2]',
        "From Court Number and Judge": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[3]',
        "To Court Number and Judge": '//*[@id="CSact"]/table[10]/tbody/tr[2]/td[4]'}
    else:
        "Not valid Case Status"
    case_details = {}

    for field, xpath in fields.items():
        try:
            value = table.find_element(By.XPATH, xpath).text.strip()       
            case_details[field] = value
        except:
            case_details[field] = "N/A"  # Handle missing values
            
    print(f"Scraped details: {case_details}")
    return case_details

def save_to_csv(data, filename="case_details.csv"):
    """
    Save the scraped data to a CSV file.
    """
    if not data:
        print("No data to save.")
        return 

    try:
        # Extract headers from the case
        headers = data[0].keys()

        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")
        
def switch_to_disposed_cases():
    try:
        disposed_button = wait.until(EC.element_to_be_clickable((By.ID, "radDact")))
        try:
            disposed_button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", disposed_button)
        time.sleep(3)
        check_and_close_modal()

    except Exception as e:
        print(f"Error clicking disposed tab: {str(e)}")
    
    # Handle Captcha
    try:

        time.sleep(2)

        max_attempts = 3
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1} to read captcha")
            captcha_text = get_captcha_text()
            if captcha_text:
                print(f"Successfully extracted text: {captcha_text}")
                # Try to find and fill captcha input
                try:
                    captcha_input = wait.until(
                        EC.presence_of_element_located((By.ID, "act_captcha_code"))
                    )
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)
                    break
                except Exception as e:
                    print(f"Error inputting captcha: {str(e)}")
            else:
                print(f"Failed attempt {attempt + 1}")
                time.sleep(2)  # Wait before next attempt
            
    except Exception as e:
        print(f"Error in captcha handling: {str(e)}")
        
    try:
        # Click Search button
        wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/main/div[2]/div/div/div[6]/div[1]/form/div[3]/div[2]/button')))
        search_button = wait.until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/main/div[2]/div/div/div[6]/div[1]/form/div[3]/div[2]/button')))
        print("Search button located.")
        driver.execute_script("arguments[0].click();", search_button)
        print("Search Button Clicked.")
        check_and_close_modal()
        try:
            wait.until(EC.presence_of_element_located((By.ID, "res_act")))
            print("Search results found")
        
        except TimeoutException:
            print("No search results found")
    except:
        print("Error clicking search button")
            
    # Wait for search results
    return driver


if __name__ == "__main__":
    act_name = input("Enter Act name (default: Indian Penal Code): ") or "Indian Penal Code"
    section_number = input("Enter Section number (default: 376): ") or "376"

    driver = access_court_services(act_name, section_number)

    all_case_data = process_search_results("pending")

    save_to_csv(all_case_data)

    switch_to_disposed_cases()
    all_disposed_case_data = process_search_results("disposed")
    save_to_csv(all_disposed_case_data, "disposed_case_details.csv")
