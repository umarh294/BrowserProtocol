import sys
import os
import urllib.parse
from PyQt6.QtCore import QUrl, Qt, QFileInfo, QEvent
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLineEdit, QLabel, QPushButton, QTabWidget, QListWidget)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ad_blocker_trie import AdBlockTrie
from rule_parser import RuleParser

# Ad-purging engine
AD_CLEANUP_SCRIPT = """
(function() {
    function purge() {
        const selectors = ['amp-ad', 'ins.adsbygoogle', 'div[id^="div-gpt-ad"]', '.adsbox', '.ad-container', '.ad-placement', '[class*="ad-sharing"]', 'iframe[src*="doubleclick.net"]'];
        selectors.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
    }
    setInterval(purge, 500);
})();
"""

class NetworkInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, trie, update_ui):
        super().__init__()
        self.trie, self.update_ui, self.count = trie, update_ui, 0

    def interceptRequest(self, info):
        if self.trie.should_block(info.requestUrl().toString()):
            info.block(True)
            self.count += 1
            self.update_ui(self.count)

class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Privacy Engine Pro")
        self.resize(1340, 880)
        self.trie = AdBlockTrie()
        self.manage_cache_lifecycle()
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(NetworkInterceptor(self.trie, self.increment_display))
        self.init_ui()

    def init_ui(self):
        self.central = QWidget()
        self.setCentralWidget(self.central)
        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. TAB BAR ROW (Layout + TabWidget + Button)
        tab_row = QHBoxLayout()
        tab_row.setContentsMargins(0, 0, 0, 0)
        tab_row.setSpacing(0)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(lambda i: self.tab_widget.removeTab(i))
        tab_row.addWidget(self.tab_widget, stretch=1)

        # Dedicated Add Tab Button
        self.btn_add = QPushButton("＋")
        self.btn_add.setFixedSize(40, 30)
        self.btn_add.setStyleSheet("""
            QPushButton { background: #2a2a2e; color: white; border: none; font-size: 16px; border-radius: 4px; }
            QPushButton:hover { background: #3d3d44; }
        """)
        self.btn_add.clicked.connect(lambda: self.add_new_tab(QUrl("https://www.google.com"), "New Tab"))
        tab_row.addWidget(self.btn_add)
        
        main_layout.addLayout(tab_row)

        # 2. NAV BAR SECTION
        nav_wrapper = QWidget()
        nav_wrapper.setStyleSheet("background: #1a1a1e; padding: 10px;")
        nav_layout = QHBoxLayout(nav_wrapper)
        
        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("background: #2a2a2e; color: white; border-radius: 18px; padding: 8px 15px; border: 1px solid #3d3d44;")
        self.url_bar.returnPressed.connect(self.navigate)
        nav_layout.addWidget(self.url_bar)
        
        self.btn_bookmarks = QPushButton("🔖")
        self.btn_bookmarks.setStyleSheet("background: #2a2a2e; padding: 8px; border-radius: 18px; color: white;")
        self.btn_bookmarks.clicked.connect(self.toggle_sidebar)
        nav_layout.addWidget(self.btn_bookmarks)
        
        self.counter = QLabel("🛡️ 0")
        self.counter.setStyleSheet("color: #00b0ff; font-weight: bold; margin-left: 10px;")
        nav_layout.addWidget(self.counter)
        main_layout.addWidget(nav_wrapper)

        # 3. Sidebar Setup
        self.sidebar = QListWidget(self)
        self.sidebar.setGeometry(-200, 100, 200, self.height() - 100)
        self.sidebar.setStyleSheet("background: #1e1e24; color: white; border: none;")
        self.sidebar.addItems(["google.com", "youtube.com", "github.com"])
        self.sidebar.itemClicked.connect(lambda i: self.nav_to(i.text()))
        
        self.add_new_tab(QUrl("https://www.google.com"), "New Tab")

    def add_new_tab(self, qurl, title):
        browser = QWebEngineView()
        browser.setUrl(qurl)
        browser.loadFinished.connect(lambda: browser.page().runJavaScript(AD_CLEANUP_SCRIPT))
        
        # Explicitly show the browser
        browser.show()
        
        index = self.tab_widget.addTab(browser, title)
        self.tab_widget.setCurrentIndex(index)

    def navigate(self):
        url = self.url_bar.text()
        url = url if "." in url else f"https://www.google.com/search?q={urllib.parse.quote(url)}"
        self.tab_widget.currentWidget().setUrl(QUrl(url if "://" in url else "https://" + url))

    def nav_to(self, url):
        self.tab_widget.currentWidget().setUrl(QUrl("https://" + url))
        self.toggle_sidebar()

    def toggle_sidebar(self):
        self.sidebar.move(0 if self.sidebar.x() < 0 else -200, 100)

    def increment_display(self, count):
        self.counter.setText(f"🛡️ {count}")

    def manage_cache_lifecycle(self):
        RuleParser(self.trie).fetch_and_populate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomBrowser()
    window.show()
    sys.exit(app.exec())