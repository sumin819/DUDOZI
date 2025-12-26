# This Python file uses the following encoding: utf-8
import sys
import os
import pytz
from datetime import datetime
import cv2
from PySide6.QtWidgets import (
    QApplication, QMainWindow,
    QFrame, QLabel, QVBoxLayout, QSizePolicy, QHBoxLayout
) 
from PySide6.QtCore import QTimer, Qt
from PySide6.QtCore import QEvent

from ui_form import Ui_MainWindow
from api.sidebar import on_toggle_system, send_agv_start, send_agv_pause
from api.camera import send_move, update_camera_frame, start_camera_stream, stop_camera_stream
from api.analysis import fetch_task_list, get_latest_cycle_id
from api.history import fetch_agv_history
from widgets.analysis_widget import create_analysis_card, clear_layout, format_cycle_id
from widgets.history_widget import create_history_card


# ================================
# CONFIG
# ================================
AGV_ID = "AGV1"
TIMEZONE = pytz.timezone("Asia/Seoul")
DEFAULT_CYCLE_ID = "2025_12_17_1936"


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DUDOZI")

        # ================================
        # UI 로드
        # ================================
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ================================
        # QSS 적용
        # ================================
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(base_dir, "styles", "dark_glass.css")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        # ================================
        # START / STOP
        # ================================
        self.ui.toggleSystem.setCheckable(True)
        self.ui.toggleSystem.clicked.connect(
            lambda: on_toggle_system(self)
        )

        # ================================
        # 카메라 / 타이머
        # ================================
        self.cap = None
        self.cam_timer = QTimer(self)
        self.cam_timer.timeout.connect(lambda: update_camera(self))

        # ================================
        # 서버 상태 동기화
        # ================================
        self.sync_run_state()

        # ================================
        # 방향키 (테스트용)
        # ================================
        self.ui.btnUp.clicked.connect(lambda: send_move(self, "FORWARD"))
        self.ui.btnDown.clicked.connect(lambda: send_move(self, "BACKWARD"))
        self.ui.btnLeft.clicked.connect(lambda: send_move(self, "LEFT"))
        self.ui.btnRight.clicked.connect(lambda: send_move(self, "RIGHT"))

        # ================================
        # Analysis 새로고침
        # ================================
        self.ui.analysisScroll.setWidgetResizable(True)
        self.ui.analysisScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.analysisScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.ui.analysisContent.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        # analysisContent에 설정된 레이아웃을 가져와 정렬 설정
        if self.ui.analysisContent.layout() is None:
            self.llmLayout = QVBoxLayout(self.ui.analysisContent)
            self.llmLayout.setAlignment(Qt.AlignTop)
            self.llmLayout.setContentsMargins(5, 5, 5, 5)
            self.llmLayout.setSpacing(5)
        else:
            self.llmLayout = self.ui.analysisContent.layout()

        # ================================
        # History Scroll / Layout 준비
        # ================================
        self.ui.historyScroll.setWidgetResizable(True)
        self.ui.historyScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.historyScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # historyContent 안에 레이아웃이 없으면 생성
        if self.ui.historyContent.layout() is None:
            self.historyLayout = QHBoxLayout(self.ui.historyContent)
            self.historyLayout.setContentsMargins(10, 10, 10, 10)
            self.historyLayout.setSpacing(10)
            self.historyLayout.setAlignment(Qt.AlignLeft)
        else:
            self.historyLayout = self.ui.historyContent.layout()

        self.ui.historyScroll.viewport().installEventFilter(self)
        self.ui.historyScroll.setFocusPolicy(Qt.StrongFocus)

        # ================================
        # 초기 상태
        # ================================
        self.lock_controls()
        self.enter_stopped_state()

        # ================================
        # 시간 업데이트
        # ================================
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)


        # ================================
        # Analysis 이벤트 연결 (중복 제거)
        # ================================
        # 기존에 DEFAULT_CYCLE_ID를 직접 넣던 lambda 연결은 삭제하고
        # 최신 ID를 먼저 찾는 refresh_analysis만 연결합니다.
        self.ui.refreshBtn.clicked.connect(self.refresh_analysis)
        self.ui.refreshHistoryBtn.clicked.connect(self.refresh_history)

        # ===============================
        # 한 사이클 돌기
        # ===============================
        self.mission_state = "IDLE"
        # IDLE | RUNNING | PAUSED
        self.ui.btnStart.clicked.connect(self.on_start_button)


    # ==================================================
    # START / STOP 상태
    # ==================================================
    def sync_run_state(self):
        # sidebar.py 쪽 로직 사용
        pass

    def enter_running_state(self):
        self.ui.toggleSystem.setChecked(True)
        self.ui.toggleSystem.setText("OFF")
        self.ui.lblAgvState.setText("SYSTEM: RUNNING")
        self.ui.cameraView.setText("SYSTEM: RUNNING\nEnter Start Button")

        self.ui.btnStart.setEnabled(True)
        self.unlock_controls()

        self.unlock_controls()

        self.ui.refreshBtn.setEnabled(True)
        self.ui.refreshHistoryBtn.setEnabled(True)
        self.refresh_analysis()
        self.refresh_history()


    def enter_stopped_state(self):
        self.ui.toggleSystem.setChecked(False)
        self.ui.toggleSystem.setText("ON")
        self.ui.lblAgvState.setText("SYSTEM: OFF")

        self.mission_state = "IDLE"
        self.current_cycle_id = None

        self.ui.btnStart.setText("START")
        self.ui.btnStart.setEnabled(False)

        self.lock_controls()

        if self.cam_timer.isActive():
                self.cam_timer.stop()

        stop_camera_stream(self)

        self.ui.cameraView.setText("SYSTEM OFF")
        self.ui.cameraView.setAlignment(Qt.AlignCenter)

        self.show_analysis_placeholder(
            "Analysis is available when SYSTEM is RUNNING"
        )
        self.show_history_placeholder("SYSTEM OFF")
        self.ui.refreshHistoryBtn.setEnabled(False)
        self.ui.refreshBtn.setEnabled(False)

    # ==================================================
    # 사이클 돌기
    # ==================================================
    def on_start_button(self):
        if not self.ui.toggleSystem.isChecked():
            return  # SYSTEM OFF

        if self.mission_state == "IDLE":
            self.start_mission()

        elif self.mission_state == "RUNNING":
            self.pause_mission()

        elif self.mission_state == "PAUSED":
            self.start_mission()

    def start_mission(self):
        ok = send_agv_start(agv_id=AGV_ID)
        if not ok:
            print("[ERROR] Mission start failed")
            return

        self.mission_state = "RUNNING"

        self.ui.btnStart.setText("STOP")
        self.ui.lblAgvState.setText("SYSTEM: RUNNING")

        # MJPEG 스트림 시작 (스레드)
        start_camera_stream(self)

        print("[MISSION] Mission started")



    def pause_mission(self):
        ok = send_agv_pause(AGV_ID)
        if not ok:
            print("Mission pause failed")
            return

        self.mission_state = "PAUSED"
        self.ui.btnStart.setText("START")
        self.ui.lblAgvState.setText("SYSTEM: PAUSED")

        print("Mission paused")


    # ==================================================
    # Analysis UI
    # ==================================================
    def load_analysis(self, cycle_id: str):
        try:
            data = fetch_task_list(cycle_id)

            if data.get("status") != "ready":
                return

            layout = self.llmLayout
            clear_layout(layout)

            # ----------------------------
            # 분석 시간 라벨 (한 번만)
            # ----------------------------
            cycle_time = format_cycle_id(cycle_id)

            time_label = QLabel(f"Analysis Time : {cycle_time}")
            time_label.setStyleSheet("""
                color: #AAAAAA;
                font-size: 10px;
                padding-left: 4px;
                padding-bottom: 6px;
            """)
            time_label.setAlignment(Qt.AlignLeft)

            layout.addWidget(time_label)

            # ----------------------------
            # 카드들 추가
            # ----------------------------
            task_list = data.get("task_list", [])
            summary_dict = data.get("summary", {})

            for task in task_list:
                node = task["node"]
                card = create_analysis_card(
                    node=node,
                    action=task["action"],
                    reason=task.get("reason", ""),
                    summary=summary_dict.get(node, "")
                )
                layout.addWidget(card)

            layout.addStretch(1)

        except Exception as e:
            print("분석 로드 실패:", e)


    def refresh_analysis(self):
        # ❌ OFF 상태면 아무것도 안 함
        if not self.ui.toggleSystem.isChecked():
            return

        latest_id = get_latest_cycle_id()
        if latest_id:
            self.load_analysis(latest_id)
        else:
            self.load_analysis(DEFAULT_CYCLE_ID)


    def show_analysis_placeholder(self, text: str):
        clear_layout(self.llmLayout)

        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            padding: 12px;
        """)

        self.llmLayout.addWidget(placeholder)

    # ==================================================
    # 히스토리 관리
    # ==================================================
    def clear_history(self):
        layout = self.historyLayout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_history_placeholder(self, text: str):
        self.clear_history()

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #666666;
            font-size: 11px;
            padding: 12px;
        """)

        self.historyLayout.addWidget(label)
        self.historyLayout.addStretch(1)

    def refresh_history(self):
        # ❌ OFF 상태면 아무것도 안 함
        if not self.ui.toggleSystem.isChecked():
            return

        try:
            data = fetch_agv_history()
            if not data:
                self.show_history_placeholder("No history data")
                return

            observations = data.get("observations", [])
            if not observations:
                self.show_history_placeholder("No observations")
                return

            self.clear_history()

            for obs in observations:
                card = create_history_card(
                    node=obs.get("node", ""),
                    result=obs.get("yolo", {}).get("result", "unknown"),
                    image_url=obs.get("image_url", "")
                )
                self.historyLayout.addWidget(card)

            # 가로 스크롤 여유
            self.historyLayout.addStretch(1)

        except Exception as e:
            print("History refresh failed:", e)
            self.show_history_placeholder("History load error")


    def eventFilter(self, obj, event):
        if obj is self.ui.historyScroll.viewport() and event.type() == QEvent.Wheel:
            # 휠 delta: 위로 굴리면 +, 아래로 굴리면 -
            delta = event.angleDelta().y()

            bar = self.ui.historyScroll.horizontalScrollBar()

            # 자연스러운 방향: 아래로 휠 → 오른쪽 이동
            bar.setValue(bar.value() - delta)

            event.accept()
            return True

        return super().eventFilter(obj, event)


    # ==================================================
    # 컨트롤 잠금 / 해제
    # ==================================================
    def lock_controls(self):
        for w in [
            self.ui.btnDashboard,
            self.ui.btnStart,
            self.ui.btnHistory,
            self.ui.btnEmergency,
            self.ui.btnUp,
            self.ui.btnDown,
            self.ui.btnLeft,
            self.ui.btnRight,
        ]:
            w.setEnabled(False)

    def unlock_controls(self):
        for w in [
            self.ui.btnDashboard,
            self.ui.btnStart,
            self.ui.btnHistory,
            self.ui.btnEmergency,
            self.ui.btnUp,
            self.ui.btnDown,
            self.ui.btnLeft,
            self.ui.btnRight,
        ]:
            w.setEnabled(True)

    # ==================================================
    # 시간
    # ==================================================
    def update_time(self):
        now = datetime.now(TIMEZONE)
        self.ui.lblTime.setText(now.strftime("%Y-%m-%d %H:%M"))

    # ==================================================
    # 종료
    # ==================================================
    def closeEvent(self, event):
        try:
            if self.cam_timer.isActive():
                self.cam_timer.stop()
            if self.cap:
                self.cap.release()
        except Exception:
            pass
        super().closeEvent(event)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

