import urllib.request
import re
import ssl
from ad_blocker_trie import AdBlockTrie

class RuleParser:
    def __init__(self, trie_engine: AdBlockTrie):
        self.trie = trie_engine
        # Target raw production blocklists (Using AdAway host format for clean domain extraction)
        self.source_url = "https://raw.githubusercontent.com/AdAway/adaway.github.io/master/hosts.txt"

    def fetch_and_populate(self) -> int:
        print(f"🌐 Requesting upstream live blocklist from: {self.source_url}")
        try:
            # Create an unverified SSL context to bypass missing local macOS root issuer certificates
            context = ssl._create_unverified_context()
            
            req = urllib.request.Request(self.source_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Pass the unverified context directly into the secure stream connection
            with urllib.request.urlopen(req, context=context) as response:
                raw_data = response.read().decode('utf-8')
        except Exception as e:
            print(f"❌ Failed to stream blocklist data: {e}")
            return 0

        print("🧮 Parsing and cleaning network rules...")
        rules_added = 0
        
        # Standard hosts format matches lines like: 127.0.0.1 target-ad-domain.com
        # We look for lines starting with IP loops or local configurations
        pattern = re.compile(r"^(?:127\.0\.0\.1|0\.0\.0\.0)\s+(\S+)")

        for line in raw_data.splitlines():
            line = line.strip()
            # Drop structural comments and metadata lines
            if not line or line.startswith("#"):
                continue
                
            match = pattern.match(line)
            if match:
                domain_to_block = match.group(1).lower()
                # Exclude local host configurations to prevent system loop interception
                if domain_to_block in ["localhost", "localhost.localdomain"]:
                    continue
                
                self.trie.insert(domain_to_block)
                rules_added += 1

        print(f"✅ Successfully ingested and structuralized {rules_added:,} live rules into the Trie.")
        return rules_added

if __name__ == "__main__":
    # Quick structural isolation test
    test_trie = AdBlockTrie()
    parser = RuleParser(test_trie)
    count = parser.fetch_and_populate()
    
    # Run a spot verification check against known standard tracker strings
    test_url = "https://analytics.google.com/api/v2/track"
    print(f"🔍 Validation check for '{test_url}': Blocked = {test_trie.should_block(test_url)}")