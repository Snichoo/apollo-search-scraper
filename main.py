import os
import csv
import json
import time
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

from flask import Flask, request, jsonify

app = Flask(__name__)

# Set up the driver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")

# Initialize the driver using the system-installed chromedriver
driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
driver.implicitly_wait(2)

# Load config data
with open('config.json', 'r') as file:
    config = json.load(file)

def login_to_site(driver, config):
    print('Starting login process...')
    driver.get('https://app.apollo.io/#/login')

    # Wait for the login form to be present
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "email")))

    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    email_field.send_keys(config['email'])
    password_field.send_keys(config['password'])
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for the URL to change indicating successful login
    print("Waiting for login to complete...")
    try:
        WebDriverWait(driver, 30).until(lambda d: 'apollo.io' in d.current_url and '/home' in d.current_url)
        print("Login successful.")
    except TimeoutException:
        print("Login failed: timeout waiting for login to complete.")
        driver.save_screenshot('login_timeout.png')
        print("Saved screenshot to 'login_timeout.png'")
        driver.quit()
        exit(1)

def reveal_and_collect_email(driver):
    try:
        # First, try to find the email directly
        print("Attempting to find the email directly...")
        email_element = driver.find_element(By.XPATH, "//span[contains(text(), '@')]")
        email = email_element.text
        print(f"Collected email directly: {email}")
        return email
    except NoSuchElementException:
        print("Email not found directly. Checking for 'Access email' button...")

    try:
        # If email is not found, look for the 'Access email' button
        access_email_button = driver.find_element(By.XPATH, "//button[.//span[text()='Access email']]")
        print("Found 'Access email' button, clicking...")
        access_email_button.click()
        print("Clicked 'Access email' button.")

        # Wait for the email to be visible after clicking the button
        print("Waiting for email to be visible...")
        email_element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), '@')]"))
        )
        email = email_element.text
        print(f"Collected email after clicking button: {email}")
        return email

    except NoSuchElementException:
        print("Neither email nor 'Access email' button found.")
        driver.save_screenshot('email_not_found.png')
        print("Saved screenshot to 'email_not_found.png'")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.save_screenshot('reveal_and_collect_email_exception.png')
        print("Saved screenshot to 'reveal_and_collect_email_exception.png'")
        return None

@app.route('/get_email', methods=['POST'])
def get_email():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    organization_id = data.get('organization_id')

    if not (first_name and last_name and organization_id):
        return jsonify({'error': 'Missing parameters'}), 400

    # Construct the URL
    url = f"https://app.apollo.io/#/people?sortByField=%5Bnone%5D&sortAscending=false&page=1&qPersonName={first_name}%20{last_name}&organizationIds[]={organization_id}"

    # Ensure we are logged in
    if not driver.current_url.startswith('https://app.apollo.io/'):
        login_to_site(driver, config)

    # Navigate to the URL
    driver.get(url)

    try:
        # Wait for the page to load
        print("Waiting for page to load...")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded successfully.")

        # Call the function to reveal and collect the email
        email = reveal_and_collect_email(driver)

        if email:
            return jsonify({'email': email})
        else:
            return jsonify({'error': 'Email not found'}), 404

    except TimeoutException:
        print("Timeout: Page did not load within the expected time.")
        driver.save_screenshot('main_timeout_screenshot.png')
        print("Saved screenshot to 'main_timeout_screenshot.png'")
        return jsonify({'error': 'Timeout loading page'}), 500
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.save_screenshot('exception_screenshot.png')
        print("Saved screenshot to 'exception_screenshot.png'")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    # For Google Cloud Run, the port should be 8080
    app.run(host='0.0.0.0', port=8080)
