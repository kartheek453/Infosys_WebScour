import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from queue import Queue

# Fetch Page

def fetch_page(url):
    try:
        response = requests.get(url, timeout=5, headers={"User-Agent": "MultiWorkerCrawler/1.0"})
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

# Extract Links

def extract_links(base_url, html, seed_domain):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]

        # Skip useless links
        if href.startswith(("mailto:", "javascript:", "#", "tel:")):
            continue

        full_url = urljoin(base_url, href)

        if not full_url.startswith("http"):
            continue

        if urlparse(full_url).netloc != seed_domain:
            continue

        links.add(full_url)

    return links


# WORKER FUNCTION (TASK 3 + 4)

def worker(worker_id, queue, visited, lock, seed_domain, max_pages):
    while True:
        try:
            url = queue.get(timeout=3)
        except:
            return

        with lock:
            if len(visited) >= max_pages or url in visited:
                queue.task_done()
                continue
            visited.add(url)

        print(f"[Worker-{worker_id}] Crawling: {url}")

        html = fetch_page(url)
        if html:
            # Save page
            file_name = f"pages/page_{len(visited)}.html"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(html)

            links = extract_links(url, html, seed_domain)
            for link in links:
                with lock:
                    if link not in visited:
                        queue.put(link)

        queue.task_done()
        time.sleep(0.2)



# MAIN

def main():
    seed_url = "https://coursera.org"
    seed_domain = urlparse(seed_url).netloc
    max_pages = 10
    num_workers = 3

    if not os.path.exists("pages"):
        os.mkdir("pages")

    queue = Queue()
    queue.put(seed_url)

    visited = set()
    lock = threading.Lock()

    threads = []
    start_time = time.time()

    for i in range(num_workers):
        t = threading.Thread(
            target=worker,
            args=(i + 1, queue, visited, lock, seed_domain, max_pages)
        )
        t.start()
        threads.append(t)

    queue.join()

    end_time = time.time()

    with open("visited.txt", "w") as f:
        for url in visited:
            f.write(url + "\n")

    print("\n========= SUMMARY =========")
    print(f"Workers Used   : {num_workers}")
    print(f"Pages Crawled  : {len(visited)}")
    print(f"Time Taken    : {end_time - start_time:.2f} sec")
    print("===========================\n")


if __name__ == "__main__":
    main()
