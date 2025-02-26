"""
This module is used to scrape and validate proxies.
"""

import requests
import re
import random
import time
import logging
from multiprocessing import Pool
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("proxy_scraper")


def retry(retries=3, delay=0.5):
    """
    Retry decorator that can be used with parameters.

    Args:
        retries: Maximum number of retries
        delay: Delay between retries in seconds

    Returns:
        Decorator function that wraps the target function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    attempts += 1
                    if attempts >= retries:
                        raise e
                    time.sleep(delay)

        return wrapper

    return decorator


@retry()
def get_proxies():
    """
    Scrapes proxies from multiple sources and returns a list
    """
    proxies = []

    # Source 1: spys.me
    try:
        regex = r"[0-9]+(?:\.[0-9]+){3}:[0-9]+"
        raw_proxy_str = requests.get("https://spys.me/proxy.txt", timeout=10).text
        spys_proxies = re.findall(regex, raw_proxy_str)
        proxies.extend(spys_proxies)
        logger.debug(f"Found {len(spys_proxies)} proxies from spys.me")
    except requests.exceptions.RequestException as e:
        logger.debug(f"Error fetching from spys.me: {e}")

    # Source 2: free-proxy-list.net
    try:
        response = requests.get("https://free-proxy-list.net/", timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.select(".fpl-list .table tbody tr")

        fpl_proxies = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                ip = cells[0].text.strip()
                port = cells[1].text.strip()
                fpl_proxies.append(f"{ip}:{port}")

        proxies.extend(fpl_proxies)
        logger.debug(f"Found {len(fpl_proxies)} proxies from free-proxy-list.net")
    except requests.exceptions.RequestException as e:
        logger.debug(f"Error fetching from free-proxy-list.net: {e}")

    # Remove duplicates
    proxies = list(set(proxies))
    return proxies


@retry(retries=2, delay=0.5)
def validate_proxy(proxy, test_url="https://linkedin.com", timeout=2):
    """
    Validate a single proxy

    Args:
        proxy: Proxy to validate in format ip:port
        test_url: URL to test the proxy against
        timeout: Request timeout in seconds

    Returns:
        Tuple of (proxy, response_time) if valid, None if invalid
    """
    proxies = {"https": f"http://{proxy}", "http": f"http://{proxy}"}
    start_time = time.perf_counter()

    try:
        r = requests.get(url=test_url, proxies=proxies, timeout=timeout)
        end_time = time.perf_counter()
        response_time = end_time - start_time

        if r.status_code == 200:
            logger.debug(f"Valid proxy: {proxy}, response time: {response_time:.2f}s")
            return (proxy, response_time)
        return None
    except Exception:
        return None


def validate_proxies_worker(proxy):
    """
    Worker function for validating proxies in parallel

    Args:
        proxy: Proxy to validate

    Returns:
        Validated proxy or None
    """
    logger.debug(f"Testing proxy: {proxy}")
    result = validate_proxy(proxy)

    if result:
        proxy, _ = result
        return proxy
    return None


def validate_proxies(proxy_list, workers=10):
    """
    Validate a list of proxies in parallel

    Args:
        proxy_list: List of proxies to validate
        workers: Number of parallel workers

    Returns:
        List of valid proxies
    """
    logger.info(f"Validating {len(proxy_list)} proxies...")

    # Use a smaller pool size to avoid overwhelming resources
    with Pool() as pool:
        results = pool.map(validate_proxies_worker, proxy_list)

    # Filter out None results
    valid_proxies = [proxy for proxy in results if proxy]

    # Save valid proxies to file
    with open("verified_proxies.txt", "w") as file:
        for proxy in valid_proxies:
            file.write(f"{proxy}\n")

    logger.info(f"Found {len(valid_proxies)} working proxies")
    return valid_proxies


if __name__ == "__main__":

    # Validate proxies
    valid_proxies = validate_proxies(proxy_list=get_proxies(), workers=15)

    logger.info("Validation complete. Results saved to verified_proxies.txt")
