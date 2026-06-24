import time
import random
import string
from ad_blocker_trie import AdBlockTrie

def generate_random_domain():
    """Generates a random domain string like 'ads-b4f1.doubleclick.net'"""
    sub = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    domains = ["doubleclick.net", "analytics.google.com", "adservice.io", "telemetry.net"]
    return f"ads-{sub}.{random.choice(domains)}"

def run_benchmark():
    print("🚀 Initializing M2 Pro Benchmarking Framework...")
    
    # 1. Generate 10,000 distinct dummy domains
    all_domains = [generate_random_domain() for _ in range(10000)]
    
    # 2. Pick 2,500 of them to be explicitly blacklisted
    blacklist_sample = random.sample(all_domains, 2500)
    
    # Setup Data Structures
    trie = AdBlockTrie()
    linear_list = []
    
    # Populate both
    for domain in blacklist_sample:
        trie.insert(domain)
        linear_list.append(domain)
        
    print(f"📦 Populated engines with {len(blacklist_sample)} blacklisted rules.")
    print(f"📡 Simulating screening of {len(all_domains)} incoming network requests...\n")
    
    # --- Test 1: Standard Linear Array Lookup O(n) ---
    start_time = time.perf_counter()
    list_blocked_count = 0
    for url in all_domains:
        # Simple linear verification
        for blocked_domain in linear_list:
            if blocked_domain in url:
                list_blocked_count += 1
                break
    list_duration = (time.perf_counter() - start_time) * 1000 # convert to ms
    
    # --- Test 2: Optimized Trie Lookup O(m) ---
    start_time = time.perf_counter()
    trie_blocked_count = 0
    for url in all_domains:
        if trie.should_block(url):
            trie_blocked_count += 1
    trie_duration = (time.perf_counter() - start_time) * 1000 # convert to ms
    
    # --- Results Dashboard ---
    print("=" * 50)
    print("📊 BENCHMARK METRICS PERFORMANCE REPORT")
    print("=" * 50)
    print(f"Linear List Lookup O(n):  {list_duration:.2f} ms")
    print(f"Optimized Trie Lookup O(m): {trie_duration:.2f} ms")
    
    if trie_duration > 0:
        speedup = list_duration / trie_duration
        print(f"\n⚡ Result: Your Trie engine is {speedup:.1f}x FASTER than a standard list scan.")
    print("=" * 50)

if __name__ == "__main__":
    run_benchmark()