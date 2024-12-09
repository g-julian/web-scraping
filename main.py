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
chrome_options.add_experimental_option('detach', False)

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://www.texas-drilling.com')

for name, value in cookies.items():
    driver.add_cookie({'name': name, 'value': value})

anchor_tag = driver.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
links = [tag.get_attribute('href') for tag in anchor_tag]
# print(links)

# iterating through the links to scrape the data
for link in links:
    driver.get(link)
    time.sleep(3)

    title = driver.find_element(By.CSS_SELECTOR, 'li.current').text

    top_operator_xpath = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[4]/div[1]/div[1]/div[2]/ul')
    top_op_anchor_tags = top_operator_xpath.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
    top_ops_list = [anchor.text for anchor in top_op_anchor_tags]
    # print(top_ops_list)

    top_lease_xpath = driver.find_element(By.XPATH, '//*[@id="main_content"]/div[4]/div[1]/div[2]/div[2]/ul')
    top_lease_anchor_tag = top_lease_xpath.find_elements(By.CSS_SELECTOR, 'a.sepV_b')
    top_lease_list = [anc.text for anc in top_lease_anchor_tag]
    # print(top_lease_list)

    summary = driver.find_element(By.CSS_SELECTOR,'ul.summary_list')
    li_list = summary.find_elements(By.TAG_NAME, 'li')
    separate = [li.text.split(' ', 1) for li in li_list]
    # print(separate)

    diction = {
        'Top Producing Operators': pd.Series(top_ops_list),
        'Top Producing Leases': pd.Series(top_lease_list),
    }

    summary_diction = {
        separate[0][1]: [separate[0][0]],
        separate[1][1]: [separate[1][0]],
        separate[2][1]: [separate[2][0]],
        separate[3][1]: [separate[3][0]],
        separate[4][1]: [separate[4][0]],
    }
    # print(summary_diction)

    df = pd.DataFrame(diction)
    df.to_excel(f'{title}.xlsx', index=False)

    dh = pd.DataFrame(summary_diction)
    with pd.ExcelWriter(f'{title}.xlsx', engine='openpyxl', mode='a') as writer:
        dh.to_excel(writer, sheet_name='Summary', index=False)


# Attempt to get json data with map coordinates
# driver.get(f '{link}'+ '?json')
# soup = BeautifulSoup(driver.page_source, 'html.parser')
#
# response = requests.get(anderson_link + '?json')
# data = response.json()
#
# with open(f'{title}.txt','w') as file:
#     json.dump(data, file, indent=4)


