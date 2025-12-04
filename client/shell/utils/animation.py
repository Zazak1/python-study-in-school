"""
动画工具类 - 封装常用动效
"""
from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QObject, 
    QPoint, QRect, QSize, QParallelAnimationGroup
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

class AnimationUtils:
    """动画工具"""
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300, delay: int = 0):
        """淡入动画"""
        # 检查是否已有 effect
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            
        effect.setOpacity(0)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        
        if delay > 0:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(delay, anim.start)
        else:
            anim.start()
        
        # 保存引用防止被垃圾回收
        widget._fade_anim = anim
        
    @staticmethod
    def slide_in_up(widget: QWidget, duration: int = 400, distance: int = 20):
        """从下方滑入"""
        pos = widget.pos()
        start_pos = QPoint(pos.x(), pos.y() + distance)
        
        # 同时淡入
        AnimationUtils.fade_in(widget, duration)
        
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(pos)
        anim.setEasingCurve(QEasingCurve.OutBack) # 回弹效果
        anim.start()
        
        widget._slide_anim = anim

    @staticmethod
    def hover_scale(widget: QWidget, enter: bool, scale_amt: int = 2):
        """
        悬停轻微缩放/位移 (通过 geometry 模拟，因为 QWidget 没有 scale 属性)
        这里使用简单的位移模拟浮起效果
        """
        current_pos = widget.y()
        target_pos = current_pos - scale_amt if enter else current_pos + scale_amt
        
        # 这里假设原始位置是固定的，简化处理
        # 实际生产中建议使用 QGraphicsView 或 transform，或者只做阴影变化
        pass # 暂时留空，由 GameCard 自行实现更复杂的

