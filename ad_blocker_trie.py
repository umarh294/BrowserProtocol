import sys

class TrieNode:
    # Bypasses Python's dynamic instance dictionary creation.
    # Forces memory layouts to match strict C-level structure sizes for attributes.
    __slots__ = ('children', 'is_end_of_domain')
    
    def __init__(self):
        self.children = {}
        self.is_end_of_domain = False

class AdBlockTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, domain: str):
        """Inserts a blacklisted domain into the Trie."""
        node = self.root
        domain = domain.lower().strip()
        for char in domain:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_domain = True

    def should_block(self, url: str) -> bool:
        """
        Extracts the hostname and evaluates it against the Trie.
        Implements a right-to-left suffix fallback strategy to catch all subdomains.
        """
        # Clean the incoming URL down to just the fully qualified domain name (FQDN)
        clean_domain = url.lower().replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]
        
        # Tokenize the domain by its periods
        tokens = clean_domain.split('.')
        
        # Iterate backwards to check root domains and subdomains hierarchically
        for i in range(len(tokens) - 1, -1, -1):
            substring_domain = ".".join(tokens[i:])
            if self._search_exact(substring_domain):
                return True
                
        return False

    def _search_exact(self, domain: str) -> bool:
        """Internal helper to trace characters explicitly through the Trie structure."""
        node = self.root
        for char in domain:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_domain