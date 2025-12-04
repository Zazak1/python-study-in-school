"""
Qt 样式表 (QSS) - 游戏大厅风格
"""
from .theme import Theme, DARK_THEME


def get_stylesheet(theme: Theme = DARK_THEME) -> str:
    """
    生成完整的 Qt 样式表
    
    Args:
        theme: 主题配置
        
    Returns:
        QSS 样式字符串
    """
    t = theme.to_dict()
    
    return f"""
    /* ========== 全局样式 ========== */
    QWidget {{
        background-color: {t['bg_dark']};
        color: {t['text_primary']};
        font-family: {t['font_family']};
        font-size: 14px;
    }}
    
    QMainWindow {{
        background-color: {t['bg_dark']};
    }}
    
    /* ========== 按钮样式 ========== */
    QPushButton {{
        background-color: {t['bg_light']};
        color: {t['text_primary']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 14px;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: {t['primary_dark']};
        border-color: {t['primary']};
        color: {t['text_primary']};
    }}
    
    QPushButton:pressed {{
        background-color: {t['primary']};
        color: {t['text_inverse']};
    }}
    
    QPushButton:disabled {{
        background-color: {t['bg_medium']};
        color: {t['text_muted']};
        border-color: {t['border']};
    }}
    
    /* 主要按钮 */
    QPushButton[class="primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t['primary']}, stop:1 {t['primary_dark']});
        color: {t['text_inverse']};
        border: none;
        font-weight: bold;
    }}
    
    QPushButton[class="primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t['primary_light']}, stop:1 {t['primary']});
    }}
    
    /* 次要按钮 */
    QPushButton[class="secondary"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {t['secondary']}, stop:1 #CC2579);
        color: {t['text_primary']};
        border: none;
    }}
    
    /* 游戏按钮 - 大尺寸 */
    QPushButton[class="game-btn"] {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t['bg_card']}, stop:1 {t['bg_dark']});
        border: 2px solid {t['border']};
        border-radius: 12px;
        padding: 20px;
        min-height: 80px;
        font-size: 16px;
    }}
    
    QPushButton[class="game-btn"]:hover {{
        border-color: {t['primary']};
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {t['bg_light']}, stop:1 {t['bg_card']});
    }}
    
    /* ========== 输入框样式 ========== */
    QLineEdit {{
        background-color: {t['bg_medium']};
        color: {t['text_primary']};
        border: 2px solid {t['border']};
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 14px;
        selection-background-color: {t['primary']};
    }}
    
    QLineEdit:focus {{
        border-color: {t['primary']};
        background-color: {t['bg_light']};
    }}
    
    QLineEdit:disabled {{
        background-color: {t['bg_dark']};
        color: {t['text_muted']};
    }}
    
    QLineEdit[echoMode="2"] {{
        lineedit-password-character: 9679;
    }}
    
    /* ========== 文本区域 ========== */
    QTextEdit, QPlainTextEdit {{
        background-color: {t['bg_medium']};
        color: {t['text_primary']};
        border: 2px solid {t['border']};
        border-radius: 8px;
        padding: 12px;
        font-family: {t['font_family']};
    }}
    
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {t['primary']};
    }}
    
    /* ========== 列表样式 ========== */
    QListWidget {{
        background-color: {t['bg_medium']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    
    QListWidget::item {{
        background-color: transparent;
        color: {t['text_primary']};
        border-radius: 6px;
        padding: 12px;
        margin: 2px 4px;
    }}
    
    QListWidget::item:hover {{
        background-color: {t['bg_light']};
    }}
    
    QListWidget::item:selected {{
        background-color: {t['primary_dark']};
        color: {t['text_primary']};
    }}
    
    /* ========== 滚动条 ========== */
    QScrollBar:vertical {{
        background-color: {t['bg_dark']};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {t['border_light']};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {t['primary']};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        background-color: {t['bg_dark']};
        height: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {t['border_light']};
        border-radius: 5px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {t['primary']};
    }}
    
    /* ========== 标签页 ========== */
    QTabWidget::pane {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {t['bg_medium']};
        color: {t['text_secondary']};
        border: none;
        padding: 12px 24px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: bold;
    }}
    
    QTabBar::tab:selected {{
        background-color: {t['bg_card']};
        color: {t['primary']};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {t['bg_light']};
        color: {t['text_primary']};
    }}
    
    /* ========== 标签 ========== */
    QLabel {{
        color: {t['text_primary']};
        background: transparent;
    }}
    
    QLabel[class="title"] {{
        font-size: 28px;
        font-weight: bold;
        color: {t['primary']};
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 16px;
        color: {t['text_secondary']};
    }}
    
    QLabel[class="heading"] {{
        font-size: 18px;
        font-weight: bold;
        color: {t['text_primary']};
    }}
    
    QLabel[class="status-online"] {{
        color: {t['success']};
        font-weight: bold;
    }}
    
    QLabel[class="status-offline"] {{
        color: {t['text_muted']};
    }}
    
    /* ========== 分组框 ========== */
    QGroupBox {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        color: {t['primary']};
    }}
    
    /* ========== 分割线 ========== */
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{
        background-color: {t['border']};
        max-height: 1px;
    }}
    
    /* ========== 工具提示 ========== */
    QToolTip {{
        background-color: {t['bg_card']};
        color: {t['text_primary']};
        border: 1px solid {t['primary']};
        border-radius: 4px;
        padding: 8px;
        font-size: 12px;
    }}
    
    /* ========== 菜单 ========== */
    QMenu {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px;
    }}
    
    QMenu::item {{
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {t['primary_dark']};
    }}
    
    /* ========== 进度条 ========== */
    QProgressBar {{
        background-color: {t['bg_medium']};
        border: none;
        border-radius: 6px;
        height: 12px;
        text-align: center;
        font-size: 10px;
        color: {t['text_primary']};
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t['primary']}, stop:1 {t['secondary']});
        border-radius: 6px;
    }}
    
    /* ========== 复选框 ========== */
    QCheckBox {{
        color: {t['text_primary']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {t['border']};
        border-radius: 4px;
        background-color: {t['bg_medium']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {t['primary']};
        border-color: {t['primary']};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {t['primary']};
    }}
    """

