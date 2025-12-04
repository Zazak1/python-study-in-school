"""
聊天组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QFrame,
    QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent
from typing import List, Dict, Any
from datetime import datetime


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
        layout.setContentsMargins(8, 4, 8, 4)
        
        if self.is_self:
            layout.addStretch()
        
        # 消息容器
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(4)
        
        if self.is_self:
            bubble.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00D4FF, stop:1 #0099CC);
                    border-radius: 12px;
                    border-top-right-radius: 4px;
                }
            """)
            text_color = "#0A0E17"
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background: #1F2937;
                    border-radius: 12px;
                    border-top-left-radius: 4px;
                }
            """)
            text_color = "#F0F4F8"
            
            # 发送者名称
            sender = QLabel(msg.get('sender_name', '未知'))
            sender.setStyleSheet(f"""
                font-size: 11px;
                font-weight: bold;
                color: {msg.get('sender_color', '#00D4FF')};
                background: transparent;
            """)
            bubble_layout.addWidget(sender)
        
        # 消息内容
        content = QLabel(msg.get('content', ''))
        content.setWordWrap(True)
        content.setMaximumWidth(280)
        content.setStyleSheet(f"""
            font-size: 13px;
            color: {text_color};
            background: transparent;
        """)
        bubble_layout.addWidget(content)
        
        # 时间
        time_str = msg.get('time', '')
        if not time_str:
            time_str = datetime.now().strftime('%H:%M')
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            font-size: 10px;
            color: {'rgba(10, 14, 23, 0.6)' if self.is_self else '#64748B'};
            background: transparent;
        """)
        time_label.setAlignment(Qt.AlignRight if self.is_self else Qt.AlignLeft)
        bubble_layout.addWidget(time_label)
        
        layout.addWidget(bubble)
        
        if not self.is_self:
            layout.addStretch()


class ChatInput(QLineEdit):
    """聊天输入框 - 支持 Enter 发送"""
    
    send_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入消息...")
        self.setStyleSheet("""
            QLineEdit {
                background: #1F2937;
                border: 2px solid #2d3748;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                color: #F0F4F8;
            }
            QLineEdit:focus {
                border-color: #00D4FF;
            }
        """)
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理按键"""
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
        self.current_channel = "lobby"  # lobby, room, team
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
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #64748B;
                    border: none;
                    padding: 6px 12px;
                    font-size: 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    color: #94A3B8;
                    background: #1F2937;
                }
                QPushButton:checked {
                    color: #00D4FF;
                    background: rgba(0, 212, 255, 0.1);
                    font-weight: bold;
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
                background: #111827;
                border: 1px solid #2d3748;
                border-radius: 8px;
            }
        """)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(4, 8, 4, 8)
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch()
        
        self.scroll.setWidget(self.messages_container)
        layout.addWidget(self.scroll, 1)
        
        # 输入区域
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        # 表情按钮
        emoji_btn = QPushButton("😊")
        emoji_btn.setFixedSize(40, 40)
        emoji_btn.setCursor(Qt.PointingHandCursor)
        emoji_btn.setStyleSheet("""
            QPushButton {
                background: #1F2937;
                border: none;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #2d3748;
            }
        """)
        input_layout.addWidget(emoji_btn)
        
        # 输入框
        self.chat_input = ChatInput()
        self.chat_input.send_message.connect(self._on_send)
        input_layout.addWidget(self.chat_input, 1)
        
        # 发送按钮
        send_btn = QPushButton("发送")
        send_btn.setFixedSize(60, 40)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #00D4FF;
                color: #0A0E17;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5CE1FF;
            }
        """)
        send_btn.clicked.connect(lambda: self._on_send(self.chat_input.text()))
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
    
    def set_local_user(self, user_id: str):
        """设置本地用户 ID"""
        self.local_user_id = user_id
    
    def _switch_channel(self, channel: str):
        """切换频道"""
        self.current_channel = channel
        
        # 更新按钮状态
        for cid, btn in self.channel_btns.items():
            btn.setChecked(cid == channel)
        
        # 清空消息（实际应用中应该从缓存加载对应频道的消息）
        self._clear_messages()
    
    def _clear_messages(self):
        """清空消息"""
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_message(self, msg_data: Dict[str, Any]):
        """添加消息"""
        is_self = msg_data.get('sender_id') == self.local_user_id
        
        # 移除末尾的 stretch
        if self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(self.messages_layout.count() - 1)
        
        bubble = MessageBubble(msg_data, is_self)
        self.messages_layout.addWidget(bubble)
        self.messages_layout.addStretch()
        
        # 滚动到底部
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_send(self, text: str):
        """发送消息"""
        text = text.strip()
        if not text:
            return
        
        self.chat_input.clear()
        self.message_sent.emit(self.current_channel, text)
        
        # 本地显示消息（实际应用中应该等服务器确认）
        self.add_message({
            'sender_id': self.local_user_id,
            'sender_name': '我',
            'content': text,
            'time': datetime.now().strftime('%H:%M')
        })


class SystemMessage(QWidget):
    """系统消息"""
    
    def __init__(self, text: str, msg_type: str = "info", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        colors = {
            'info': '#64748B',
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444'
        }
        color = colors.get(msg_type, '#64748B')
        
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            font-size: 11px;
            color: {color};
            background: transparent;
            padding: 4px 12px;
        """)
        
        layout.addWidget(label)

