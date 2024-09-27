import mysql.connector
from mysql.connector import Error
import time
def create_database_and_tables(db_config):
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS NAME OF DATABASE")
            cursor.execute("USE NAME OF DATABASE")
            
            # Create auctions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS auctions (
                unique_identifier VARCHAR(255) PRIMARY KEY,
                item_name VARCHAR(255),
                buy_it_now_price DECIMAL(10, 2),
                no_jumper_limit FLOAT,
                is_runner_up_discount BOOLEAN DEFAULT False,
                is_no_reentry BOOLEAN DEFAULT False,
                is_tripple_booked BOOLEAN DEFAULT False,
                is_sold BOOLEAN DEFAULT False
            )
            """)
            
            # Create bids table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bids (
                unique_identifier VARCHAR(255),
                highest_bid DECIMAL(10, 2),
                bidder_name VARCHAR(255),
                bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create bidders table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bidders (
                bidder_name VARCHAR(255) PRIMARY KEY,
                bidder_location VARCHAR(255),
                join_date DATE
            )
            """)
                
            print("Database and tables created successfully")
            return connection
        
    except Error as e:
        print(f"Error: {e}")
        return None

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "********"
}

create_database_and_tables(db_config)