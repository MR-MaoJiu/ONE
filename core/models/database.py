"""
数据库模型
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import os

# 创建数据库目录
os.makedirs('data', exist_ok=True)

# 创建数据库引擎
engine = create_engine('sqlite:///data/memory.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Memory(Base):
    """记忆表"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    meta_info = Column(JSON)
    
    snapshots = relationship("Snapshot", secondary="memory_snapshots")
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.meta_info
        }

class Snapshot(Base):
    """快照表"""
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    meta_info = Column(JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.meta_info
        }

class MemorySnapshot(Base):
    """记忆快照关联表"""
    __tablename__ = 'memory_snapshots'
    
    memory_id = Column(Integer, ForeignKey('memories.id'), primary_key=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'), primary_key=True)
    relevance_score = Column(Float, default=0.0)

# 创建数据库表
Base.metadata.create_all(engine)

def get_session():
    """获取数据库会话"""
    return Session() 