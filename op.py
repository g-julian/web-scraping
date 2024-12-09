import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import json
from dotenv import load_dotenv

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
chrome_options.add_experimental_option('detach', True)

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://www.texas-drilling.com')

for name, value in cookies.items():
    driver.add_cookie({'name': name, 'value': value})

anchor_tag = driver.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
links = [tag.get_attribute('href') for tag in anchor_tag]

#iterating through highest county links
for link in links:
    driver.get(link)
    time.sleep(3)
    top_ops_in_county_x = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[4]/div[1]/div[1]/div[2]/ul')
    top_ops_in_county_tag = top_ops_in_county_x.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
    top_ops_in_county_link = [anchor.get_attribute('href') for anchor in top_ops_in_county_tag]

# iterating through each operator
    for ref in top_ops_in_county_link:
        driver.get(ref)
        first_data = []
        title = driver.find_element(By.CSS_SELECTOR, 'li.current').text
        while True:
            table = driver.find_elements(By.TAG_NAME, 'table')
            lo_table = table[len(table) - 2]

            content = lo_table.find_elements(By.TAG_NAME, 'tr')

            for row in content:
                cells = row.find_elements(By.TAG_NAME, 'td')
                data = [cell.text for cell in cells]
                first_data.append(data)

            try:
                next_button = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[3]/div[2]/div/div[4]/span[4]')
                if '_disabled' in next_button.get_attribute('class'):
                    break
                next_button.click()

            except:
                break

        lease_filtered = []
        for lst in first_data:
            if lst:
                lease_filtered.append(lst)
        # print(lease_filtered)
        lease_numbers = []
        lease_name = []
        county = []

        for sublist in lease_filtered:
            lease_numbers.append(sublist[0])
            lease_name.append(sublist[1])
            county.append(sublist[2])

        diction = {
            'Lease No.': lease_numbers,
            'Lease Name': lease_name,
            'County': county
        }

        df = pd.DataFrame(diction)
        df.to_excel(f'{title}.xlsx', index=False)

        second_data = []
        while True:
            table = driver.find_elements(By.TAG_NAME, 'table')
            dp_table = table[len(table) - 1]

            content = dp_table.find_elements(By.TAG_NAME, 'tr')

            for row in content:
                cells = row.find_elements(By.TAG_NAME, 'td')
                data = [cell.text for cell in cells]
                second_data.append(data)

            try:
                next_button = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[3]/div[4]/div/div[4]/span[4]')
                if '_disabled' in next_button.get_attribute('class'):
                    break
                next_button.click()

            except:
                break

        # print(second_data)
        second_filter = []
        for li in second_data:
            if li:
                second_filter.append(li)
        # print(second_filter)

        submitted = []
        approved = []
        well = []
        county_permit = []
        status = []

        for sub in second_filter:
            submitted.append(sub[0])
            approved.append(sub[1])
            well.append(sub[2])
            county_permit.append(sub[3])
            status.append(sub[4])

        diction_2 = {
            'Submitted': submitted,
            'Approved': approved,
            'Well': well,
            'County': county_permit,
            'Status': status

        }
        dh = pd.DataFrame(diction_2)
        with pd.ExcelWriter(f'{title}.xlsx', engine='openpyxl', mode='a') as writer:
            dh.to_excel(writer, sheet_name='Drilling_Permits', index=False)

        contacts = driver.find_element(By.CLASS_NAME, 'box_c_content')
        test = (contacts.text.replace('\n', ' ').split(':'))
        all_info = [word.replace('Address', '').replace('Phone', '').replace('Company Name', '') for word in test]
        name = all_info[1]

        address = all_info[2]

        phone = all_info[3]

        diction_3 = {
            'Company Name': name,
            'Address': address,
            'Phone': [phone]
        }

        ch = pd.DataFrame(diction_3)
        with pd.ExcelWriter(f'{title}.xlsx', engine='openpyxl', mode='a') as writer:
            ch.to_excel(writer, sheet_name='Contact Info', index=False)
