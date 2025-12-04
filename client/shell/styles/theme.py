"""
主题配置 - 2.0 设计升级
采用 Apple Design / Material 3 融合风格
强调：弥散阴影、微渐变、精细排版、流畅动效
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """主题配置"""
    # 品牌色 (Brand Colors)
    primary: str           # 主色 (Royal Blue)
    primary_hover: str     # 悬停
    primary_pressed: str   # 按下
    primary_bg: str        # 主色背景 (极淡)
    
    # 功能色 (Functional Colors)
    secondary: str         # 次要色 (Coral)
    success: str           # 成功 (Emerald)
    warning: str           # 警告 (Amber)
    error: str             # 错误 (Rose)
    info: str              # 信息 (Sky)
    
    # 背景色 (Backgrounds)
    bg_base: str           # 应用底色 (带微蓝灰)
    bg_card: str           # 卡片背景 (纯白)
    bg_hover: str          # 悬停背景
    bg_active: str         # 激活背景
    bg_overlay: str        # 遮罩层
    
    # 文字色 (Typography)
    text_display: str      # 标题 (几乎纯黑)
    text_body: str         # 正文 (深灰)
    text_caption: str      # 说明 (中灰)
    text_placeholder: str  # 占位符 (浅灰)
    text_white: str        # 反白文字
    
    # 边框 (Borders)
    border_light: str      # 极细边框
    border_normal: str     # 常规边框
    border_active: str     # 激活边框
    
    # 阴影 (Shadows - CSS RGBA)
    shadow_sm: str         # 浮起
    shadow_md: str         # 悬停
    shadow_lg: str         # 模态/弹出
    shadow_colored: str    # 彩色弥散阴影模板
    
    # 字体 (Fonts)
    font_family: str
    
    def to_dict(self) -> Dict[str, str]:
        return self.__dict__


# 2.0 升级版主题
DESIGN_THEME = Theme(
    # 品牌色：更现代的 Royal Blue
    primary='#3B82F6',        # 标准蓝
    primary_hover='#2563EB',  # 加深
    primary_pressed='#1D4ED8',
    primary_bg='#EFF6FF',     # 极淡蓝背景
    
    # 功能色：低饱和度，不刺眼
    secondary='#F97316',      # 活力橙
    success='#10B981',        # 翡翠绿
    warning='#F59E0B',        # 琥珀黄
    error='#EF4444',          # 玫瑰红
    info='#0EA5E9',           # 天空蓝
    
    # 背景：层次感
    bg_base='#F8FAFC',        # 冷灰底色
    bg_card='#FFFFFF',        # 纯白
    bg_hover='#F1F5F9',       # 交互悬停
    bg_active='#E2E8F0',      # 激活/按下
    bg_overlay='rgba(255, 255, 255, 0.85)',
    
    # 文字：Inter 风格
    text_display='#0F172A',   # 标题黑
    text_body='#334155',      # 正文深蓝灰
    text_caption='#64748B',   # 说明灰
    text_placeholder='#94A3B8',
    text_white='#FFFFFF',
    
    # 边框
    border_light='#F1F5F9',
    border_normal='#E2E8F0',
    border_active='#3B82F6',
    
    # 阴影系统
    shadow_sm='rgba(0, 0, 0, 0.04)',
    shadow_md='rgba(0, 0, 0, 0.08)',
    shadow_lg='rgba(0, 0, 0, 0.12)',
    shadow_colored='rgba({r}, {g}, {b}, 0.25)', # 动态替换
    
    # 字体栈
    font_family='-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei UI", "Helvetica Neue", Helvetica, Arial, sans-serif',
)

# 导出供调用
CURRENT_THEME = DESIGN_THEME

# 兼容旧代码 (虽然现在是浅色，但为了兼容引用保留变量名)
DARK_THEME = DESIGN_THEME 
