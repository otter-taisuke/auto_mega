import argparse
import os
import time

from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ORGANISM = "organism.txt"
DEFAULT_QUERY = "query.txt"


class DownloadTimeoutException(Exception):
    pass


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="automation: blastp")
    parser.add_argument("-s", "--simple", action="store_true")
    parser.add_argument("-o", "--organism", default=DEFAULT_ORGANISM)
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


def open_new_blastp(download: str) -> webdriver.chrome:
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download}
    chrome_options.add_experimental_option("prefs", prefs)
    browser = webdriver.Chrome(options=chrome_options)
    browser.get("https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastp&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome")
    return browser


def wait_by_xpath(browser: webdriver.chrome, xpath: str, limit: int = 20):
    wait = WebDriverWait(browser, limit)
    wait.until(EC.presence_of_element_located((By.XPATH, xpath)))


def run_alignment(browser: webdriver.chrome, query: str, organism: str):
    wait_by_xpath(browser, "//div[@id=\"wrap\"]")
    query_box = browser.find_elements(By.XPATH, "//textarea[@id=\"seq\"]")
    query_box[0].send_keys(query)
    organism_input = browser.find_elements(By.XPATH, "//input[@id=\"qorganism\"]")
    organism_input[0].send_keys(organism)
    wait_by_xpath(browser, "//li[@role=\"menuitem\"]")
    suggested_organism = browser.find_elements(By.XPATH, "//li[@role=\"menuitem\"]")
    suggested_organism[0].click()
    run_button = browser.find_elements(By.XPATH, "//input[@class=\"blastbutton\"]")
    time.sleep(1)  # care delay/lag
    run_button[0].click()
    wait_by_xpath(browser, "//main[@class=\"results content blastp\"]", 300)


def wait_download(path: str, limit: int = 120):
    for i in range(limit):
        if os.path.exists(path):
            return
        else:
            time.sleep(1)
    raise DownloadTimeoutException


def download_result(browser: webdriver.chrome, download: str, organism: str):
    download_selector = browser.find_elements(By.XPATH, "//button[@class=\"usa-accordion-button usa-nav-link toolsCtr\"]")
    download_selector[0].click()
    wait_by_xpath(browser, "//a[contains(text(), \"FASTA (completesequence)\")]")
    fasta_download = browser.find_elements(By.XPATH, "//a[contains(text(), \"FASTA (completesequence)\")]")
    action = ActionChains(browser).move_to_element(fasta_download[0])
    action.click()
    action.perform()
    # fasta_download[0].click()
    raw_path = os.path.join(download, "seqdump.txt")
    result_path = os.path.join(download, organism + ".txt")
    wait_download(raw_path)
    os.rename(raw_path, result_path)


def auto_blastp(args: argparse.Namespace):
    query_list: list[str] | None = None
    organism_list: list[str] | None = None
    if args.simple:
        query_list = [input("Enter Query Seq :")]
    else:
        query_list = load_input(os.path.join(ROOT, args.query))
    organism_list = load_input(os.path.join(ROOT, args.organism))
    if query_list is None or organism_list is None:
        print("Error: Incomplete input information.")
    for query in query_list:
        download = os.path.join(ROOT, "blastp", query)
        os.makedirs(download, exist_ok=True)
        blastp = open_new_blastp(download)
        for organism in tqdm(organism_list, desc=f"Now searching <{query}> similarity..."):
            try:
                run_alignment(blastp, query, organism)
                download_result(blastp, download, organism)
            except NoSuchElementException:
                tqdm.write(f"{organism} has no similar seq with {query}.")
                continue
            except DownloadTimeoutException:
                tqdm.write(f"Timeout: Download time has exceeded the limit.({query}-{organism})")
                continue
            # except:
            #     tqdm.write("Error: Unknown error.")
            #     continue
        blastp.get("https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastp&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome")


if __name__ == "__main__":
    args = get_arguments()
    auto_blastp(args)
