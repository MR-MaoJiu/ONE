"""
处理器基础类和接口定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ProcessorConfig:
    """处理器配置基类"""
    pass

@dataclass
class ProcessorResult:
    """处理器结果基类"""
    success: bool
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class Processor(ABC):
    """处理器基类"""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> ProcessorResult:
        """处理输入数据"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        pass

class ProcessorException(Exception):
    """处理器异常基类"""
    pass

class ProcessorConfigException(ProcessorException):
    """配置相关异常"""
    pass

class ProcessorInputException(ProcessorException):
    """输入相关异常"""
    pass

class ProcessorExecutionException(ProcessorException):
    """执行相关异常"""
    pass 