"""
Qt 样式表 (QSS) - 2.0 设计升级
"""
from .theme import Theme, CURRENT_THEME


def get_stylesheet(theme: Theme = CURRENT_THEME) -> str:
    """生成 QSS"""
    t = theme.to_dict()
    
    return f"""
    /* ========== 全局重置 ========== */
    QWidget {{
        background-color: {t['bg_base']};
        color: {t['text_body']};
        font-family: {t['font_family']};
        font-size: 14px;
        outline: none;
    }}
    
    QMainWindow {{
        background-color: {t['bg_base']};
    }}
    
    /* ========== 卡片系统 ========== */
    QFrame[class="card"], #card, #loginCard, #gameCard {{
        background-color: {t['bg_card']};
        border: 1px solid {t['border_light']};
        border-radius: 20px;
    }}
    
    /* ========== 字体排版 ========== */
    QLabel {{
        background: transparent;
        color: {t['text_body']};
    }}
    
    QLabel[class="display"] {{
        font-size: 36px;
        font-weight: 800;
        color: {t['text_display']};
    }}
    
    QLabel[class="h1"] {{
        font-size: 24px;
        font-weight: 700;
        color: {t['text_display']};
    }}
    
    QLabel[class="h2"] {{
        font-size: 18px;
        font-weight: 600;
        color: {t['text_display']};
    }}
    
    QLabel[class="body"] {{
        font-size: 14px;
        color: {t['text_body']};
    }}
    
    QLabel[class="caption"] {{
        font-size: 12px;
        color: {t['text_caption']};
    }}
    
    /* ========== 按钮 ========== */
    QPushButton {{
        background-color: {t['bg_card']};
        color: {t['text_body']};
        border: 1px solid {t['border_normal']};
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {t['bg_hover']};
        border-color: {t['border_active']};
        color: {t['primary']};
    }}
    
    QPushButton:pressed {{
        background-color: {t['bg_active']};
    }}
    
    /* Primary Button */
    QPushButton[class="primary"] {{
        background-color: {t['primary']};
        color: {t['text_white']};
        border: 1px solid {t['primary']};
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {t['primary_hover']};
        border-color: {t['primary_hover']};
    }}
    
    QPushButton[class="primary"]:pressed {{
        background-color: {t['primary_pressed']};
    }}
    
    /* Ghost Button */
    QPushButton[class="ghost"] {{
        background-color: transparent;
        border: none;
        color: {t['text_caption']};
        font-weight: 500;
    }}
    
    QPushButton[class="ghost"]:hover {{
        background-color: {t['bg_hover']};
        color: {t['primary']};
    }}
    
    /* Icon Button */
    QPushButton[class="icon-btn"] {{
        background-color: transparent;
        border: none;
        border-radius: 18px;
        padding: 0;
    }}
    
    QPushButton[class="icon-btn"]:hover {{
        background-color: {t['bg_hover']};
    }}
    
    /* ========== 输入框 ========== */
    QLineEdit {{
        background-color: {t['bg_card']};
        color: {t['text_display']};
        border: 1px solid {t['border_normal']};
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        selection-background-color: {t['primary_bg']};
        selection-color: {t['primary']};
    }}
    
    QLineEdit:hover {{
        border-color: {t['text_placeholder']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {t['primary']};
        padding: 11px 15px;
        background-color: #FFFFFF;
    }}
    
    QLineEdit::placeholder {{
        color: {t['text_placeholder']};
    }}
    
    /* ========== 滚动条 ========== */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 4px;
    }}
    
    QScrollBar::handle:vertical {{
        background: #CBD5E1;
        border-radius: 3px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: #94A3B8;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
        height: 0;
    }}
    
    /* ========== 标签页 ========== */
    QTabWidget::pane {{ border: none; }}
    
    QTabBar::tab {{
        background: transparent;
        color: {t['text_caption']};
        font-weight: 600;
        padding: 8px 16px;
        border-bottom: 2px solid transparent;
        margin-right: 12px;
    }}
    
    QTabBar::tab:selected {{
        color: {t['primary']};
        border-bottom-color: {t['primary']};
    }}
    
    QTabBar::tab:hover:!selected {{
        color: {t['text_body']};
        background: {t['bg_hover']};
        border-radius: 6px;
    }}
    
    /* ========== 分割线 ========== */
    QFrame[class="divider"] {{
        background-color: {t['border_normal']};
        max-height: 1px;
        border: none;
    }}
    
    /* ========== 工具提示 ========== */
    QToolTip {{
        background-color: {t['text_display']};
        color: {t['text_white']};
        border: none;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    """
