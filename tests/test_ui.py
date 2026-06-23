import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", None)

def test_frontend_sentiment():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if SELENIUM_REMOTE_URL:
        driver = webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options
        )
    else:
        driver = webdriver.Chrome(options=options)

    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 15)

        text_input = wait.until(EC.presence_of_element_located((By.ID, "text-input")))
        text_input.send_keys("This hotel is absolutely wonderful")

        submit_btn = driver.find_element(By.ID, "submit-btn")
        submit_btn.click()

        # FIX: wait for actual content — "Confidence" always appears in output
        wait.until(EC.text_to_be_present_in_element((By.ID, "result-output"), "Confidence"))

        result_text = driver.find_element(By.ID, "result-output").text

        assert result_text.strip() != "", "Result output is empty"
        assert any(word in result_text for word in ["POSITIVE", "NEGATIVE", "Confidence"]), \
            f"Unexpected result: {result_text}"
    finally:
        driver.quit()
