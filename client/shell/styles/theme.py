"""
主题配置 - 游戏大厅风格
采用赛博朋克 + 霓虹风格，深色背景配合亮色点缀
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """主题配置"""
    # 主色调
    primary: str           # 主要强调色
    primary_light: str     # 主色亮版
    primary_dark: str      # 主色暗版
    
    # 次要色
    secondary: str         # 次要强调色
    accent: str            # 点缀色
    
    # 背景色
    bg_dark: str           # 最深背景
    bg_medium: str         # 中等背景
    bg_light: str          # 较亮背景
    bg_card: str           # 卡片背景
    
    # 文字色
    text_primary: str      # 主要文字
    text_secondary: str    # 次要文字
    text_muted: str        # 弱化文字
    text_inverse: str      # 反色文字
    
    # 状态色
    success: str           # 成功/在线
    warning: str           # 警告
    error: str             # 错误/离线
    info: str              # 信息
    
    # 边框
    border: str            # 边框色
    border_light: str      # 亮边框
    
    # 特效
    glow: str              # 发光效果色
    shadow: str            # 阴影色
    
    # 字体
    font_family: str       # 主字体
    font_family_mono: str  # 等宽字体
    
    def to_dict(self) -> Dict[str, str]:
        """转为字典"""
        return {
            'primary': self.primary,
            'primary_light': self.primary_light,
            'primary_dark': self.primary_dark,
            'secondary': self.secondary,
            'accent': self.accent,
            'bg_dark': self.bg_dark,
            'bg_medium': self.bg_medium,
            'bg_light': self.bg_light,
            'bg_card': self.bg_card,
            'text_primary': self.text_primary,
            'text_secondary': self.text_secondary,
            'text_muted': self.text_muted,
            'text_inverse': self.text_inverse,
            'success': self.success,
            'warning': self.warning,
            'error': self.error,
            'info': self.info,
            'border': self.border,
            'border_light': self.border_light,
            'glow': self.glow,
            'shadow': self.shadow,
            'font_family': self.font_family,
            'font_family_mono': self.font_family_mono,
        }


# 深色主题 - 赛博霓虹风格
DARK_THEME = Theme(
    # 主色：电光蓝
    primary='#00D4FF',
    primary_light='#5CE1FF',
    primary_dark='#0099CC',
    
    # 次要色：霓虹粉
    secondary='#FF2E97',
    accent='#FFE600',  # 金黄点缀
    
    # 背景：深邃黑蓝
    bg_dark='#0A0E17',
    bg_medium='#111827',
    bg_light='#1F2937',
    bg_card='#161E2E',
    
    # 文字
    text_primary='#F0F4F8',
    text_secondary='#94A3B8',
    text_muted='#64748B',
    text_inverse='#0A0E17',
    
    # 状态色
    success='#10B981',
    warning='#F59E0B',
    error='#EF4444',
    info='#3B82F6',
    
    # 边框
    border='#2D3748',
    border_light='#4A5568',
    
    # 特效
    glow='rgba(0, 212, 255, 0.4)',
    shadow='rgba(0, 0, 0, 0.5)',
    
    # 字体 - 使用系统自带的现代字体
    font_family='"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif',
    font_family_mono='"SF Mono", "Fira Code", "Monaco", monospace',
)


# 可选：亮色主题
LIGHT_THEME = Theme(
    primary='#0066FF',
    primary_light='#3399FF',
    primary_dark='#0044CC',
    secondary='#FF3366',
    accent='#FFAA00',
    bg_dark='#F8FAFC',
    bg_medium='#F1F5F9',
    bg_light='#E2E8F0',
    bg_card='#FFFFFF',
    text_primary='#1E293B',
    text_secondary='#475569',
    text_muted='#94A3B8',
    text_inverse='#FFFFFF',
    success='#10B981',
    warning='#F59E0B',
    error='#EF4444',
    info='#3B82F6',
    border='#E2E8F0',
    border_light='#CBD5E1',
    glow='rgba(0, 102, 255, 0.3)',
    shadow='rgba(0, 0, 0, 0.1)',
    font_family='"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", sans-serif',
    font_family_mono='"SF Mono", "Fira Code", "Monaco", monospace',
)

