"""
This module is used to scrape proxies.
"""
import requests
import re
import random
import time

from bs4 import BeautifulSoup


def retry(func, retries=50):
    """
    retry decorator to retry the method over and over till we get a non-exception result
    """

    def retry_wrapper(*args, **kwargs):
        attempts = 0
        while attempts < retries:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                print(e)
                time.sleep(2)
                attempts += 1

    return retry_wrapper


def get_proxies():
    """
    !!! exprimental code copied from github #TODO clean up code
    """

    # scraping proxies from spys.me and writing in proxies_list.txt
    regex = r"[0-9]+(?:\.[0-9]+){3}:[0-9]+"
    raw_proxy_str = requests.get("https://spys.me/proxy.txt").text
    proxies = re.finditer(regex, raw_proxy_str, re.MULTILINE)
    with open("proxies_list.txt", "w") as file:
        for proxy in proxies:
            print(proxy.group(), file=file)

    soup = BeautifulSoup(
        requests.get("https://free-proxy-list.net/").content, "html.parser"
    )
    td_elements = soup.select(".fpl-list .table tbody tr td")
    ips = []
    ports = []
    for j in range(0, len(td_elements), 8):
        ips.append(td_elements[j].text.strip())
        ports.append(td_elements[j + 1].text.strip())
    with open("proxies_list.txt", "a") as myfile:
        for ip, port in zip(ips, ports):
            proxy = f"{ip}:{port}"
            print(proxy, file=myfile)


get_proxies()


def proxy_from_txt(filename):
    with open(filename, "r") as f:
        txt_proxies = [line.strip() for line in f]
    return txt_proxies


@retry
def validate_proxies(proxy_choice):
    url = "https://google.com"
    proxy_index = random.choice(range(len(proxy_choice)))
    proxy = proxy_choice[proxy_index]
    proxies = {"https": proxy, "http": proxy}
    proxy_choice.pop(proxy_index)
    r = requests.get(url, proxies=proxies, timeout=2)
    data = {
        "data": [r.json()["products"][0]["id"], r.json()["products"][0]["title"]],
        "proxy": proxies,
    }
    print(data)


if __name__ == "__main__":
    get_proxies()
    proxy_list = proxy_from_txt("proxies_list.txt")
    validate_proxies(proxy_list)

print(requests.get("https://linkedin.com", timeout=2))
