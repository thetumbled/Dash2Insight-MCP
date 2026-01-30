"""日志配置模块"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "dash2insight-mcp",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: logger 名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件备份数
    
    Returns:
        配置好的 logger 对象
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 日志格式（levelname 标明真实级别；若输出被标为 [error] 是因 stderr 流，非 ERROR 级别）
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 handler - 输出到 stderr（重要！不能用 stdout）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 handler（如果指定了日志文件）
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"无法创建日志文件 {log_file}: {e}")
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: logger 名称，默认为 dash2insight-mcp
    
    Returns:
        logger 对象
    """
    if name:
        return logging.getLogger(f"dash2insight-mcp.{name}")
    return logging.getLogger("dash2insight-mcp")
