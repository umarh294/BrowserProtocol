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
        # Extract the full request URL string from Chromium's pipeline
        request_url = info.requestUrl().toString()
        
        # Screen the live resource network request using our right-to-left suffix matching
        if self.trie.should_block(request_url):
            info.block(True)
            self.blocked_count += 1
            print(f"🛑 [BLOCKED] Intercepted tracker: {request_url} | Total Intercepted: {self.blocked_count}")


class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Privacy Engine Desktop Browser")
        self.resize(1200, 800)

        # 1. Spin up the advanced Trie matching infrastructure
        self.trie = AdBlockTrie()
        self.synchronize_live_rules()

        # 2. Bind our request interceptor directly to the default profile networking layer
        self.interceptor = NetworkInterceptor(self.trie)
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.interceptor)

        # 3. Assemble native application UI components
        layout = QVBoxLayout()
        
        # URL Input Field
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        layout.addWidget(self.url_bar)

        # Embedded Chromium Web Rendering Shell
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        
        # Ensure the address bar updates visually when navigation redirects occur
        self.browser.urlChanged.connect(lambda qurl: self.url_bar.setText(qurl.toString()))
        layout.addWidget(self.browser)

        # Set main layout structure
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def synchronize_live_rules(self):
        """Streams, cleans, and builds the live security blocklist directly in RAM."""
        print("📥 Initializing live upstream blocklist synchronization...")
        self.parser = RuleParser(self.trie)
        
        # Fire the network stream to ingest the production host rules
        rules_loaded = self.parser.fetch_and_populate()
        print(f"🚀 Navigation engine successfully armed with {rules_loaded:,} rules.")

    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomBrowser()
    window.show()
    sys.exit(app.exec())