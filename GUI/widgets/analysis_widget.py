from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QSizePolicy

def create_analysis_card(node, action, reason, summary):
    # ---------- 외부 Wrapper (레이아웃용) ----------
    wrapper = QWidget()
    wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

    wrapper_layout = QVBoxLayout(wrapper)
    wrapper_layout.setContentsMargins(5, 5, 5, 5)  # 🔥 오른쪽 여유 크게
    wrapper_layout.setSpacing(0)

    # ---------- 실제 카드 배경 ----------
    card_bg = QFrame()
    card_bg.setObjectName("analysisCardBg")
    card_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

    accent_color = "#00C8FF"
    if "치료제" in action:
        accent_color = "#FF3C3C"
    elif "비료" in action:
        accent_color = "#00FF99"

    card_bg.setStyleSheet(f"""
        QFrame#analysisCardBg {{
            background-color: rgba(255,255,255,20);
            border: 1px solid rgba(255,255,255,30);
            border-left: 4px solid {accent_color};
            border-radius: 10px;   /* 🔥 이제 아무리 커도 안 잘림 */
        }}
    """)

    # ---------- 내용 레이아웃 ----------
    content_layout = QVBoxLayout(card_bg)
    content_layout.setContentsMargins(10, 10, 10, 10)
    content_layout.setSpacing(6)

    title = QLabel(f"📍 {node.upper()} : {action}")
    title.setStyleSheet(f"font-weight:bold; color:{accent_color};")

    desc = QLabel(f"<b>사유:</b> {reason}")
    desc.setWordWrap(True)

    summary_lbl = QLabel(summary)
    summary_lbl.setWordWrap(True)
    summary_lbl.setStyleSheet("color:#AAAAAA; font-size:10px;")

    content_layout.addWidget(title)
    content_layout.addWidget(desc)
    content_layout.addWidget(summary_lbl)

    # ---------- 합치기 ----------
    wrapper_layout.addWidget(card_bg)

    return wrapper

def clear_layout(layout):
    """레이아웃 내부의 위젯과 Stretch 등 모든 아이템을 제거"""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()

def format_cycle_id(cycle_id: str) -> str:
    """
    2025_12_17_1936 -> 2025-12-17 19:36
    """
    try:
        yyyy, mm, dd, hhmm = cycle_id.split("_")
        return f"{yyyy}-{mm}-{dd} {hhmm[:2]}:{hhmm[2:]}"
    except Exception:
        return cycle_id


