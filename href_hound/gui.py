#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import webbrowser

from PyQt5 import QtCore, QtWidgets

from .config import Config
from .crawler import LinkChecker
from .reporter import generate_report


class LinkCheckerWorker(QtCore.QThread):
    """
    リンクチェック処理をバックグラウンド実行するワーカースレッド。
    """
    progress = QtCore.pyqtSignal(int, int, str)
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def run(self):
        # キャンセル判定用イベント
        self.config.cancel_event.clear()
        try:
            runner = LinkChecker(self.config, progress_callback=self._on_progress)
            import asyncio

            results = asyncio.run(runner.run())
            generate_report(results, self.config.output)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, pages: int, errors: int, current: str):
        self.progress.emit(pages, errors, current)

    def stop(self):
        self.config.cancel_event.set()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Set window title in English to avoid titlebar font issues
        self.setWindowTitle("Link Checker GUI")
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        form = QtWidgets.QFormLayout()
        # 起点URL
        self.le_start = QtWidgets.QLineEdit()
        form.addRow("起点URL:", self.le_start)
        # 出力レポート
        h_out = QtWidgets.QHBoxLayout()
        self.le_output = QtWidgets.QLineEdit("report.html")
        btn_out = QtWidgets.QPushButton("参照")
        btn_out.clicked.connect(self._browse_output)
        h_out.addWidget(self.le_output)
        h_out.addWidget(btn_out)
        form.addRow("出力レポート:", h_out)
        # クロール範囲
        hb = QtWidgets.QHBoxLayout()
        self.cb_same = QtWidgets.QCheckBox("同一オリジンのみ")
        self.cb_same.setChecked(True)
        self.cb_sub = QtWidgets.QCheckBox("サブドメインを含む")
        hb.addWidget(self.cb_same)
        hb.addWidget(self.cb_sub)
        form.addRow("クロール範囲:", hb)
        # 最大深度 (-1: 無制限)
        self.sp_depth = QtWidgets.QSpinBox()
        self.sp_depth.setRange(-1, 100)
        self.sp_depth.setValue(3)
        form.addRow("最大深度 (-1: 無制限):", self.sp_depth)
        # 除外パターン
        self.te_exclude = QtWidgets.QPlainTextEdit()
        form.addRow("除外URLパターン(1行1つ):", self.te_exclude)
        # 包含パターン
        self.te_include = QtWidgets.QPlainTextEdit()
        form.addRow("包含URLパターン(1行1つ):", self.te_include)
        # リソースチェック
        self.cb_res = QtWidgets.QCheckBox("リソースリンクもチェック (img, link, script)")
        form.addRow("", self.cb_res)
        # User-Agent
        self.le_agent = QtWidgets.QLineEdit("LinkChecker/1.0")
        form.addRow("User-Agent:", self.le_agent)
        # タイムアウト
        self.sp_timeout = QtWidgets.QDoubleSpinBox()
        self.sp_timeout.setRange(1, 3600)
        self.sp_timeout.setValue(10.0)
        form.addRow("タイムアウト(秒):", self.sp_timeout)
        # 同時リクエスト数
        self.sp_conc = QtWidgets.QSpinBox()
        self.sp_conc.setRange(1, 100)
        self.sp_conc.setValue(5)
        form.addRow("同時リクエスト数:", self.sp_conc)
        # リクエスト間隔
        self.sp_delay = QtWidgets.QDoubleSpinBox()
        self.sp_delay.setRange(0, 60)
        self.sp_delay.setValue(0.0)
        form.addRow("リクエスト間隔(秒):", self.sp_delay)
        # エラーコード
        self.le_error_codes = QtWidgets.QLineEdit()
        form.addRow("リンク切れ判定ステータスコード (カンマ区切り):", self.le_error_codes)

        layout.addLayout(form)
        # ボタン
        hb2 = QtWidgets.QHBoxLayout()
        self.btn_start = QtWidgets.QPushButton("開始")
        self.btn_stop = QtWidgets.QPushButton("中断")
        self.btn_open = QtWidgets.QPushButton("レポートを開く")
        self.btn_stop.setEnabled(False)
        self.btn_open.setEnabled(False)
        hb2.addWidget(self.btn_start)
        hb2.addWidget(self.btn_stop)
        hb2.addWidget(self.btn_open)
        layout.addLayout(hb2)
        # 進捗 & ログ
        self.lbl_status = QtWidgets.QLabel("Ready")
        layout.addWidget(self.lbl_status)
        self.te_log = QtWidgets.QPlainTextEdit()
        self.te_log.setReadOnly(True)
        layout.addWidget(self.te_log)

        # シグナル接続
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_open.clicked.connect(self._on_open)
        self.cb_sub.stateChanged.connect(self._on_sub_toggle)

    def _browse_output(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "出力レポートを選択", "", "HTML Files (*.html);;All Files (*)"
        )
        if path:
            self.le_output.setText(path)

    def _on_sub_toggle(self, state):
        if state == QtCore.Qt.Checked:
            self.cb_same.setChecked(True)

    def _on_start(self):
        start_url = self.le_start.text().strip()
        output = self.le_output.text().strip()
        if not start_url or not output:
            QtWidgets.QMessageBox.warning(self, "Error", "起点URLと出力ファイルは必須です。")
            return
        config = Config(
            start_url=start_url,
            output=output,
            same_origin=self.cb_same.isChecked(),
            include_subdomains=self.cb_sub.isChecked(),
            max_depth=self.sp_depth.value(),
            exclude=[l for l in self.te_exclude.toPlainText().splitlines() if l.strip()],
            include=[l for l in self.te_include.toPlainText().splitlines() if l.strip()],
            check_resources=self.cb_res.isChecked(),
            user_agent=self.le_agent.text().strip(),
            timeout=self.sp_timeout.value(),
            concurrency=self.sp_conc.value(),
            delay=self.sp_delay.value(),
            error_codes=[int(x) for x in self.le_error_codes.text().split(",") if x.strip()]
        )
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.te_log.clear()
        self.lbl_status.setText("Starting...")
        self._worker = LinkCheckerWorker(config)
        self._worker.progress.connect(self._update_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_stop(self):
        # User requested stop: signal worker and forcibly terminate thread
        if self._worker:
            # Disable stop button to prevent repeated clicks
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("Stopping...")
            # Signal cancellation to crawler
            self._worker.stop()
            # Forcefully terminate the thread (immediate stop)
            self._worker.terminate()
            # Wait for thread to finish
            self._worker.wait()
            # Reset UI state
            self.btn_start.setEnabled(True)
            self.btn_open.setEnabled(False)
            self.lbl_status.setText("Stopped")

    def _on_open(self):
        webbrowser.open(f"file://{self.le_output.text().strip()}")

    def _update_progress(self, pages: int, errors: int, current: str):
        self.lbl_status.setText(f"Checked pages: {pages}, errors: {errors}")
        self.te_log.appendPlainText(f"{current}")

    def _on_finished(self):
        self.lbl_status.setText("Finished")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_open.setEnabled(True)

    def _on_error(self, msg: str):
        self.lbl_status.setText(f"Error: {msg}")
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

def main():
    app = QtWidgets.QApplication(sys.argv)
    # 日本語フォントを優先設定。見つからない場合は警告
    from PyQt5.QtGui import QFontDatabase, QFont
    db = QFontDatabase()
    default_pt = app.font().pointSize()
    if default_pt <= 0:
        default_pt = 10
    preferred = [
        "Meiryo", "Yu Gothic", "Noto Sans CJK JP",
        "TakaoPGothic", "MS PGothic", "MS Gothic",
        "Hiragino Maru Gothic Pro"
    ]
    families = db.families()
    selected = False
    for fam in preferred:
        if fam in families:
            app.setFont(QFont(fam, default_pt))
            selected = True
            break
    if not selected:
        # Warn user in English if no Japanese font found
        QtWidgets.QMessageBox.warning(
            None,
            "Japanese font not detected",
            "No Japanese font was detected on your system, so the GUI may display garbled text.\n"
            "If you are using Ubuntu on WSL2, please install a Japanese font, e.g.:\n"
            "  sudo apt update && sudo apt install fonts-noto-cjk"
        )
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()