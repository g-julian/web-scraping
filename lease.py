import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import shutil

load_dotenv()
cookies_str = os.getenv('COOKIES')
cookies = json.loads(cookies_str)

header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/131.0.0.0 Safari/537.36",

}

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--remote-allow-origins=*")
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option('detach', False)

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://www.texas-drilling.com')

for name, value in cookies.items():
    driver.add_cookie({'name': name, 'value': value})

anchor_tag = driver.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
links = [tag.get_attribute('href') for tag in anchor_tag]

# Getting each county link from the highest county table
for ref in links:
    driver.get(ref)
    time.sleep(3)

#Creating a folder for the counties
    folder_name = driver.find_element(By.CSS_SELECTOR, 'li.current').text
    parent_folder = Path(folder_name)

#Getting the top operators in the county
    top_ops_in_county_x = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[4]/div[1]/div[1]/div[2]/ul')
    top_ops_in_county_tag = top_ops_in_county_x.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
    top_ops_in_county_link = [anchor.get_attribute('href') for anchor in top_ops_in_county_tag]

#Going to each operator and getting their leases
    for portal in top_ops_in_county_link:
        driver.get(portal)
        response = requests.get(portal)
        response.raise_for_status()
        page = response.content

        soup = BeautifulSoup(page, 'html.parser')
        tables = soup.find('table')
        a_tag = tables.find_all('a')
        lease_link = [link['href'] for link in a_tag]

#Setting the sub folders
        sub_title = soup.find('h1', class_='sepH_c').text
        first_sub = parent_folder / f'{sub_title}'
        sub_folder = parent_folder / f'{sub_title}' / 'Leases'
        sub_folder.mkdir(parents=True, exist_ok=True)

# Going through every lease to get Well information
        for item in lease_link:

            driver.get(item)

            well_data = []

            soup2 = BeautifulSoup(driver.page_source, 'html.parser')
            title = soup2.find(name='li', class_='current').text.split(',')[0].replace('/', '_').replace('|',
                                                                                                         '_').replace(
                '"', '')
            tables = soup2.find_all('table')
            well_table = tables[len(tables) - 1]

            content = well_table.find_all('tr')

            for row in content:
                cells = row.find_all('td')
                data = [cell.text for cell in cells]
                well_data.append(data)

            filtered_data = []
            for lst in well_data:
                if lst:
                    filtered_data.append(lst)

            api = []
            well_name = []
            well_type = []
            complete = []
            status = []

            for info in filtered_data:
                api.append(info[0])
                well_name.append(info[1])
                well_type.append(info[2])
                complete.append(info[3])
                status.append(info[4])

            diction_3 = {
                'API Number': api,
                'Well Name': well_name,
                'Well Type': well_type,
                'Completion Date': complete,
                'Status': status
            }

            first_table = soup2.find_all('table')
            summary_table = first_table[0]

            inside = summary_table.find_all('tr')
            summary_list = []

            for row in inside:
                cells = row.find_all('td')
                data = [cell.text for cell in cells]
                summary_list.append(data)

            county = summary_list[0]
            lease = summary_list[1]
            operator = summary_list[2]
            pro_dates = summary_list[3]
            total_oil = summary_list[4]
            total_gas = summary_list[5]
            oil_pro = summary_list[6]
            gas_pro = summary_list[7]
            well = summary_list[8]

            diction4 = {
                'County': county,
                'Lease#': lease,
                'Operator': operator,
                'Production Dates': pro_dates,
                'Total Oil Production': total_oil,
                'Total Gas Production': total_gas,
                'Recent Oil Prod.': oil_pro,
                'Recent Gas Prod.': gas_pro,
                'Wells on Lease': well
            }
            dc = pd.DataFrame(diction4)
            dc.to_excel(f'{title}.xlsx', index=False)
            file_name = f'{title}.xlsx'

            df = pd.DataFrame(diction_3)
            with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
                df.to_excel(writer, sheet_name='Wells Located on Lease', index=False)

            file_to_move = Path(file_name)
            destination_path = sub_folder / file_to_move.name

            shutil.move(str(file_to_move), str(destination_path))
