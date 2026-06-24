import sys
import os
import time
from PyQt6.QtCore import QUrl, Qt, QFileInfo
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QLabel
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ad_blocker_trie import AdBlockTrie
from rule_parser import RuleParser

class NetworkInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, trie_engine: AdBlockTrie, update_callback):
        super().__init__()
        self.trie = trie_engine
        self.blocked_count = 0
        self.update_ui = update_callback

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        request_url = info.requestUrl().toString()
        
        # Suffix-matching engine lookups
        if self.trie.should_block(request_url):
            info.block(True)
            self.blocked_count += 1
            # Dispatch count modifications back safely to the main GUI thread layout
            self.update_ui(self.blocked_count)
            print(f"🛑 [BLOCKED] Intercepted tracker: {request_url} | Total Intercepted: {self.blocked_count}")


class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Privacy Engine Browser (M2 Pro Optimized)")
        self.resize(1280, 850)

        # 1. Initialize Trie data model
        self.trie = AdBlockTrie()
        self.manage_cache_lifecycle()

        # 2. Assemble UI elements
        self.init_ui()

        # 3. Bind request interceptor with a cross-thread visual callback update
        self.interceptor = NetworkInterceptor(self.trie, self.increment_block_display)
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.interceptor)

    def init_ui(self):
        main_layout = QVBoxLayout()
        top_navigation_bar = QHBoxLayout()

        # Action bar: Address element
        self.url_bar = QLineEdit()
        self.url_bar.placeholderText = "Enter a URL or search path..."
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        top_navigation_bar.addWidget(self.url_bar, stretch=4)

        # Action bar: Visual Block Counter Component
        self.counter_label = QLabel("🛡️ Trackers Blocked: 0")
        self.counter_label.setStyleSheet("font-weight: bold; color: #00b0ff; padding-left: 10px; font-size: 13px;")
        top_navigation_bar.addWidget(self.counter_label, stretch=1)
        
        main_layout.addLayout(top_navigation_bar)

        # Embedded Core Web View Container
        self.browser_view = QWebEngineView()
        self.browser_view.setUrl(QUrl("https://www.google.com"))
        self.browser_view.urlChanged.connect(lambda qurl: self.url_bar.setText(qurl.toString()))
        main_layout.addWidget(self.browser_view)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def manage_cache_lifecycle(self):
        """Validates if cache state is fresh, otherwise prompts automated sync sweeps."""
        cache_path = "trie_cache.bin"
        self.parser = RuleParser(self.trie)
        
        if os.path.exists(cache_path):
            file_info = QFileInfo(cache_path)
            age_in_seconds = file_info.lastModified().secsTo(file_info.lastModified().currentDateTime())
            
            # If cache file lifecycle is older than 24 hours (86,400 seconds), clear out stale file state
            if age_in_seconds > 86400:
                print("⚠️ Local blocklist cache expired. Removing stale state references...")
                try:
                    os.remove(cache_path)
                except Exception as e:
                    print(f"⚠️ Cache invalidation fault: {e}")

        # Hydrate internal memory model via rule engine orchestrator
        self.parser.fetch_and_populate()

    def increment_block_display(self, count):
        """Updates the status counter label safely inside the user interface loop."""
        self.counter_label.setText(f"🛡️ Trackers Blocked: {count}")

    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.browser_view.setUrl(QUrl(url))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomBrowser()
    window.show()
    sys.exit(app.exec())