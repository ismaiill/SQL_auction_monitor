from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
import time
import threading
import time
import re
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date,timedelta
import schedule

class Aggregator:
    def __init__(self, url, driver):
        self.url = url
        self.driver = driver
        self.auctions = []

    def aggregate_auctions(self):
        last_index  = 13
        for index in range(3, 6):
            self.get_auctions_from_current_page()
            self.go_to_next_page(index)
            time.sleep(2)
        self.driver.quit()
        return self.auctions

    def go_to_next_page(self, index):
        L0 = self.get_cards()
        L1 = L0[0]
        L2 = L1.find_element(By.XPATH, "./*[1]")
        cards = L2.find_element(By.XPATH, "./*[1]")

        navigation = cards.find_element(By.XPATH, "./*[12]")
        navigation = navigation.find_element(By.XPATH, "./*[1]")
        button = navigation.find_element(By.XPATH, "./*[" + str(index) + "]")
        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(10)
        button.click()

    def get_auctions_from_current_page(self):
        L0 = self.get_cards()
        L1 = L0[0]
        L2 = L1.find_element(By.XPATH, "./*[1]")
        cards = L2.find_element(By.XPATH, "./*[1]")

        rows = cards.find_elements(By.XPATH, "./*")       
        rows = list(rows)
        for i in range(2, 12):
             for j in range(2, 7):
                try:
                    row = cards.find_element(By.XPATH, "./*[" + str(i) + "]")
                    row = row.find_element(By.XPATH, "./*[1]")
                    card = row.find_element(By.XPATH, "./*[" + str(j) + "]")
                    date_container = card.find_element(By.XPATH, "./*[4]")
                    auction_date = date_container.find_element(By.XPATH, "./*[1]")
                    html = "https://www.dealdash.com/auction/" + card.get_attribute("id")[8:]
                    auction_date = auction_date.get_attribute("innerText")
                    if auction_date.split(" ")[0] == "Today" or auction_date.split(" ")[0] == "Tomorrow":
                        time_of_auction = auction_date.split(" ")[2] + " " + auction_date.split(" ")[3]
                        time_of_auction = datetime.strptime(time_of_auction, "%I:%M %p")
                        time_of_auction = time_of_auction.strftime("%H:%M")

                        if auction_date.split(" ")[0] == "Today":
                            date_of_auction = date.today()
                        if auction_date.split(" ")[0] == "Tomorrow":
                            date_of_auction = date.today() + timedelta(days=1)
                        # print(date_of_auction, time_of_auction)
                        # print(html)
                        self.auctions.append((html, date_of_auction, time_of_auction))
                except:
                    continue

        # print(self.auctions)         
    def get_cards(self, timeout=2):
        cards_container = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.css-175oi2r.r-150rngu.r-eqz5dr.r-16y2uox.r-1wbh5a2.r-11yh6sk.r-1rnoaur.r-agouwx.r-1udh08x.r-13awgt0'))        )
        return cards_container


def get_auctions():
    url = 'https://www.dealdash.com/'
    driver = setup_aggregator_driver()
    driver.get(url)
    driver.get(url)
    time.sleep(5)
    auctions = Aggregator(url, driver)
    auctions_list = auctions.aggregate_auctions()
    return auctions_list

def setup_aggregator_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out or remove this line
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("detach", True)  # This keeps the browser open
    chrome_options.add_argument("--start-maximized")  # Start with maximized window
    chrome_options.add_argument("--disable-infobars")  # Disable infobars
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    
    return webdriver.Chrome(options=chrome_options)



get_auctions()