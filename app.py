"""
Module: namshi_scraper

This module contains the `NamshiScrape` class designed for scraping product information from the Namshi website.
It uses Selenium WebDriver to interact with the website and Pandas to manage and store the scraped data.

Dependencies:
- os
- pandas
- selenium
- webdriver_manager

Usage:
1. Create an instance of `NamshiScrape` with the URL of the Namshi page to scrape.
2. Call `main_page_product_links_scrape_to_csv()` to scrape product links from the main page and save them to a CSV file.
3. Call `scrape_links()` to scrape detailed product information from the links saved in the CSV file.

Example:
    from namshi_scraper import NamshiScrape

    # Initialize the scraper with the URL
    url = 'https://www.namshi.com/saudi-en/kids/'
    scraper = NamshiScrape(url)

    # Scrape product links from the main page and save to CSV
    scraper.main_page_product_links_scrape_to_csv()

    # Scrape product details from the links and save to CSV
    scraper.scrape_links()

"""



import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from locators.xpath_locator import Locators
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException

url = 'https://www.namshi.com/saudi-en/kids/'

class NamshiScrape:
    """
    Class `NamshiScrape`:
    
    A class for scraping product information from the Namshi website.
    
    Attributes:
        url (str): URL of the Namshi page to scrape.
        wait (int): wait time(default is 5 seconds).
        driver (webdriver.Chrome): Selenium WebDriver instance.
        first_page_links (list): List to store URLs of products on the main page.
        failed_url_index (int): Index of the last failed URL for retrying.



    Methods:

        __init__(self, url, wait=10):
            Initializes the `NamshiScrape` instance with the URL and optional wait time.

        create_driver(self):
            Creates and initializes a Selenium WebDriver instance with Chrome options.

        main_page_product_links_scrape_to_csv(self, file_name='main_page_url_links.csv'):
            Scrapes product links from the main page and saves them to a CSV file.

        write_to_csv(self, data, file_name='product_info.csv'):
            Writes or appends data to a CSV file.

        scrape_links(self, file_name='main_page_url_links.csv'):
            Scrapes detailed product information from URLs listed in the CSV file and saves the data to another CSV file.


    """
    def __init__(self, url, wait=5):
        self.options = webdriver.ChromeOptions()
        #uncomment to add headless mode
        # self.options.add_argument('--headless')
        self.options.add_experimental_option('detach', True)
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.url = url
        self.wait = wait
        self.driver = None
        self.first_page_links = []
        self.failed_url_index = None

        

    def create_driver(self):
        """
        Creates and initializes a Selenium WebDriver instance with Chrome options.
        """

        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver.implicitly_wait(self.wait)

    def main_page_product_links_scrape_to_csv(self, file_name='main_page_url_links.csv'):
        try:
            if not self.driver:
                self.create_driver()
            self.driver.get(self.url)
            element_box = self.driver.find_elements(By.XPATH, Locators.MAIN_PAGE_LINKS_LOCATORS)
            
            for element_link in element_box[:10]:  # Scraping the first ten product links
                self.first_page_links.append({"url": element_link.get_attribute('href')})

            if not os.path.exists(file_name):
                main_page_url_links = pd.DataFrame(self.first_page_links)
                main_page_url_links.to_csv(file_name, index=False)
                print(main_page_url_links)
            else:
                print(self.first_page_links)

        except Exception as error:
            print(error)
        finally:
            if self.driver:
                self.driver.quit()

    def write_to_csv(self, data, file_name='product_info.csv'):
        """
        Writes or appends data to a CSV file.

        Parameters:
            data (list of dict): Data to be written to the CSV file.
            file_name (str): Name of the CSV file to write data (default is 'product_info.csv').
        """
        new_dataframe = pd.DataFrame(data)
        if os.path.exists(file_name):
            dataFrame = pd.read_csv(file_name)
            combined_data = pd.concat([dataFrame, new_dataframe], ignore_index=True)
            combined_data.to_csv(file_name, index=False)
            print(combined_data)
        else:
            new_dataframe.to_csv(file_name, index=False)
            print(new_dataframe)

    def scrape_links(self,file_name='main_page_url_links.csv'):
        '''
        Scrapes detailed product information from URLs listed in the CSV file and saves the data to another CSV file.

        Parameters:
            file_name (str): Name of the CSV file that contains the product links (default is 'main_page_url_links.csv').

        Raises:
            Exception: If the CSV file with URLs does not exist.
        
        '''


        if not os.path.exists(file_name):
            raise Exception('You need to call the main_page_product_links_scrape_to_csv() method first.')
        
        #List for collecting product information pages
        product_info_list = []
        try:
            url_list = pd.read_csv(file_name)['url']
            if not self.driver:
                self.create_driver()
            if self.failed_url_index:
                url_list = pd.read_csv(file_name)['url'][self.failed_url_index:]

            for index,url in enumerate(url_list):

                try:
                    print('Getting the url: ',url)
                    self.driver.get(url)
                    import time
                    time.sleep(self.wait)

                    product_block = self.driver.find_elements(By.XPATH, Locators.PRODUCT_ALL_DETAILS_LOCATOR)

                    product_info_dict = {
                        'Brand': None,
                        'Product_Name': None,
                        'Price_After_Discount': None,
                        'Price_Before_Discount': None,
                        'Image_Links': [],
                        'Description': [],
                        'Sizes-Stock-Normal': [],
                        'Size-Low-Stock': [],
                        'Size-Out-Of-Stock':[],
                        'Category': None,
                    }

                    for product in product_block:
                        print('finding and creating the product_info data: brand,name,pad,pbd...')
                        brand = product.find_element(By.XPATH, Locators.BRAND).text
                        name = product.find_element(By.XPATH, Locators.NAME).text
                        pad = product.find_element(By.XPATH, Locators.PRICE_AFTER_DISCOUNT).text
                        pbd = product.find_element(By.XPATH, Locators.PRICE_BEFORE_DISCOUNT).text

                        product_info_dict['Brand'] = brand
                        product_info_dict['Product_Name'] = name
                        product_info_dict['Price_After_Discount'] = pad
                        product_info_dict['Price_Before_Discount'] = pbd

                    sizes = product.find_elements(By.XPATH, Locators.SIZE_CONTAINER)
                    for button_array in sizes:
                        print('finding and add stock_information...')
                        for out_of_stock in button_array.find_elements(By.XPATH,Locators.OUT_OF_STOCK):
                            product_info_dict['Size-Out-Of-Stock'].append(out_of_stock.text)

                        for lowsock_size in button_array.find_elements(By.XPATH, Locators.BUTTON_LOW_STOCK_ARRAY):
                            product_info_dict['Size-Low-Stock'].append(lowsock_size.text)

                        for size in button_array.find_elements(By.XPATH, Locators.BUTTON_NORMAL_STOCK):
                            product_info_dict['Sizes-Stock-Normal'].append(size.text)

                    product_images_block = self.driver.find_elements(By.XPATH, Locators.IMAGE_CONTAINER)
                    for element in product_images_block:
                        print('finding and adding product image_links...')
                        for image in element.find_elements(By.TAG_NAME, 'img'):
                            product_info_dict['Image_Links'].append(image.get_attribute('src'))

                    categories = self.driver.find_elements(By.XPATH, Locators.CATEGORY_CONTAINER)
                    category_string = ''
                    print('finding the category information')
                    for element in categories:
                        for category in element.find_elements(By.TAG_NAME, 'a'):
                            if category.text == 'Home':
                                continue
                            category_string += category.text + '/'
                    product_info_dict['Category'] = category_string

                    print('finding product description...')
                    self.driver.find_element(By.XPATH, Locators.PRODUCT_HIGHLIGHTS_BUTTON).click()
                    
                    description_element = self.driver.find_elements(By.XPATH, Locators.PRODUCT_CORE_DETAILS)
                    description_list = [detail.text.strip('\n') for detail in description_element]
                    product_info_dict['Description'] = ','.join(description_list)


                    product_info_list.append(product_info_dict)
                   

                except NoSuchElementException as e:
                    self.failed_url_index = index
                    
                    print(f"Error processing URL {url}: {e},continuing would try to process again")
                except Exception as e:
                    self.failed_url_index = index
                    print(f"Error processing URL {url}: {e},continuing would try to process again")
            
            
        
        except Exception as error:
            print(error)
            if self.failed_url_index:
                print('trying to processs failed urls')
                return self.scrape_links()

        
        finally:
            self.write_to_csv(product_info_list)
            print('write to csv done.')
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    # Usage
    Scraper = NamshiScrape(url)
    # Scraper.main_page_product_links_scrape_to_csv()
    Scraper.scrape_links()
