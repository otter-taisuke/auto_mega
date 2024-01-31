import argparse
import os
import time

from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


ROOT = os.path.abspath(os.path.dirname(__file__))
DEFAULT_ORGANISM = "organism.txt"
DEFAULT_QUERY = "query.txt"

blastp = "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastp&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome"
blastn = "https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome"


class DownloadTimeoutException(Exception):
    pass


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="automation: blast")
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


def open_new_browser(download: str | None = None) -> webdriver.chrome:
    chrome_options = webdriver.ChromeOptions()
    if download:
        prefs = {"download.default_directory": download}
        chrome_options.add_experimental_option("prefs", prefs)
    browser = webdriver.Chrome(options=chrome_options)
    return browser


def wait_by_xpath(browser: webdriver.chrome, xpath: str, limit: int = 20):
    wait = WebDriverWait(browser, limit)
    wait.until(EC.presence_of_element_located((By.XPATH, xpath)))


def run_blast(browser: webdriver.chrome, query: str, organism: str):
    wait_by_xpath(browser, "//div[@id=\"wrap\"]")
    query_box = browser.find_elements(By.XPATH, "//textarea[@id=\"seq\"]")
    query_box[0].clear()
    query_box[0].send_keys(query)
    organism_input = browser.find_elements(By.XPATH, "//input[@id=\"qorganism\"]")
    organism_input[0].clear()
    organism_input[0].send_keys(organism)
    wait_by_xpath(browser, "//li[@role=\"menuitem\"]")
    suggested_organism = browser.find_elements(By.XPATH, "//li[@role=\"menuitem\"]")
    suggested_organism[0].click()
    run_button = browser.find_elements(By.XPATH, "//input[@class=\"blastbutton\"]")
    time.sleep(1)  # care delay/lag
    run_button[0].click()
    wait_by_xpath(browser, "//main[contains(@class, \"results content blast\")]", 300)


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
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # fasta_download[0].click()
    action = ActionChains(browser).move_to_element_with_offset(fasta_download[0], 1, 1)
    action.click().perform()
    raw_path = os.path.join(download, "seqdump.txt")
    result_path = os.path.join(download, organism + ".txt")
    wait_download(raw_path)
    os.rename(raw_path, result_path)


def auto_blastp(args: argparse.Namespace):
    if args.simple:
        query_list = [input("Enter Query Seq :")]
    else:
        query_list = load_input(os.path.join(ROOT, args.query))
    organism_list = load_input(os.path.join(ROOT, args.organism))
    if args.simple and (query_list[0] == "" or organism_list is None):
        print("Error: Incomplete input information.")
    elif not args.simple and (query_list is None or organism_list is None):
        print("Error: Incomplete input information.")
    for query_line in query_list:
        query, code = query_line.split(",")
        download = os.path.join(ROOT, "blast", query)
        os.makedirs(download, exist_ok=True)
        browser = open_new_browser(download)
        for organism in tqdm(organism_list, desc=f"Now searching <{query}> similarity..."):
            try:
                browser.get(blastp)
                run_blast(browser, code, organism)
                tqdm.write(f"finish search {organism}")
                download_result(browser, download, organism)
            except ElementNotInteractableException:
                tqdm.write(f"<{organism}> has no similar seq with <{query}>.")
                with open(os.path.join(ROOT, "blast", f"{query} - no homology.txt"), mode="a") as f:
                    f.write(organism + "\n")
                continue
            except DownloadTimeoutException:
                tqdm.write(f"Timeout: Download time has exceeded the limit.({query}-{organism})")
                continue
            except:
                tqdm.write("Error: Unknown error.({query}-{organism})")
                continue


def assist_blastp():
    data = os.path.join(ROOT, "blast_assist/assist_data.txt")
    data_set = load_input(data)
    query = data_set[0]
    organism = data_set[1:]
    browser = open_new_browser()
    browser.get(blastn)
    wait_by_xpath(browser, "//div[@id=\"wrap\"]")
    try:
        query_box = browser.find_elements(By.XPATH, "//textarea[@id=\"seq\"]")
        query_box[0].clear()
        query_box[0].send_keys(query)
    except:
        print("Error: When enter query")
    for i, org in enumerate(organism):
        try:
            if i == 0:
                input_button = browser.find_elements(By.XPATH, "//input[@id=\"qorganism\"]")
            else:
                input_button = browser.find_elements(By.XPATH, f"//input[@id=\"qorganism{i}\"]")
            input_button[0].clear()
            input_button[0].send_keys(org)
            wait_by_xpath(browser, "//li[@role=\"menuitem\"]")
            suggested_organism = browser.find_elements(By.XPATH, "//li[@role=\"menuitem\"]")
            suggested_organism[0].click()
            add_button = browser.find_elements(By.XPATH, "//input[@class=\"usa-button-secondary addOrg\"]")[0]
            add_button.click()
        except:
            print(f"Error: When enter {org}")
            continue
    time.sleep(100000)


if __name__ == "__main__":
    args = get_arguments()
    auto_blastp(args)
    # assist_blastp()
