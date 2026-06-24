import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ad_blocker_trie import AdBlockTrie
from rule_parser import RuleParser


class NetworkInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, trie_engine: AdBlockTrie):
        super().__init__()
        self.trie = trie_engine
        self.blocked_count = 0

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        request_url = info.requestUrl().toString()
        
        # Intercept and screen the network request through our Trie data structure
        if self.trie.should_block(request_url):
            info.block(True)
            self.blocked_count += 1
            print(  f"[BLOCKED] Intercepted ad request: {request_url} | Total Blocked: {self.blocked_count}"  )


class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Privacy Engine Desktop Browser")
        self.resize(1200, 800)

        # 1. Initialize our high-performance Trie Engine
        self.trie = AdBlockTrie()
        self.load_mock_blocklist()

        # 2. Setup Network Interception Pipeline
        self.interceptor = NetworkInterceptor(self.trie)
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.interceptor)

        # 3. Create GUI Layout
        layout = QVBoxLayout()
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        layout.addWidget(self.url_bar)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://google.com"))
        self.browser.urlChanged.connect(lambda qurl: self.url_bar.setText(qurl.toString()))
        layout.addWidget(self.browser)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_mock_blocklist(self):
        """Streams real, high-volume production blocklists directly into memory"""
        print("📥 Initializing live blocklist synchronization...")
        self.parser = RuleParser(self.trie)
        
        # This streams over 50,000+ real-world tracking rules into your Trie on startup
        rules_loaded = self.parser.fetch_and_populate()
        print(f"🚀 Navigation engine armed with {rules_loaded:,} rules.")

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomBrowser()
    window.show()
    sys.exit(app.exec())