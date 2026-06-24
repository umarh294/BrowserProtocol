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

# Dynamic Visual Cosmetic ad-purger and YouTube video bypass script
AD_CLEANUP_SCRIPT = """
(function() {
    function purgeAdElements() {
        const selectors = [
            'amp-ad', 'ins.adsbygoogle', 'div[id^="div-gpt-ad"]', 
            '.adsbox', '.ad-container', '.ad-placement', '[class*="ad-sharing"]',
            'iframe[src*="doubleclick.net"]', 'iframe[id^="google_ads_frame"]'
        ];
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.style.display = 'none';
                element.remove();
            });
        });

        if (window.location.hostname.includes('youtube.com')) {
            const video = document.querySelector('video');
            const adContainer = document.querySelector('.video-ads ytp-ad-module');
            const skipButton = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button-mod');

            if (adContainer && adContainer.children.length > 0 && video) {
                if (skipButton) {
                    skipButton.click();
                } else {
                    video.muted = true;
                    video.playbackRate = 16.0; 
                    if (!isNaN(video.duration)) {
                        video.currentTime = video.duration - 0.1;
                    }
                }
            }
        }
    }
    purgeAdElements();
    setInterval(purgeAdElements, 500);
})();
"""

class NetworkInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, trie_engine: AdBlockTrie, update_callback):
        super().__init__()
        self.trie = trie_engine
        self.blocked_count = 0
        self.update_ui = update_callback

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        request_url = info.requestUrl().toString()
        if self.trie.should_block(request_url):
            info.block(True)
            self.blocked_count += 1
            self.update_ui(self.blocked_count)


class HoverLogoButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)

    def enterEvent(self, event):
        if hasattr(self.window(), 'show_sidebar'):
            self.window().show_sidebar()
        super().enterEvent(event)


class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Privacy Engine Desktop Browser")
        self.resize(1300, 850)

        self.trie = AdBlockTrie()
        self.manage_cache_lifecycle()

        self.interceptor = NetworkInterceptor(self.trie, self.increment_block_display)
        QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(self.interceptor)

        self.global_blocked_count = 0
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Base horizontal shell to house the sliding drawer
        outer_layout = QHBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. BOOKMARKS DRAWER
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #1e1e24; border-right: 1px solid #2d2d35;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        sidebar_title = QLabel("🔖 Bookmarks")
        sidebar_title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; padding: 5px;")
        sidebar_layout.addWidget(sidebar_title)

        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setStyleSheet("color: #cfcfd6; border: none; background: transparent; font-size: 12px;")
        self.bookmarks_list.addItems(["wikipedia.org", "github.com", "reddit.com", "youtube.com"])
        self.bookmarks_list.itemClicked.connect(self.navigate_to_bookmark)
        sidebar_layout.addWidget(self.bookmarks_list)
        
        self.sidebar.hide()
        outer_layout.addWidget(self.sidebar)

        # 2. MAIN APPLICATION CONTENT VIEWPORT
        main_content_shell = QWidget()
        outer_layout.addWidget(main_content_shell)
        
        main_layout = QVBoxLayout(main_content_shell)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 3. CONTROL BAR
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(5, 5, 5, 5)
        nav_bar.setSpacing(6)

        self.logo_btn = HoverLogoButton("🛡️")
        self.logo_btn.setStyleSheet("font-size: 16px; background: transparent; border: none; padding: 2px 8px;")
        nav_bar.addWidget(self.logo_btn)

        self.back_btn = QPushButton("◀")
        self.back_btn.setStyleSheet("background-color: #32323d; color: white; border-radius: 4px; padding: 4px 8px;")
        self.back_btn.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("▶")
        self.forward_btn.setStyleSheet("background-color: #32323d; color: white; border-radius: 4px; padding: 4px 8px;")
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("background-color: #2a2a35; color: white; border: 1px solid #3d3d4d; border-radius: 4px; padding: 4px; padding-left: 8px;")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        self.add_tab_btn = QPushButton("＋")
        self.add_tab_btn.setStyleSheet("background-color: #00b0ff; color: white; font-weight: bold; border-radius: 4px; padding: 4px 12px;")
        self.add_tab_btn.clicked.connect(lambda: self.add_new_tab(QUrl("https://www.google.com"), "New Tab"))
        nav_bar.addWidget(self.add_tab_btn)

        self.counter_label = QLabel("Blocked: 0")
        self.counter_label.setStyleSheet("font-weight: bold; color: #00b0ff; padding: 0px 8px; min-width: 80px;")
        nav_bar.addWidget(self.counter_label)

        # 4. CHROME-STYLE TOP TABS ENGINE
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; background: #121214; }
            QTabBar::tab { background: #232329; color: #a9a9b3; padding: 6px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #1c1c22; color: white; font-weight: bold; border-bottom: 2px solid #00b0ff; }
        """)

        # Add components sequentially to main window canvas
        main_layout.addWidget(self.tab_widget, stretch=1)
        main_layout.addLayout(nav_bar)

        # Ingest core template page
        self.add_new_tab(QUrl("https://www.google.com"), "New Tab")
        central_widget.installEventFilter(self)

    def add_new_tab(self, qurl: QUrl, title: str):
        """Creates a web runtime shell and adds it directly as a separate tab element."""
        browser = QWebEngineView()
        browser.setUrl(qurl)
        
        index = self.tab_widget.addTab(browser, title)
        
        # Connect redirect signals
        browser.urlChanged.connect(lambda url, b=browser: self.update_url_text(url, b))
        browser.titleChanged.connect(lambda t, b=browser: self.update_tab_title(t, b))
        browser.loadFinished.connect(lambda ok, b=browser: b.page().runJavaScript(AD_CLEANUP_SCRIPT))
        
        self.tab_widget.setCurrentIndex(index)
        return browser

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            browser = self.tab_widget.widget(index)
            if browser:
                browser.deleteLater()
            self.tab_widget.removeTab(index)
        else:
            self.close()

    def tab_changed(self, index):
        browser = self.tab_widget.widget(index)
        if browser:
            self.url_bar.setText(browser.url().toString())

    def update_url_text(self, qurl, browser):
        if self.tab_widget.currentWidget() == browser:
            self.url_bar.setText(qurl.toString())

    def update_tab_title(self, title, browser):
        index = self.tab_widget.indexOf(browser)
        if index != -1:
            short_title = title[:12] + '...' if len(title) > 12 else title
            self.tab_widget.setTabText(index, short_title)

    def navigate_back(self):
        current_browser = self.tab_widget.currentWidget()
        if current_browser:
            current_browser.back()

    def navigate_forward(self):
        current_browser = self.tab_widget.currentWidget()
        if current_browser:
            current_browser.forward()

    def navigate_to_url(self):
        input_text = self.url_bar.text().strip()
        if not input_text:
            return

        if " " in input_text or "." not in input_text:
            query = urllib.parse.quote(input_text)
            target_url = QUrl(f"https://www.google.com/search?q={query}")
        else:
            if not input_text.startswith("http://") and not input_text.startswith("https://"):
                input_text = "https://" + input_text
            target_url = QUrl(input_text)
        
        current_browser = self.tab_widget.currentWidget()
        if current_browser:
            current_browser.setUrl(target_url)

    def navigate_to_bookmark(self, item):
        url = "https://" + item.text()
        current_browser = self.tab_widget.currentWidget()
        if current_browser:
            current_browser.setUrl(QUrl(url))
        self.sidebar.hide()

    def show_sidebar(self):
        self.sidebar.show()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove:
            if self.sidebar.isVisible() and event.position().x() > 220:
                self.sidebar.hide()
        return super().eventFilter(obj, event)

    def increment_block_display(self, count):
        self.global_blocked_count = count
        self.counter_label.setText(f"Blocked: {count}")

    def manage_cache_lifecycle(self):
        cache_path = "trie_cache.bin"
        self.parser = RuleParser(self.trie)
        if os.path.exists(cache_path):
            file_info = QFileInfo(cache_path)
            if file_info.lastModified().secsTo(file_info.lastModified().currentDateTime()) > 86400:
                try:
                    os.remove(cache_path)
                except Exception:
                    pass
        self.parser.fetch_and_populate()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomBrowser()
    window.show()
    sys.exit(app.exec())