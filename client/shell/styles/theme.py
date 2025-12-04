"""
主题配置 - 现代化浅色风格
采用 Material Design 3 / Apple Design 风格，清爽、明亮、高可读性
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """主题配置"""
    # 主色调
    primary: str           # 品牌主色 (科技蓝)
    primary_light: str     # 主色亮版 (悬停)
    primary_dark: str      # 主色暗版 (按下)
    
    # 次要色
    secondary: str         # 次要色 (活力橙)
    accent: str            # 点缀色 (紫色/粉色)
    
    # 背景色
    bg_base: str           # 基础背景 (应用底色)
    bg_surface: str        # 表面背景 (卡片/面板)
    bg_surface_variant: str # 变体表面 (输入框/列表项)
    
    # 文字色
    text_primary: str      # 主要文字 (深灰/黑)
    text_secondary: str    # 次要文字 (中灰)
    text_tertiary: str     # 辅助文字 (浅灰)
    text_inverse: str      # 反色文字 (白)
    
    # 状态色
    success: str           # 成功/在线
    warning: str           # 警告
    error: str             # 错误/离线
    info: str              # 信息
    
    # 边框与分割线
    border: str            # 常规边框
    border_focus: str      # 焦点边框
    divider: str           # 分割线
    
    # 特效
    shadow_sm: str         # 小阴影
    shadow_md: str         # 中阴影
    shadow_lg: str         # 大阴影
    overlay: str           # 遮罩层
    
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
            'bg_base': self.bg_base,
            'bg_surface': self.bg_surface,
            'bg_surface_variant': self.bg_surface_variant,
            'text_primary': self.text_primary,
            'text_secondary': self.text_secondary,
            'text_tertiary': self.text_tertiary,
            'text_inverse': self.text_inverse,
            'success': self.success,
            'warning': self.warning,
            'error': self.error,
            'info': self.info,
            'border': self.border,
            'border_focus': self.border_focus,
            'divider': self.divider,
            'shadow_sm': self.shadow_sm,
            'shadow_md': self.shadow_md,
            'shadow_lg': self.shadow_lg,
            'overlay': self.overlay,
            'font_family': self.font_family,
            'font_family_mono': self.font_family_mono,
        }


# 现代化浅色主题
LIGHT_MODERN_THEME = Theme(
    # 主色：Inter Blue
    primary='#2563EB',        # 鲜艳的蓝
    primary_light='#3B82F6',  # 亮蓝
    primary_dark='#1D4ED8',   # 深蓝
    
    # 次要色
    secondary='#F59E0B',      # 琥珀色
    accent='#8B5CF6',         # 梦幻紫
    
    # 背景：灰白层次
    bg_base='#F3F4F6',        # 极浅灰底色
    bg_surface='#FFFFFF',     # 纯白卡片
    bg_surface_variant='#F9FAFB', # 浅灰表面
    
    # 文字：高对比度深灰
    text_primary='#111827',   # 近乎黑
    text_secondary='#4B5563', # 深灰
    text_tertiary='#9CA3AF',  # 浅灰
    text_inverse='#FFFFFF',   # 纯白
    
    # 状态色
    success='#10B981',        # 翡翠绿
    warning='#F59E0B',        # 琥珀黄
    error='#EF4444',          # 玫瑰红
    info='#3B82F6',           # 天空蓝
    
    # 边框
    border='#E5E7EB',         # 浅灰边框
    border_focus='#2563EB',   # 聚焦蓝边框
    divider='#F3F4F6',        # 分割线
    
    # 阴影 (CSS 格式 rgba)
    shadow_sm='rgba(0, 0, 0, 0.05)',
    shadow_md='rgba(0, 0, 0, 0.1)',
    shadow_lg='rgba(0, 0, 0, 0.15)',
    overlay='rgba(255, 255, 255, 0.8)',
    
    # 字体 - 优先使用系统字体
    font_family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif',
    font_family_mono='"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
)

# 默认主题指向新主题
DARK_THEME = LIGHT_MODERN_THEME 
