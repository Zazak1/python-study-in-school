"""
日志系统 - 结构化日志
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Dict
from logging.handlers import RotatingFileHandler


class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        
        # 时间
        time_str = datetime.now().strftime('%H:%M:%S')
        
        # 格式化
        msg = f"{color}[{time_str}] [{record.levelname:^8}]{self.RESET} {record.getMessage()}"
        
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


class AppLogger(logging.Logger):
    """应用日志器"""
    
    def __init__(self, name: str, level: int = logging.DEBUG):
        super().__init__(name, level)
    
    def with_context(self, **kwargs) -> logging.LoggerAdapter:
        """添加上下文信息"""
        return logging.LoggerAdapter(self, {'extra_data': kwargs})
    
    def event(self, event_type: str, **data):
        """记录事件"""
        self.info(f"[EVENT:{event_type}]", extra={'extra_data': {'event': event_type, **data}})
    
    def metric(self, name: str, value: float, **tags):
        """记录指标"""
        self.debug(f"[METRIC:{name}={value}]", extra={'extra_data': {'metric': name, 'value': value, **tags}})


# 日志实例缓存
_loggers: Dict[str, AppLogger] = {}


def setup_logger(
    log_dir: Optional[Path] = None,
    level: int = logging.DEBUG,
    console: bool = True,
    file: bool = True
):
    """设置日志系统"""
    
    # 根日志器
    root = logging.getLogger()
    root.setLevel(level)
    
    # 清除现有处理器
    root.handlers.clear()
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        root.addHandler(console_handler)
    
    # 文件处理器
    if file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 常规日志
        file_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        root.addHandler(file_handler)
        
        # 错误日志
        error_handler = RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root.addHandler(error_handler)


def get_logger(name: str) -> AppLogger:
    """获取日志器"""
    if name not in _loggers:
        logger = AppLogger(name)
        _loggers[name] = logger
    return _loggers[name]

