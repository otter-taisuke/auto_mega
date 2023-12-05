import argparse
import os

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ORGANISM = "organism.txt"
DEFAULT_QUERY = "query.txt"


def get_argumants() -> argparse.Namespace:
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
                    inputs = f.readlines()
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
    query_box = browser.find_elements(By.XPATH, "//textarea[@id=\"seq\"]")
    query_box[0].send_keys(query)
    organism_input = browser.find_elements(By.XPATH, "//input[@id=\"qorganism\"]")
    organism_input[0].send_keys(organism)
    wait_by_xpath(browser, "//li[@role=\"menuitem\"]")
    suggested_organism = browser.find_elements(By.XPATH, "//li[@role=\"menuitem\"]")
    suggested_organism[0].click()
    run_button = browser.find_elements(By.XPATH, "//input[@class=\"blastbutton\"]")
    run_button[0].click()
    wait_by_xpath(browser, "//main[@class=\"results content blastp\"]", 300)



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
        for organism in tqdm(organism_list):
            download = os.path.join(ROOT, "output", query)
            os.makedirs(download, exist_ok=True)
            blast = open_new_blastp(download)
            run_alignment(blast, query, organism)



if __name__ == "__main__":
    args = get_argumants()
    auto_blastp(args)
