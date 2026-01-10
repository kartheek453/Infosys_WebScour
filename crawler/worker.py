import pika
import requests
import os
import threading
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ---------- CONFIG ----------
NUM_WORKERS = 3
MAX_PAGES = 10          
visited = set()
visited_lock = threading.Lock()
pages_crawled = 0
start_time = time.time()
# ----------------------------

def fetch_page(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for tag in soup.find_all("a", href=True):
        full_url = urljoin(base_url, tag["href"])
        if full_url.startswith("http"):
            links.add(full_url)
    return links

def worker(worker_id):
    global pages_crawled

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue="url_queue", durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        global pages_crawled
        url = body.decode()

        with visited_lock:
            if pages_crawled >= MAX_PAGES:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()
                return

            if url in visited:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            visited.add(url)
            pages_crawled += 1
            page_no = pages_crawled

        print(f"[Worker-{worker_id}] Crawling: {url}")

        html = fetch_page(url)
        if html:
            os.makedirs("pages", exist_ok=True)
            with open(f"pages/worker{worker_id}_page{page_no}.html", "w", encoding="utf-8") as f:

                f.write(html)

            links = extract_links(url, html)
            for link in links:
                with visited_lock:
                    if pages_crawled < MAX_PAGES:
                        ch.basic_publish(
                            exchange="",
                            routing_key="url_queue",
                            body=link
                        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue="url_queue",
        on_message_callback=callback
    )

    print(f"[Worker-{worker_id}] Started")
    channel.start_consuming()
    connection.close()

# ---------- START ALL WORKERS ----------
threads = []

for i in range(1, NUM_WORKERS + 1):
    t = threading.Thread(target=worker, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

end_time = time.time()

print("\n========== SUMMARY ==========")
print(f"Workers Used   : {NUM_WORKERS}")
print(f"Pages Crawled  : {pages_crawled}")
print(f"Time Taken    : {end_time - start_time:.2f} sec")
print("============================\n")
