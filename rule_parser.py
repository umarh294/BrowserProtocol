import urllib.request
import re
import ssl
import pickle
import os
from ad_blocker_trie import AdBlockTrie

class RuleParser:
    def __init__(self, trie_engine: AdBlockTrie):
        self.trie = trie_engine
        self.source_url = "https://raw.githubusercontent.com/AdAway/adaway.github.io/master/hosts.txt"
        self.cache_file = "trie_cache.bin"

    def fetch_and_populate(self) -> int:
        # 1. Check if localized pre-compiled state exists
        if os.path.exists(self.cache_file):
            print(f"📦 Local storage match hit. Deserializing binary tree state from {self.cache_file}...")
            try:
                with open(self.cache_file, 'rb') as f:
                    cached_root = pickle.load(f)
                self.trie.root = cached_root
                print("⚡ Trie memory matrix hydrated instantly from local binary cache.")
                return -1 # Signaling cache recovery instead of raw count recalculation
            except Exception as e:
                print(f"⚠️ Cache read mismatch: {e}. Falling back to remote stream synchronization...")

        # 2. Network Fallback Pipeline
        print(f"🌐 Requesting upstream live blocklist from: {self.source_url}")
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(self.source_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=context) as response:
                raw_data = response.read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to stream blocklist data: {e}")
            return 0

        print("🧮 Parsing and cleaning network rules...")
        rules_added = 0
        pattern = re.compile(r"^(?:127\.0\.0\.1|0\.0\.0\.0)\s+(\S+)")

        for line in raw_data.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            match = pattern.match(line)
            if match:
                domain_to_block = match.group(1).lower()
                if domain_to_block in ["localhost", "localhost.localdomain"]:
                    continue
                self.trie.insert(domain_to_block)
                rules_added += 1

        # 3. Snapshot compiled state out to the disk filesystem
        print(f"💾 Ingestion complete. Serializing tree matrix states to disk...")
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.trie.root, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"✅ State checkpoint logged cleanly to {self.cache_file}.")
        except Exception as e:
            print(f"⚠️ State serialization storage aborted: {e}")

        return rules_added

if __name__ == "__main__":
    test_trie = AdBlockTrie()
    parser = RuleParser(test_trie)
    parser.fetch_and_populate()