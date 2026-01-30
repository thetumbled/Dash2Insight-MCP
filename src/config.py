"""配置加载模块"""
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    file: Optional[str] = "dash2insight-mcp.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class PrometheusConfig(BaseModel):
    """Prometheus 配置"""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30


class DashboardConfig(BaseModel):
    """Dashboard 配置"""
    name: str
    path: str


class Config(BaseModel):
    """全局配置"""
    prometheus: PrometheusConfig
    dashboards: List[DashboardConfig] = Field(default_factory=list)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: str = "config.yaml") -> Config:
    """加载配置文件"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    return Config(**config_dict)
