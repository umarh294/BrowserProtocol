import sys

class TrieNode:
    __slots__ = ('children', 'is_end_of_domain')
    
    def __init__(self):
        self.children = {}
        self.is_end_of_domain = False

    def __getstate__(self):
        """Custom serialization map required because __slots__ drops standard __dict__ representation."""
        return (self.is_end_of_domain, self.children)

    def __setstate__(self, state):
        """Reconstructs slot boundaries instantly from serialized binary chunks."""
        self.is_end_of_domain, self.children = state


class AdBlockTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, domain: str):
        """Inserts a blacklisted domain into the Trie structure."""
        node = self.root
        domain = domain.lower().strip()
        for char in domain:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_domain = True

    def should_block(self, url: str) -> bool:
        """Evaluates fully qualified domain components via right-to-left suffix matching."""
        clean_domain = url.lower().replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]
        tokens = clean_domain.split('.')
        
        for i in range(len(tokens) - 1, -1, -1):
            substring_domain = ".".join(tokens[i:])
            if self._search_exact(substring_domain):
                return True
        return False

    def _search_exact(self, domain: str) -> bool:
        node = self.root
        for char in domain:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_of_domain