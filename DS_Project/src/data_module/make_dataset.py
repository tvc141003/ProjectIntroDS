import subprocess
import requests
import numpy as np
import pandas as pd
from typing import List
from bs4 import BeautifulSoup

from typing import List, Dict
import os
import re
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import concurrent.futures

import os
import pandas as pd

# Kiểm tra robots.txt để xác định xem có cho phép thu thập dữ liệu hay không.
import urllib.robotparser

def check_robots_txt(url: str) -> bool:
    """Hàm kiểm tra robots.txt để xác định xem có cho phép thu thập dữ liệu hay không.

    Args:
        url (str): Đường dẫn robots.txt

    Returns:
        bool: True nếu được phép thu thập dữ liệu, False nếu không được phép.
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(url)
    rp.read()
    return rp.can_fetch("*", url)

def pathExists(path: str) -> bool:
    """Hàm kiểm tra đường dẫn có tồn tại hay không

    Args:
        path (str): Đường dẫn

    Returns:
        bool: True nếu tồn tại, False nếu không tồn tại
    """
    import os.path
    return os.path.exists(path)

def saveCSV2DataFrame(url: str, sep: str = ',', encoding: str = 'utf-8') -> pd.DataFrame:
    """Hàm lưu file csv từ url thành DataFrame

    Args:
        url (str): Đường dẫn file csv
        sep (str, optional): Ký tự phân chia các đặc trưng trong file csv. Defaults to ','.
        encoding (str, optional): . Defaults to 'utf-8'.

    Returns:
        pd.DataFrame: DataFrame
    """
    if pathExists(url):
        try:
            df = pd.read_csv(url, sep=sep, encoding=encoding)
        except:
            raise ModuleNotFoundError
            # return None
    else:
        raise FileNotFoundError
        # return None
    return df






def getUrls(url: str, max_range: int) -> List[str]:
    """Hàm lấy danh sách url từ sitemap

    Args:
        url (str): Đường dẫn sitemap

    Returns:
        List[str]: Danh sách url
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml-xml')  # Use 'lxml-xml' parser
    loc_tags = soup.find_all('loc')
    
    result = [loc_tag.text.strip() for i, loc_tag in enumerate(loc_tags) if i < max_range]
            
    return result
    

def writeListToFile(list: List[str], path: str) -> None:
    """Hàm ghi danh sách url vào file

    Args:
        list (List[str]): Danh sách url
        path (str): Đường dẫn file
    """
    with open(path, 'w') as f:
        for item in list:
            f.write("%s\n" % item)

def readListFromFile(path: str) -> List[str]:
    """Hàm đọc danh sách url từ file

    Args:
        path (str): Đường dẫn file

    Returns:
        List[str]: Danh sách url
    """
    with open(path, 'r') as f:
        result = f.readlines()
    return result



def extractInfoFromUrl(driver) -> Dict[str, List[str]]:
    selectors = {
        'rating': '.game-header-title-rating',
        'title': '.game-header-title-info h1',
        'description': '.game-header-title-info p',
        'items': '.gameplay-item .gameplay-item-primary',
        'summary': '.game-header-title-info .game-header-title-summary a',
        'credits': '.game-header-credits.hidden-game-header-collapsed li',
        'classification header': '.game-description-classification.well.ng-scope .features .feature-title.ng-binding',
        'classification': '.game-description-classification.well.ng-scope .features .feature-description'
    }

    elems = {key: [elem.text.strip() for elem in driver.find_elements(By.CSS_SELECTOR, selector)] for key, selector in selectors.items()}

    return elems

def extractTitleInfo(text):
    pattern = re.compile(r'(.*)\s\((\d{4})\)')
    match = pattern.match(text)
    return match.groups() if match else (None, None)

def extractSummaryInfo(summary):
    result = []
    
    pattern = re.compile(r'(\d+(\.\d+)?)([KM]?)', re.IGNORECASE)
    for i in range(2):
        match = pattern.match(summary[i])
        if match:
            number = float(match.group(1))
            multiplier = {'K': 1000, 'M': 1000000}.get(match.group(3).upper(), 1)
            result.append(int(number * multiplier))
        else:
            result.append(None)
    return tuple(result)

def extractComplexityRatingInfo(text):
    pattern = re.compile(r'(\d+(\.\d+)?) / (\d+)')
    match = pattern.search(text)
    return float(match.group(1)) if match else None

def extractRangeInfo(text):
    pattern = re.compile(r'(\d+)(?:–(\d+))?')
    match = pattern.match(text)
    if match:
        min_range = int(match.group(1))
        max_range = int(match.group(2)) if match.group(2) else min_range
        return min_range, max_range
    return None, None

def extractCreditsInfo(credits):
    fields = ['Designer', 'Artist', 'Publisher']
    result = {field: '' for field in fields}
    
    for credit in credits:
        test = credit.split(' ')
        if test[0] in fields:
            credit = credit.removeprefix(f'{test[0]} ').split(', ')
            result[test[0]] = ', '.join(credit)
    return tuple(result.values())
    
def extractNumber(text):
    pattern = re.compile(r'\d+')
    match = pattern.search(text)
    return int(match.group(0)) if match else None

def extractClassificationInfo(classification, classification_header):
    fields = ['Type', 'Category', 'Mechanism', 'Family']
    result = {field: '' for field in fields}
    
    for i, header in enumerate(classification_header):
        if header in fields:
            if header == 'Type':
                result[header] = ', '.join(classification[i].split('\n')[0:-1])
            else:
                result[header] = ', '.join(classification[i].split('\n'))
                
    return tuple(result.values())

def processInfoFromUrl(elems: Dict[str, List[str]]) -> Dict[str, List[str]]:
    average_rating = float(elems['rating'][1])
    name, year = extractTitleInfo(elems['title'][1])
    description = elems['description'][0]
    designer, artist, publisher = extractCreditsInfo(elems['credits'])
    min_players, max_players = extractRangeInfo(elems['items'][0])
    min_playtime, max_playtime = extractRangeInfo(elems['items'][1])
    playing_time = (min_playtime + max_playtime) / 2 if min_playtime and max_playtime else None
    min_age = extractNumber(elems['items'][2])
    complexity_rating = extractComplexityRatingInfo(elems['items'][3])
    user_ratings, user_comments = extractSummaryInfo(elems['summary'])
    type, category, mechanism, family = extractClassificationInfo(elems['classification'], elems['classification header'])
    
    result = {
        'average_rating': average_rating,
        'name': name,
        'year': year,
        'description': description,
        'designer': designer,
        'artist': artist,
        'publisher': publisher,
        'min_players': min_players,
        'max_players': max_players,
        'min_playtime': min_playtime,
        'max_playtime': max_playtime,
        'playing_time': playing_time,
        'min_age': min_age,
        'complexity_rating': complexity_rating,
        'user_ratings': user_ratings,
        'user_comments': user_comments,
        'type': type,
        'category': category,
        'mechanism': mechanism,
        'family': family
    }

    return result


def process_url(url, chrome_options):
    try:
        with Chrome(options=chrome_options) as driver:
            driver.get(url)
            driver.implicitly_wait(3)
            elems = extractInfoFromUrl(driver)
            result = processInfoFromUrl(elems)
            return result
    except Exception as e:
        print(f"Error processing URL: {url}, skipping... {e}")
        return None
    finally:
        driver.quit()

def collect_data(urls, chrome_options):
    fields = ['name', 'description', 'designer', 'artist', 'publisher', 'min_players', 'max_players', 
              'min_playtime', 'max_playtime', 'playing_time', 'min_age', 'complexity_rating', 'user_ratings', 'user_comments', 
              'type', 'category', 'mechanism', 'family', 'year', 'average_rating']

    data = {field: [] for field in fields}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_url, url, chrome_options): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                for field in fields:
                    data[field].append(result[field])

    return data

import time

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    for i in range(1, 2):
        boardgame_urls = readListFromFile(f'./data/external/boardgame_urls/boardgame_urls_page_{i}.txt')
        start_time = time.time()
        data = collect_data(boardgame_urls, chrome_options)
        elapsed_time = time.time() - start_time

        pd.DataFrame(data).to_csv(f'./data/raw/raw_data_page_{i}.csv', index=False)

        print(f"Elapsed time: {elapsed_time} seconds")

    print("Done!")

if __name__ == '__main__':
    main()
                       
    # sitemap_url = 'https://boardgamegeek.com/sitemapindex'
    # page_urls = getUrls(sitemap_url, 16)
    # writeListToFile(page_urls, './data/external/sitemapindex.txt')
    
    # for page_url in page_urls:
    #     page_number = page_url.split('/')[-1].split('_')[-1]
    #     urls = getUrls(page_url, 500)
    #     writeListToFile(urls, f'./data/external/boardgame_urls/boardgame_urls_page_{page_number}.txt')
    #     print(f'boardgame_urls_page_{page_number}... Done!')

    