import requests
import numpy as np
import pandas as pd
from typing import List

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

def saveDataFrame2CSV(df: pd.DataFrame, save_path: str, sep: str = ',', encoding: str = 'utf-8') -> bool:
    """Hàm lưu DataFrame thành dạng file CSV

    Args:
        save_path (str): Đường dẫn chứa tên tập tin cần lưu, ví dụ: "data/save.csv"
        sep (str, optional): Ký tự phân chia các đặc trưng trong file csv. Defaults to ','.
        encoding (str, optional): . Defaults to 'utf-8'.

    Returns:
        bool: True
    """
    try:
        df.to_csv(save_path, sep=sep, encoding=encoding, index=False)
    except:
        raise ModuleNotFoundError
        # return False
    return True
