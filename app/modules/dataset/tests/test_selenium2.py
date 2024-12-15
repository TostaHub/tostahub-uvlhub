import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets


def test_testViewUserProfileSelenium():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}")
        wait_for_page_to_load(driver)

        # Espera explícita para "Sample dataset 4"
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sample dataset 4"))
        ).click()

        # Espera explícita para "Doe, Jane"
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Doe, Jane"))
        ).click()

        # Espera explícita para el menú de hamburguesa
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".hamburger"))
        ).click()

        # Espera explícita para el elemento de la barra lateral
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sidebar-item:nth-child(2) .align-middle:nth-child(2)"))
        ).click()

        # Espera explícita para "Sample dataset 3"
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sample dataset 3"))
        ).click()

        # Espera explícita para "Doe, John"
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Doe, John"))
        ).click()

        print("Test 2 passed!")

    finally:

        # Close the browser
        close_driver(driver)


def test_DownloadUvlDataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}")
        wait_for_page_to_load(driver)

        driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        driver.find_element(By.LINK_TEXT, "Doe, Jane").click()
        driver.find_element(By.LINK_TEXT, "Sample dataset 2").click()
        driver.find_element(By.ID, "btnGroupDropExport24").click()
        driver.find_element(By.LINK_TEXT, "UVL").click()
        driver.find_element(By.ID, "btnGroupDropExport24").click()
        driver.find_element(By.LINK_TEXT, "Glencoe").click()
        driver.find_element(By.ID, "btnGroupDropExport24").click()
        driver.find_element(By.LINK_TEXT, "DIMACS").click()
        driver.find_element(By.ID, "btnGroupDropExport24").click()
        driver.find_element(By.LINK_TEXT, "SPLOT").click()
        driver.find_element(By.ID, "btnGroupDropExport24").click()
        driver.find_element(By.LINK_TEXT, "Descargar todos (ZIP)").click()
        driver.find_element(By.ID, "btnGroupDropExport25").click()
        driver.find_element(By.LINK_TEXT, "UVL").click()
        driver.find_element(By.ID, "btnGroupDropExport26").click()
        driver.find_element(By.LINK_TEXT, "Descargar todos (ZIP)").click()

        print("Test 3 passed!")

    finally:

        # Close the browser
        close_driver(driver)


test_testViewUserProfileSelenium()
test_DownloadUvlDataset()
