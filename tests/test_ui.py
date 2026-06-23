from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

BASE_URL = "http://35.154.1.53:32500"

def test_frontend_sentiment():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(BASE_URL)
        text_input = driver.find_element(By.ID, "text-input")
        submit_btn = driver.find_element(By.ID, "submit-btn")
        result_output = driver.find_element(By.ID, "result-output")

        text_input.send_keys("Spotlessly clean rooms with attentive staff and superb amenities throughout")
        submit_btn.click()
        time.sleep(3)

        output = result_output.text
        assert output != ""
        assert "POSITIVE" in output or "NEGATIVE" in output or "Confidence" in output
    finally:
        driver.quit()
