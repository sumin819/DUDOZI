# widgets/history_widget.py
import requests
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QSizePolicy
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def show_image_popup(image_url: str):
    """클릭 시 원본 이미지 팝업"""
    dialog = QDialog()
    dialog.setWindowTitle("관찰 데이터 상세 보기")
    dialog.setFixedSize(600, 600)
    dialog.setStyleSheet("background-color: #12141A;")

    layout = QVBoxLayout(dialog)
    label = QLabel("이미지 로딩 중...")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)

    try:
        res = requests.get(image_url, timeout=5)
        if res.status_code == 200:
            pix = QPixmap()
            pix.loadFromData(res.content)
            label.setPixmap(pix.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setText("")
    except:
        label.setText("이미지를 불러올 수 없습니다.")

    dialog.exec()

def create_history_card(node: str, result: str, image_url: str):
    """개편된 가로형 히스토리 카드"""

    # 상태별 색상 및 텍스트 설정
    status_map = {
        "normal": ("정상", "#00FF99"),
        "abnormal": ("비정상", "#FF3C3C"),
        "unknown": ("미확인", "#AAAAAA")
    }
    status_text, color = status_map.get(result, ("알 수 없음", "#AAAAAA"))

    card = QFrame()
    card.setFixedSize(220, 80) # 전체 카드 크기 고정
    card.setObjectName("historyCard")
    card.setStyleSheet(f"""
        QFrame#historyCard {{
            background-color: rgba(255, 255, 255, 15);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 20);
        }}
    """)

    # 메인 레이아웃: 가로 배치
    main_layout = QHBoxLayout(card)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(12)

    # 1. 왼쪽: 고정 크기 사진 영역
    img_label = QLabel()
    img_label.setFixedSize(64, 64) # 사진 크기 동일하게 고정
    img_label.setStyleSheet("background-color: #000; border-radius: 8px;")
    img_label.setAlignment(Qt.AlignCenter)

    if image_url:
        try:
            res = requests.get(image_url, timeout=3)
            pix = QPixmap()
            pix.loadFromData(res.content)
            # AspectRatioByExpanding을 사용하여 꽉 차게 만든 후 잘라냄 (미리보기 효과)
            img_label.setPixmap(pix.scaled(64, 64, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            img_label.setCursor(Qt.PointingHandCursor)
            img_label.mousePressEvent = lambda e: show_image_popup(image_url)
        except:
            img_label.setText("ERR")

    # 2. 오른쪽: 노드 정보 및 상태 (세로 배치)
    info_layout = QVBoxLayout()
    info_layout.setSpacing(2)
    info_layout.setAlignment(Qt.AlignVCenter)

    lbl_title = QLabel("Cycle History")
    lbl_title.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold;")

    lbl_node = QLabel(f"Node {node.upper()}")
    lbl_node.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

    lbl_status = QLabel(status_text)
    lbl_status.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")

    info_layout.addWidget(lbl_title)
    info_layout.addWidget(lbl_node)
    info_layout.addWidget(lbl_status)

    main_layout.addWidget(img_label)
    main_layout.addLayout(info_layout)
    main_layout.addStretch()

    return card
