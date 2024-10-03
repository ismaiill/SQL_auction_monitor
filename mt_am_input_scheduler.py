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
from datetime import datetime, date
import schedule

class AuctionMonitor:   
    def __init__(self, url, driver, db_config):
        self.url = url
        self.auction_web_identifier = url.split("/")[-1]
        self.driver = driver
        self.db_config = db_config
        current_date = date.today()
        self.unique_identifier = f"{self.auction_web_identifier}_{current_date}"
   
    def start_monitoring_bids(self):
        self.driver = setup_driver()
        self.driver.get(self.url)
        
        previous_data = None
        try:
            while True:
                current_log = self.get_current_log(self.driver)
                self.keep_alive(self.driver)
                self.save_to_database(current_log)
                status = self.is_item_sold(self.driver)
                if status == True:
                    print("Item is sold!, stopped monitoring bids.")
                    break
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")

    def start_monitoring_bidders_info(self):
        self.driver = setup_driver()
        self.driver.get(self.url)
        
        previous_data = None
        try:
            while True:
                current_bidders_username, current_bidders_info = self.get_current_bider_info(self.driver)
                self.keep_alive(self.driver)
                if current_bidders_info != previous_data:
                    previous_data = current_bidders_info
                    if current_bidders_info and current_bidders_info != [None, None]:
                        current_bidders_time_joined = current_bidders_info[0]
                        current_bidders_location = current_bidders_info[1]
                        self.save_to_database(current_highest_bid_username=current_bidders_username, current_bidder_location=current_bidders_location, current_bidder_time_joined=current_bidders_time_joined)
                        #print( "current_bidders_username: ", current_bidders_username)
                        #print( "current_bidders_location: ", current_bidders_location)
                        #print( "current_bidders_time_joined: ", current_bidders_time_joined)
                        #print( "----------------------------------------")
                status = self.is_item_sold(self.driver)
                if status == True:
                    #self.update_database()
                    print("Item is sold!, stopped monitoring bidders info.")
                    break
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")
        # finally:
        #     self.driver.quit()

    def start_monitorinig_auction(self):
        bid_thread = threading.Thread(target=self.start_monitoring_bids)
        bidder_thread = threading.Thread(target=self.start_monitoring_bidders_info)
        bid_thread.start()
        bidder_thread.start()
        try:
            while True:
                if not bid_thread.is_alive() and not bidder_thread.is_alive():
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            # You might want to implement a way to stop the threads gracefully here
            print(f"Monitoring of auction {self.auction_web_identifier} complete.")
            self.update_database()
            print("Auction status updated in database")
            self.driver.quit()

    def keep_alive(self, driver):
        try:
            driver.execute_script("return 1;")
        except Exception as e:
            print(f"Error refreshing driver: {e}")

    def get_current_log(self, driver):
        try:
            # Wait for the parent div with role="log"
            log_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='log']"))
            )
            log_entries = log_element.find_elements(By.XPATH, "./div")
            bids = []
            for index in range(1, len(log_entries)):
                bids.append(log_entries[index].text.split("\n"))
            return bids
        except Exception as e:
            print(f"Error getting auction data: {e}")
            return None

    def get_current_bider_info(self, driver):  
        start_time = time.time()
        while True:
            try:
                bidder_username = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='css-146c3p1 r-gfo7p r-cv4lhi r-vw2c0b r-jwli3a']"))
                )
                bidder_info_element = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='css-175oi2r r-18u37iz r-1awozwy']"))
                )
                if bidder_info_element and len(bidder_username.text) != 0:
                    bidder_username = bidder_username.text
                    bidder_info_element = bidder_info_element.text
                    bidder_info = bidder_info_element.split("\n")
                    if len(bidder_info) > 1:
                        return bidder_username, bidder_info
            except (TimeoutException, StaleElementReferenceException):
                print("Element not found, retrying...")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return [None, None]

    def is_item_sold(self, driver, timeout=10):
        try:
            sold_element = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'css-146c3p1') and contains(text(), 'SOLD')]"))
            )
            return True
        except:
            return False

    def update_database(self):
        connection = self.get_db_connection()
        if not connection:
            raise Exception("Failed to get database connection")
        cursor = connection.cursor()
        
        cursor.execute("UPDATE auctions SET is_sold = 1 WHERE unique_identifier = %s", (self.unique_identifier,))
        connection.commit()
        cursor.close()
        #print("Auction status updated in database")
        connection.close()

    def save_to_database(self, current_log=None, 
                         current_highest_bid_username=None, 
                         current_bidder_location=None, 
                         current_bidder_time_joined=None):
        connection = self.get_db_connection()
        if not connection:
            raise Exception("Failed to get database connection")
        
        cursor = connection.cursor()
        try:
            if current_log is not None:
                for bid in current_log:
                    if len(bid) > 2:
                        current_date = date.today()
                        time_obj = datetime.strptime(bid[2], '%I:%M:%S %p')
                        full_timestamp = datetime.combine(current_date, time_obj.time())

                        current_highest_bid_amount = float(bid[0].replace('$', ''))
                        current_highest_bid_username = bid[1]

                        cursor.execute("INSERT IGNORE INTO bids (unique_identifier, highest_bid, bidder_name, bid_time) VALUES (%s, %s, %s, %s)", 
                            (self.unique_identifier, current_highest_bid_amount, current_highest_bid_username, full_timestamp))
           
            if current_highest_bid_username and current_bidder_location and current_bidder_time_joined:
                current_bidder_time_joined = datetime.strptime(current_bidder_time_joined.strip(), '%m/%d/%Y').date()
                cursor.execute("""
                    INSERT IGNORE INTO bidders (bidder_name, bidder_location, join_date) 
                        VALUES (%s, %s, %s)
                """, (current_highest_bid_username, current_bidder_location, current_bidder_time_joined))

            connection.commit()
            cursor.close()
            #print("Auction data saved to database")
        except Exception as e:
            print(f"An error occurred while saving to database: {e}")
        finally:
            cursor.close()
            connection.close()

    def get_db_connection(self):
        try:
            if not hasattr(self, 'db_pool'):
                self.db_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=5,
                **self.db_config
            )
            return self.db_pool.get_connection()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return None

class AuctionInfo:
    def __init__(self, url, driver, db_config):
        self.url = url
        self.driver = driver
        self.db_config = db_config
        self.item_name = None
        self.buy_it_now_price = None
        self.no_jumper_limit = None
        self.auction_web_identifier = self.url.split("/")[-1]
        current_date = date.today()
        self.unique_identifier = f"{self.auction_web_identifier}_{current_date}"

    def get_auction_info(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        self.item_name = self.get_item_info()
        self.buy_it_now_price = self.get_buy_it_now_info()
        self.no_jumper_limit = self.get_no_jumper_limit()
        is_runner_up_discount = self.is_runner_up_discount()
        is_no_reentry = self.is_no_reentry()
        is_tripple_booked = self.is_tripple_booked()
        is_overload = self.is_overload()
        self.save_to_database(is_runner_up_discount, is_no_reentry, is_tripple_booked, is_overload, is_sold=False) 
      
    def get_buy_it_now_info(self):
        price_div = self.driver.find_element(By.CSS_SELECTOR, 'div.css-146c3p1.r-cqee49.r-gfo7p.r-ubezar')
        if price_div:
            price_text = price_div.text.strip()
            price_match = re.search(r'\$([0-9,]+)', price_text)
            if price_match:
                price = price_match.group(1).replace(',', '')
                print('Buy it now price: ', '$'+price)
                return price
        return None

    def get_no_jumper_limit(self):
        try:
            no_jumper_div = self.driver.find_element(By.XPATH, "//div[contains(@class, 'css-146c3p1') and contains(text(), 'No Jumper Limit')]")
            if no_jumper_div:
                limit_text = no_jumper_div.text.strip()
                limit_match = re.search(r'\$(\d+(?:\.\d{2})?)', limit_text)
                if limit_match:
                    limit = float(limit_match.group(1))
                    print('No Jumper Limit: ', limit)
                    return limit
        except:
            pass
        return None

    def get_item_info(self):
        item_name_h1 = self.driver.find_element(By.CSS_SELECTOR, 'h1.css-146c3p1.r-gfo7p.r-xdvzot.r-1x35g6.r-vw2c0b')
        if item_name_h1:
            item_name = item_name_h1.text.strip()
            print('Item name: ', item_name)
            return item_name
        return None

    def save_to_database(self, is_runner_up_discount, is_no_reentry, is_tripple_booked, is_overload, is_sold):
        connection = self.get_db_connection()
        if not connection:
            raise Exception("Failed to get database connection")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO auctions (unique_identifier, item_name, buy_it_now_price, no_jumper_limit, is_runner_up_discount, is_no_reentry, is_tripple_booked, is_overload, is_sold) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
               (self.unique_identifier, self.item_name, self.buy_it_now_price, self.no_jumper_limit, is_runner_up_discount, is_no_reentry, is_tripple_booked, is_overload, is_sold))
        connection.commit()
        cursor.close()
        print("Auction info saved to database")
        connection.close()

    def get_db_connection(self):
        try:
            if not hasattr(self, 'db_pool'):
                self.db_pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=5,
                    **self.db_config
                )
            return self.db_pool.get_connection()
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return None
    
    def is_runner_up_discount(self):
        try:
            runner_up_discount_icon = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//div[contains(@class, 'css-146c3p1') and "
                    "contains(@class, 'r-cqee49') and "
                    "contains(@class, 'r-gfo7p') and "
                    "contains(@class, 'r-q4m81j') and "
                    "contains(text(), 'Runner-Up Discount')]"
                ))
            )
            return True
        except:
            return False

    def is_no_reentry(self):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                "//div[contains(@class, 'css-146c3p1') and "
                "contains(@class, 'r-cqee49') and "
                "contains(@class, 'r-gfo7p') and "
                "contains(@class, 'r-q4m81j') and "
                "contains(text(), 'No Re-Entry Auction')]"
                ))
            )
            return True
        except:
            return False

    def is_tripple_booked(self):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                "//div[contains(@class, 'css-146c3p1') and "
                "contains(@class, 'r-cqee49') and "
                    "contains(@class, 'r-gfo7p') and "
                    "contains(@class, 'r-q4m81j') and "
                    "contains(text(), 'Triple-Booked Auction')]"
                ))
            )
            return True
        except:
            return False

    def is_overload(self):
        try:
            element = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, 
                "//div[contains(@class, 'css-146c3p1') and contains(text(), 'Overload Auction')]"
                ))
            )
            return True
        except TimeoutException:
            return False

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def connect_to_database(db_config):
    connection = mysql.connector.connect(**db_config)
    if connection:
        cursor = connection.cursor()
        print("Database connection successful")
    else:
        raise Exception("Failed to setup database connection")
    return connection

def get_auction_info(url, driver, db_config):
    driver.get(url)
    auction_info = AuctionInfo(url, driver, db_config)
    auction_info.get_auction_info()
    duration = 1
    for _ in range(duration + 1):
            print(f"\rMonitoring starts in {duration - _} seconds", end='', flush=False)
            time.sleep(1)
    print("\rInitializing auction monitor...")

def run_monitor(url, driver, db_config):
    driver.get(url)
    current_date = date.today()
    auction_web_identifier = url.split("/")[-1]
    monitor = AuctionMonitor(url, driver, db_config)
    print('\rMonitoring initialized successfully!')
    print('\rStarting monitoring...')
    print('----------------------------------------')
    monitor.start_monitorinig_auction()

def monitor_auction_thread(url, db_config):
    driver = setup_driver()
    try:
        get_auction_info(url, driver, db_config)
        run_monitor(url, driver, db_config)
    finally:
        driver.quit()

def process_new_url(url, db_config):
    thread = threading.Thread(target=monitor_auction_thread, args=(url, db_config))
    thread.start()
    time.sleep(1)
    return thread

def schedule_auction_monitor(url, db_config, schedule_time):
    def job():
        process_new_url(url, db_config)
        return schedule.CancelJob
    schedule.every().day.at(schedule_time).do(job)
    print(f"Scheduled auction monitor for {schedule_time}")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "Abis225588", 
        "database": "auctions_schema"
    }
    threads = []    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    print("Enter URLs to monitor. You can schedule them for later processing.")
    print("Format: <URL> [YYYY-MM-DD HH:MM]")
    print("If no date/time is provided, the URL will be processed immediately.")
    print("Enter 'quit' to exit the program.")

    try:
        while True:
            user_input = input("Enter URL and optional schedule: ").strip()
            if user_input.lower() == 'quit':
                break
            
            parts = user_input.split()
            if len(parts) >= 1:
                url = parts[0]
                if len(parts) == 3:
                    # Schedule for later
                    try:
                        scheduled_time = datetime.strptime(f"{parts[1]} {parts[2]}", "%Y-%m-%d %H:%M")
                        if scheduled_time > datetime.now():
                            schedule_auction_monitor(url, db_config, parts[2])
                        else:
                            print("Scheduled time is in the past. Processing immediately.")
                            thread = process_new_url(url, db_config)
                            threads.append(thread)
                    except ValueError:
                        print("Invalid date/time format. Use YYYY-MM-DD HH:MM")
                else:
                    # Process immediately
                    thread = process_new_url(url, db_config)
                    threads.append(thread)
                    print(f"Started monitoring: {url}")
            else:
                print("Invalid input. Please enter a valid auction URL.")


    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
    finally:
        print("Waiting for all monitoring threads to complete...")
        for thread in threads:
            thread.join()
        print("All monitoring threads have completed. Program exiting.")
if __name__ == "__main__":  
    main()