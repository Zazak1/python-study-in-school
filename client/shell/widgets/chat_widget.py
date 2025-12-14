"""
聊天组件 - 现代化浅色风格
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent
from typing import List, Dict, Any
from datetime import datetime

from ..styles.theme import CURRENT_THEME as t


class MessageBubble(QWidget):
    """消息气泡"""
    
    def __init__(self, msg_data: Dict[str, Any], is_self: bool = False, parent=None):
        super().__init__(parent)
        self.msg_data = msg_data
        self.is_self = is_self
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        msg = self.msg_data
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        
        if self.is_self:
            layout.addStretch()
        
        # 消息容器
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)
        
        if self.is_self:
            # 自己的消息：蓝色背景，白色文字
            bubble.setStyleSheet(
                f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {t.primary}, stop:1 #4338CA);
                    border-radius: 14px;
                    border-top-right-radius: 6px;
                }}
                """
            )
            text_color = "#FFFFFF"
            time_color = "rgba(255, 255, 255, 0.7)"
        else:
            # 对方的消息：白色背景，深色文字
            bubble.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {t.bg_card};
                    border: 1px solid {t.border_light};
                    border-radius: 14px;
                    border-top-left-radius: 6px;
                }}
                """
            )
            text_color = "#111827"
            time_color = "#9CA3AF"
            
            # 发送者名称
            sender = QLabel(msg.get('sender_name', '未知'))
            sender.setStyleSheet(f"""
                font-size: 11px;
                font-weight: 600;
                color: {msg.get('sender_color', '#2563EB')};
            """)
            bubble_layout.addWidget(sender)
        
        # 消息内容
        content = QLabel(msg.get('content', ''))
        content.setWordWrap(True)
        content.setMaximumWidth(220)
        content.setStyleSheet(f"""
            font-size: 13px;
            color: {text_color};
        """)
        bubble_layout.addWidget(content)
        
        # 时间
        time_str = msg.get('time', '')
        if not time_str:
            time_str = datetime.now().strftime('%H:%M')
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            font-size: 10px;
            color: {time_color};
        """)
        time_label.setAlignment(Qt.AlignRight)
        bubble_layout.addWidget(time_label)
        
        layout.addWidget(bubble)
        
        if not self.is_self:
            layout.addStretch()


class ChatInput(QLineEdit):
    """聊天输入框"""
    
    send_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入消息...")
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            text = self.text().strip()
            if text:
                self.send_message.emit(text)
                self.clear()
        else:
            super().keyPressEvent(event)


class ChatWidget(QWidget):
    """聊天面板"""
    
    message_sent = Signal(str, str)  # channel, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_channel = "lobby"
        self.messages: List[Dict] = []
        self.local_user_id = ""
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 频道切换
        channel_layout = QHBoxLayout()
        channel_layout.setSpacing(4)
        
        channels = [
            ('lobby', '💬 大厅'),
            ('room', '🏠 房间'),
            ('team', '👥 队伍')
        ]
        
        self.channel_btns = {}
        for channel_id, channel_name in channels:
            btn = QPushButton(channel_name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(channel_id == 'lobby')
            
            # 扁平化标签样式
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #6B7280;
                    border: none;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                    color: #111827;
                }
                QPushButton:checked {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    font-weight: 600;
                }
            """)
            btn.clicked.connect(lambda checked, cid=channel_id: self._switch_channel(cid))
            channel_layout.addWidget(btn)
            self.channel_btns[channel_id] = btn
        
        channel_layout.addStretch()
        layout.addLayout(channel_layout)
        
        # 消息区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(4, 8, 4, 8)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll.setWidget(self.messages_container)
        layout.addWidget(self.scroll, 1)
        
        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # 表情按钮
        emoji_btn = QPushButton("😊")
        emoji_btn.setFixedSize(36, 36)
        emoji_btn.setCursor(Qt.PointingHandCursor)
        emoji_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: none;
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        input_layout.addWidget(emoji_btn)
        
        # 输入框
        self.chat_input = ChatInput()
        self.chat_input.send_message.connect(self._on_send)
        input_layout.addWidget(self.chat_input, 1)
        
        # 发送按钮 - 直接设置完整样式
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(56, 36)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.primary};
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t.primary_hover};
            }}
        """)
        send_btn.clicked.connect(lambda: self._on_send(self.chat_input.text()))
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
    
    def set_local_user(self, user_id: str):
        self.local_user_id = user_id
    
    def _switch_channel(self, channel: str):
        self.current_channel = channel
        for cid, btn in self.channel_btns.items():
            btn.setChecked(cid == channel)
        self._clear_messages()
    
    def _clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_message(self, msg_data: Dict[str, Any]):
        is_self = msg_data.get('sender_id') == self.local_user_id
        
        # 移除 stretch
        if self.messages_layout.count() > 0:
            self.messages_layout.takeAt(self.messages_layout.count() - 1)
        
        bubble = MessageBubble(msg_data, is_self)
        self.messages_layout.addWidget(bubble)
        self.messages_layout.addStretch()
        
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_send(self, text: str):
        text = text.strip()
        if not text:
            return
        self.chat_input.clear()
        self.message_sent.emit(self.current_channel, text)
        self.add_message({
            'sender_id': self.local_user_id,
            'sender_name': '我',
            'content': text,
            'time': datetime.now().strftime('%H:%M')
        })
