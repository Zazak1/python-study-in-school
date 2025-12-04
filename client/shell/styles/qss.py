"""
Qt 样式表 (QSS) - 现代化浅色风格
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
        background-color: {t['bg_base']};
        color: {t['text_primary']};
        font-family: {t['font_family']};
        font-size: 14px;
    }}
    
    QMainWindow {{
        background-color: {t['bg_base']};
    }}
    
    /* 卡片容器基础样式 (需在代码中配合 setObjectName 使用) */
    #card, #loginCard, #gameCard, QFrame[class="card"] {{
        background-color: {t['bg_surface']};
        border: 1px solid {t['border']};
        border-radius: 16px;
    }}

    /* ========== 按钮样式 ========== */
    QPushButton {{
        background-color: {t['bg_surface']};
        color: {t['text_primary']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 14px;
    }}
    
    QPushButton:hover {{
        background-color: {t['bg_surface_variant']};
        border-color: {t['primary_light']};
        color: {t['primary']};
    }}
    
    QPushButton:pressed {{
        background-color: {t['bg_base']};
        color: {t['primary_dark']};
    }}
    
    QPushButton:disabled {{
        background-color: {t['bg_base']};
        color: {t['text_tertiary']};
        border-color: {t['border']};
    }}
    
    /* 主要按钮 (填充色) */
    QPushButton[class="primary"] {{
        background-color: {t['primary']};
        color: {t['text_inverse']};
        border: none;
        font-weight: 600;
    }}
    
    QPushButton[class="primary"]:hover {{
        background-color: {t['primary_light']};
    }}
    
    QPushButton[class="primary"]:pressed {{
        background-color: {t['primary_dark']};
    }}
    
    /* 次要按钮 (无边框/幽灵按钮) */
    QPushButton[class="ghost"] {{
        background-color: transparent;
        border: none;
        color: {t['text_secondary']};
    }}
    
    QPushButton[class="ghost"]:hover {{
        background-color: rgba(0, 0, 0, 0.05);
        color: {t['text_primary']};
    }}
    
    /* 危险按钮 */
    QPushButton[class="danger"] {{
        color: {t['error']};
        border-color: {t['error']};
        background-color: {t['bg_surface']};
    }}
    
    QPushButton[class="danger"]:hover {{
        background-color: #FEF2F2; /* 浅红背景 */
    }}
    
    /* ========== 输入框样式 ========== */
    QLineEdit {{
        background-color: {t['bg_surface']};
        color: {t['text_primary']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        selection-background-color: {t['primary_light']};
        selection-color: {t['text_inverse']};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {t['primary']};
        padding: 9px 11px; /* 调整 padding 保持大小一致 */
    }}
    
    QLineEdit:disabled {{
        background-color: {t['bg_base']};
        color: {t['text_tertiary']};
    }}
    
    QLineEdit[echoMode="2"] {{
        lineedit-password-character: 9679;
    }}
    
    /* ========== 文本区域 ========== */
    QTextEdit, QPlainTextEdit {{
        background-color: {t['bg_surface']};
        color: {t['text_primary']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px;
        font-family: {t['font_family']};
    }}
    
    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {t['primary']};
    }}
    
    /* ========== 列表样式 ========== */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}
    
    QListWidget::item {{
        background-color: transparent;
        color: {t['text_primary']};
        border-radius: 8px;
        padding: 8px;
        margin: 2px 4px;
    }}
    
    QListWidget::item:hover {{
        background-color: {t['bg_surface_variant']};
    }}
    
    QListWidget::item:selected {{
        background-color: #EFF6FF; /* 极浅蓝 */
        color: {t['primary']};
    }}
    
    /* ========== 滚动条 (现代化纤细风格) ========== */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: #D1D5DB; /* 浅灰条 */
        border-radius: 4px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #9CA3AF; /* 深一点的灰 */
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 0;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: #D1D5DB;
        border-radius: 4px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: #9CA3AF;
    }}
    
    /* ========== 标签页 ========== */
    QTabWidget::pane {{
        border: none;
        background-color: {t['bg_surface']};
    }}
    
    QTabBar::tab {{
        background-color: transparent;
        color: {t['text_secondary']};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 20px;
        font-weight: 500;
        margin-right: 4px;
    }}
    
    QTabBar::tab:selected {{
        color: {t['primary']};
        border-bottom: 2px solid {t['primary']};
    }}
    
    QTabBar::tab:hover:!selected {{
        color: {t['text_primary']};
        background-color: {t['bg_surface_variant']};
        border-radius: 4px 4px 0 0;
    }}
    
    /* ========== 标签 ========== */
    QLabel {{
        color: {t['text_primary']};
        background: transparent;
    }}
    
    QLabel[class="title"] {{
        font-size: 24px;
        font-weight: 700;
        color: {t['text_primary']};
    }}
    
    QLabel[class="subtitle"] {{
        font-size: 14px;
        color: {t['text_secondary']};
    }}
    
    QLabel[class="heading"] {{
        font-size: 16px;
        font-weight: 600;
        color: {t['text_primary']};
    }}
    
    /* 状态标签 */
    QLabel[class="status-online"] {{ color: {t['success']}; font-weight: 600; }}
    QLabel[class="status-offline"] {{ color: {t['text_tertiary']}; }}
    QLabel[class="status-busy"] {{ color: {t['error']}; }}
    
    /* ========== 分组框 ========== */
    QGroupBox {{
        background-color: {t['bg_surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
        margin-top: 24px;
        padding: 20px;
        font-weight: 600;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        color: {t['text_primary']};
        background-color: {t['bg_surface']}; 
    }}
    
    /* ========== 分割线 ========== */
    QFrame[frameShape="4"] {{ /* HLine */
        background-color: {t['divider']};
        max-height: 1px;
        border: none;
    }}
    
    /* ========== 工具提示 ========== */
    QToolTip {{
        background-color: {t['text_primary']}; /* 深色背景 */
        color: {t['text_inverse']};
        border: none;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
        opacity: 230;
    }}
    
    /* ========== 菜单 ========== */
    QMenu {{
        background-color: {t['bg_surface']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
        color: {t['text_primary']};
    }}
    
    QMenu::item:selected {{
        background-color: {t['bg_surface_variant']};
    }}
    
    /* ========== 进度条 ========== */
    QProgressBar {{
        background-color: {t['bg_base']};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {t['primary']};
        border-radius: 4px;
    }}
    
    /* ========== 复选框 ========== */
    QCheckBox {{
        color: {t['text_primary']};
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {t['border']};
        border-radius: 4px;
        background-color: {t['bg_surface']};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {t['primary']};
        border-color: {t['primary']};
        image: url(client/assets/check.svg); /* 需准备图标，暂留空 */
    }}
    
    QCheckBox::indicator:hover {{
        border-color: {t['primary']};
    }}
    """
