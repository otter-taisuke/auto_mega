import argparse
import glob
import os
import time

from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_QUERY = "query.txt"


class DownloadTimeoutException(Exception):
    pass


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="automation: clustalw")
    parser.add_argument("-s", "--simple", action="store_true")
    parser.add_argument("-q", "--query", default=DEFAULT_QUERY)
    args = parser.parse_args()
    return args


def load_input(path: str) -> list[str] | None:
    ext = os.path.splitext(path)[1]
    inputs: list[str] | None = None
    if ext == ".txt":
        for enc in ["utf-8", "shift-jis", "cp932"]:
            try:
                with open(path, "r", encoding=enc) as f:
                    inputs = f.read().splitlines()
                break
            except UnicodeDecodeError:
                continue
    else:
        print("Error: Not supported except text files for inputs.")
        return None
    if inputs is None:
        print(f"Error: Could not load \"{os.path.basename(path)}\" in utf-8, shift-jis, cp932.")
        return None
    return inputs


def open_new_browser(download: str) -> webdriver.chrome:
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download}
    chrome_options.add_experimental_option("prefs", prefs)
    browser = webdriver.Chrome(options=chrome_options)
    return browser


def wait_by_xpath(browser: webdriver.chrome, xpath: str, limit: int = 20):
    wait = WebDriverWait(browser, limit)
    wait.until(EC.presence_of_element_located((By.XPATH, xpath)))


def run_clustalw(browser: webdriver.chrome, file_path: str):
    wait_by_xpath(browser, "//table[@class=\"frame2\"]")
    file_input = browser.find_elements(By.XPATH, "//input[@type=\"file\"]")[0]
    file_input.send_keys(file_path)
    run_button = browser.find_elements(By.XPATH, "//input[@value=\"Execute Multiple Alignment\"]")[0]
    run_button.click()
    wait_by_xpath(browser, "//form[@name=\"tree\"][2]", 300)


def wait_download(path: str, limit: int = 120):
    for i in range(limit):
        if os.path.exists(path):
            return
        else:
            time.sleep(1)
    raise DownloadTimeoutException


def downlaod_result(browser: webdriver.chrome, download: str, organism: str):
    dnd_link = browser.find_elements(By.XPATH, "//a[contains(text(), \"clustalw.dnd\")]")[2]
    dnd_link.click()
    raw_path = os.path.join(download, "clustalw.dnd")
    result_path = os.path.join(download, organism + ".dnd")
    wait_download(raw_path)
    os.rename(raw_path, result_path)


def auto_clustalw(args):
    if args.simple:
        query_list = [input("Enter Query Seq :")]
    else:
        query_list = load_input(os.path.join(ROOT, args.query))
    if args.simple and (query_list[0] == ""):
        print("Error: Incomplete input information.")
    elif not args.simple and (query_list is None):
        print("Error: Incomplete input information.")
    for query in query_list:
        blast_result = os.path.join(ROOT, "blastp", query)
        result_list = glob.glob(os.path.join(blast_result, "*.txt"))
        download = os.path.join(ROOT, "clustalw", query)
        os.makedirs(download, exist_ok=True)
        browser = open_new_browser(download)
        for txt_path in tqdm(result_list, desc=f"Now run clustalw about {query}"):
            organism = os.path.splitext(os.path.basename(txt_path))[0]
            try:
                browser.get("https://www.genome.jp/tools-bin/clustalw")
                run_clustalw(browser, txt_path)
                downlaod_result(browser, download, organism)
            except TimeoutException:
                tqdm.write(f"Timeout: Runtime in <{query}-{organism}> clustalw is too long.")
                with open(os.path.join(ROOT, "clustalw", f"{query} - error.txt"), mode="a") as f:
                    f.write(organism + "\n")
                continue
            except DownloadTimeoutException:
                tqdm.write(f"Timeout: Download time has exceeded the limit.({query}-{organism})")
                continue


if __name__ == "__main__":
    args = get_arguments()
    auto_clustalw(args)
