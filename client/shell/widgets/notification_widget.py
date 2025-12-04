"""
通知中心组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from typing import List, Dict, Any
from datetime import datetime

from ..styles.theme import CURRENT_THEME as t


class NotificationItem(QWidget):
    """通知项"""
    
    clicked = Signal(dict)
    dismissed = Signal(str)
    
    def __init__(self, notification: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.notification = notification
        self.setFixedHeight(80)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        notif = self.notification
        level = notif.get('level', 'info')
        
        # 颜色映射
        colors = {
            'info': (t.info, '#EFF6FF'),
            'success': (t.success, '#ECFDF5'),
            'warning': (t.warning, '#FFFBEB'),
            'error': (t.error, '#FEF2F2')
        }
        icon_color, bg_color = colors.get(level, colors['info'])
        
        # 图标映射
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'invite': '📨',
            'achievement': '🏆',
            'friend': '👋'
        }
        icon = icons.get(notif.get('icon', level), 'ℹ️')
        
        # 图标
        icon_label = QLabel(icon)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 8px;
            font-size: 20px;
        """)
        layout.addWidget(icon_label)
        
        # 内容
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        content_layout.setAlignment(Qt.AlignVCenter)
        
        title = QLabel(notif.get('title', '通知'))
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {t.text_display};
        """)
        content_layout.addWidget(title)
        
        message = QLabel(notif.get('content', ''))
        message.setWordWrap(True)
        message.setMaximumWidth(250)
        message.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
        """)
        content_layout.addWidget(message)
        
        layout.addLayout(content_layout, 1)
        
        # 时间
        time_str = notif.get('time', '')
        if not time_str:
            time_str = datetime.now().strftime('%H:%M')
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            font-size: 11px;
            color: {t.text_caption};
        """)
        layout.addWidget(time_label)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t.text_caption};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {t.error};
            }}
        """)
        close_btn.clicked.connect(lambda: self.dismissed.emit(notif.get('id', '')))
        layout.addWidget(close_btn)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.notification)
        super().mousePressEvent(event)


class NotificationCenter(QWidget):
    """通知中心面板"""
    
    notification_clicked = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications: List[Dict] = []
        self.setFixedWidth(380)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 头部
        header = QFrame()
        header.setStyleSheet(f"""
            background-color: {t.bg_card};
            border-bottom: 1px solid {t.border_light};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        title = QLabel("🔔 通知中心")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.count_label = QLabel("0 条未读")
        self.count_label.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
        """)
        header_layout.addWidget(self.count_label)
        
        clear_btn = QPushButton("清空")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t.primary};
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {t.primary_hover};
            }}
        """)
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        # 通知列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background-color: {t.bg_base}; border: none;")
        
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(12, 12, 12, 12)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)
    
    def add_notification(self, notification: Dict[str, Any]):
        """添加通知"""
        if 'id' not in notification:
            notification['id'] = str(len(self.notifications))
        if 'time' not in notification:
            notification['time'] = datetime.now().strftime('%H:%M')
        
        self.notifications.insert(0, notification)
        
        item = NotificationItem(notification)
        item.clicked.connect(self.notification_clicked.emit)
        item.dismissed.connect(self._remove_notification)
        
        self.list_layout.insertWidget(0, item)
        self._update_count()
    
    def _remove_notification(self, notif_id: str):
        """移除通知"""
        self.notifications = [n for n in self.notifications if n.get('id') != notif_id]
        
        # 移除 UI
        for i in range(self.list_layout.count() - 1):  # -1 for stretch
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, NotificationItem):
                    if widget.notification.get('id') == notif_id:
                        widget.deleteLater()
                        break
        
        self._update_count()
    
    def clear_all(self):
        """清空所有通知"""
        self.notifications.clear()
        
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._update_count()
    
    def _update_count(self):
        """更新计数"""
        count = len(self.notifications)
        self.count_label.setText(f"{count} 条未读" if count else "无通知")


class ToastNotification(QFrame):
    """Toast 提示（右下角弹出）"""
    
    def __init__(self, title: str, message: str, level: str = "info", duration: int = 3000, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.setup_ui(title, message, level)
        
        # 自动消失
        QTimer.singleShot(duration, self.close)
    
    def setup_ui(self, title: str, message: str, level: str):
        self.setFixedSize(300, 80)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 颜色
        colors = {
            'info': t.info,
            'success': t.success,
            'warning': t.warning,
            'error': t.error
        }
        color = colors.get(level, t.info)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {t.text_display};
        """)
        layout.addWidget(title_label)
        
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
        """)
        layout.addWidget(msg_label)

