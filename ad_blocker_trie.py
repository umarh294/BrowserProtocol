import time

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_domain = False

class AdBlockTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, domain: str):
        """Inserts a blacklisted domain into the Trie."""
        node = self.root
        # Process the domain backward or forward; forward works great for exact/subdomain matches
        for char in domain.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        self.is_end_of_domain = True

    def should_block(self, url: str) -> bool:
        """
        Evaluates an incoming URL string against the Trie.
        Returns True if the URL or its domain matches a blacklisted entry.
        """
        # Quick clean-up to isolate the domain logic
        clean_url = url.lower().replace("https://", "").replace("http://", "").split('/')[0]
        
        # Check standard domain and subdomains
        tokens = clean_url.split('.')
        for i in range(len(tokens)):
            test_domain = ".".join(tokens[i:])
            if self._search_exact(test_domain):
                return True
        return False

    def _search_exact(self, domain: str) -> bool:
        node = self.root
        for char in domain:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_domain