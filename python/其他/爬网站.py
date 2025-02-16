import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, QScrollArea, QMessageBox, QGridLayout, QHBoxLayout, QDialog, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import webbrowser
import pyperclip
import re

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MovieSearchService:
    def __init__(self):
        self.session = self.setup_session()

    def setup_session(self, retries=3, backoff_factor=0.3):
        session = requests.Session()
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def search_movies(self, query):
        url = f"https://hhzyapi.com/index.php/vod/search.html?wd={requests.utils.quote(query)}"
        try:
            response = self.session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('.list-item')
            results = [self.process_item(item) for item in items if self.process_item(item)]
            logging.info(f"完成数据获取，共 {len(results)} 条结果")
            return results
        except Exception as e:
            logging.error(f"获取数据时发生错误: {e}")
            return []

    def process_item(self, item):
        try:
            title = self.extract_title(item)
            href_elem = item.select_one('span.list-title a[href]')
            if not href_elem:
                logging.warning("未找到影片链接，跳过此条目")
                return None
            href = href_elem['href']
            detail_url = urljoin("https://hhzyapi.com/index.php/vod/search.html", href)
            play_links, img_url = self.get_play_link(detail_url)
            result = {'title': title, 'link': detail_url, 'img_url': img_url, 'play_links': play_links}
            logging.info(f"处理项目并附加到结果: {title}")
            return result
        except Exception as e:
            logging.error(f"处理项目时发生错误: {e}")
            return None

    def extract_title(self, item):
        try:
            title_elem = item.select_one('span.list-title a')
            if not title_elem:
                logging.warning("未找到影片标题或链接，跳过此条目")
                return "未知标题"
            title = title_elem.text.strip().replace(' 正片', '')
            logging.info(f"提取标题: {title}")
            return title
        except Exception as e:
            logging.error(f"提取标题时发生错误: {e}")
            return "未知标题"

    def get_play_link(self, detail_url):
        try:
            response = self.session.get(detail_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            if response.status_code != 200:
                logging.error(f"未能成功下载详情页HTML文件，状态码: {response.status_code}")
                return [], ''
            soup = BeautifulSoup(response.text, 'html.parser')
            info_div = soup.find('div', class_='vod-info')
            vod_img_div = info_div.find('div', class_='vod-img') if info_div else None
            img_tag = vod_img_div.find('img') if vod_img_div else None
            img_url = urljoin(detail_url, img_tag['src']) if img_tag and 'src' in img_tag.attrs else ''
            
            play_links = []
            vod_lists = soup.find_all('div', class_='vod-list')
            for vod_list in vod_lists:
                links_with_names = [link for link in vod_list.select('a[target="_blank"][href]') if link.get('href', '').startswith('http')]
                for link in links_with_names:
                    match = re.search(r'^(.*?)(?:\$|\s+)', link.text.strip())
                    name = match.group(1).strip() if match else "未知名称"
                    play_links.append({'name': name, 'url': link['href']})
                    
            logging.info(f"找到播放链接数量: {len(play_links)}")
            return play_links, img_url
        except Exception as e:
            logging.error(f"请求详情页时发生错误: {e}")
            return [], ''


class LoadImageThread(QThread):
    image_loaded = pyqtSignal(QPixmap)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_loaded.emit(pixmap)
        except Exception as e:
            logging.error(f"加载图片失败: {e}")


class MovieDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.service = MovieSearchService()
        self.load_image_threads = []  # List to keep track of image loading threads

    def initUI(self):
        self.setWindowTitle('影视搜索软件')
        self.setGeometry(300, 300, 800, 600)
        main_widget = QWidget(self)
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Set background color
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#f0f0f0'))
        self.setPalette(palette)

        search_layout = QHBoxLayout()
        self.search_box = QLineEdit(self)
        self.search_button = QPushButton('搜索', self)
        self.search_button.clicked.connect(self.on_search)
        self.search_box.returnPressed.connect(self.on_search)  # 绑定回车键到搜索按钮
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.scroll_area.setWidget(self.results_container)
        layout.addWidget(self.scroll_area)

    def closeEvent(self, event):
        """Override the closeEvent to properly clean up threads."""
        for thread in self.load_image_threads:
            if thread.isRunning():
                thread.quit()  # Ask the thread to quit
                thread.wait()  # Wait for it to finish
        event.accept()

    @pyqtSlot()
    def on_search(self):
        query = self.search_box.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
        try:
            self.clear_results()
            results = self.service.search_movies(query)
            self.display_results(results)
        except Exception as e:
            logging.error(f"启动搜索过程时发生错误: {e}")
            QMessageBox.critical(self, "错误", "启动搜索时发生错误，请检查日志文件。")

    def clear_results(self):
        """清除当前结果显示"""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def display_results(self, results):
        for result in results:
            widget = QWidget()
            grid_layout = QGridLayout(widget)
            
            label_img = QLabel()
            label_title = QLabel(f"<b>{result.get('title', '无标题')}</b>")
            label_title.setFont(QFont("Arial", 14, QFont.Bold))
            grid_layout.addWidget(label_title, 0, 1)

            # Separate play_links into play and download lists
            play_links = [link for link in result.get('play_links', []) if not link['url'].endswith('.m3u8')]
            download_links = [link for link in result.get('play_links', []) if link['url'].endswith('.m3u8')]

            row_index = 1
            row_index = self.create_buttons(play_links, self.open_in_browser, "播放", grid_layout, row_index)
            row_index = self.create_buttons(download_links, self.copy_to_clipboard, "下载", grid_layout, row_index)

            self.results_layout.addWidget(widget)

            # Load images asynchronously after UI elements are added to the layout
            if result['img_url']:
                thread = LoadImageThread(result['img_url'])
                thread.image_loaded.connect(lambda pixmap, lbl=label_img: self.set_image(lbl, pixmap))
                thread.finished.connect(lambda t=thread: self.load_image_threads.remove(t))  # Remove from list on finish
                self.load_image_threads.append(thread)  # Add to list
                thread.start()
                grid_layout.addWidget(label_img, 0, 0, 2, 1)

    def set_image(self, label, pixmap):
        label.setPixmap(pixmap.scaledToWidth(150))

    def create_buttons(self, links, action, text_prefix, layout, start_row):
        if len(links) > 1:
            button = QPushButton(f"{text_prefix}列表")
            button.clicked.connect(lambda checked, ls=links, act=action, prefix=text_prefix: self.show_playlist(ls, act, prefix))
            layout.addWidget(button, start_row, 1)
            return start_row + 1
        elif len(links) == 1:
            button = QPushButton(text_prefix)
            button.clicked.connect(lambda checked, url=links[0]['url']: action(url))
            layout.addWidget(button, start_row, 1)
            return start_row + 1
        return start_row

    def show_playlist(self, links, action, prefix):
        """显示播放或下载链接列表对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{prefix}列表")
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)
        for link in links:
            item = QListWidgetItem(f"{link['name']}")
            item.setData(Qt.UserRole, link['url'])
            list_widget.addItem(item)

        list_widget.itemClicked.connect(lambda item: action(item.data(Qt.UserRole)))
        layout.addWidget(list_widget)

        dialog.exec_()

    def open_in_browser(self, url):
        """在默认浏览器中打开提供的URL"""
        webbrowser.open(url)

    def copy_to_clipboard(self, url):
        """将提供的URL复制到剪贴板"""
        pyperclip.copy(url)
        QMessageBox.information(self, "提示", "链接已复制到剪贴板")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MovieDisplayApp()
    window.show()
    sys.exit(app.exec_())