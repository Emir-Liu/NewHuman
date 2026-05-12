"""
多知识库管理器
支持知识库的创建、切换、删除和元数据管理
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from config.vectordb_config import VectorDBConfig
from config.emb_config import EmbeddingConfig
from vectorstore.base import KnowledgeBaseInfo
from vectorstore.knowledge_base import KnowledgeBase


class KnowledgeBaseManager:
    """
    多知识库管理器
    
    管理多个知识库的创建、切换和元数据
    每个知识库独立存储在子目录中
    """
    
    # 元数据文件名称
    META_FILE = "kb_meta.json"
    
    def __init__(
        self,
        vectordb_config: Optional[VectorDBConfig] = None,
        embedding_config: Optional[EmbeddingConfig] = None,
    ):
        self.vectordb_config = vectordb_config or VectorDBConfig()
        self.embedding_config = embedding_config or EmbeddingConfig()
        
        # 基础存储目录
        self.base_path = Path(self.vectordb_config.persist_directory)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 加载元数据
        self._meta_data: Dict[str, KnowledgeBaseInfo] = {}
        self._knowledge_bases: Dict[str, KnowledgeBase] = {}
        self._current_kb_id: Optional[str] = None
        
        self._load_meta()
    
    def _get_meta_path(self) -> Path:
        """获取元数据文件路径"""
        return self.base_path / self.META_FILE
    
    def _load_meta(self):
        """从文件加载知识库元数据"""
        meta_path = self._get_meta_path()
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for kb_id, info_dict in data.get("knowledge_bases", {}).items():
                        self._meta_data[kb_id] = KnowledgeBaseInfo(**info_dict)
                    self._current_kb_id = data.get("current_kb_id")
            except Exception as e:
                print(f"加载知识库元数据失败: {e}")
                self._meta_data = {}
    
    def _save_meta(self):
        """保存知识库元数据到文件"""
        meta_path = self._get_meta_path()
        try:
            data = {
                "knowledge_bases": {
                    kb_id: {
                        "kb_id": info.kb_id,
                        "name": info.name,
                        "description": info.description,
                        "created_at": info.created_at,
                        "updated_at": info.updated_at,
                        "doc_count": info.doc_count,
                        "status": info.status,
                    }
                    for kb_id, info in self._meta_data.items()
                },
                "current_kb_id": self._current_kb_id,
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库元数据失败: {e}")
    
    def _get_kb_path(self, kb_id: str) -> Path:
        """获取知识库存储路径"""
        return self.base_path / kb_id
    
    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        kb_id: Optional[str] = None,
    ) -> KnowledgeBaseInfo:
        """
        创建新 knowledge_base
        
        Args:
            name: 知识库名称
            description: 知识库描述
            kb_id: 可选，指定知识库ID，默认自动生成
        
        Returns:
            KnowledgeBaseInfo: 新创建的知识库信息
        """
        # 生成唯一ID
        if kb_id is None:
            kb_id = f"kb_{uuid.uuid4().hex[:8]}"
        
        # 检查ID是否已存在
        if kb_id in self._meta_data:
            raise ValueError(f"Knowledge_base ID '{kb_id}' 已存在")
        
        # 创建知识库存储目录
        kb_path = self._get_kb_path(kb_id)
        kb_path.mkdir(parents=True, exist_ok=True)
        
        # 创建元数据
        now = datetime.now().isoformat()
        kb_info = KnowledgeBaseInfo(
            kb_id=kb_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            doc_count=0,
            status="active",
        )
        
        # 保存元数据
        self._meta_data[kb_id] = kb_info
        self._save_meta()
        
        # 创建 KnowledgeBase 实例（延迟初始化，实际使用时才加载）
        print(f"Knowledge_base '{name}' (ID: {kb_id}) 创建成功")
        
        return kb_info
    
    def _init_knowledge_base(self, kb_id: str) -> KnowledgeBase:
        """初始化指定 knowledge_base 的 Chroma 实例"""
        if kb_id not in self._meta_data:
            raise ValueError(f"Knowledge_base ID '{kb_id}' 不存在")
        
        # 如果已加载，直接返回
        if kb_id in self._knowledge_bases:
            return self._knowledge_bases[kb_id]
        
        # 创建新的配置，指定到知识库子目录
        kb_path = self._get_kb_path(kb_id)
        
        # 临时修改配置的路径
        original_config = self.vectordb_config
        kb_config = VectorDBConfig()
        kb_config.persist_directory = str(kb_path)
        
        # 初始化 KnowledgeBase
        kb = KnowledgeBase(
            vectordb_config=kb_config,
            embedding_config=self.embedding_config,
        )
        
        self._knowledge_bases[kb_id] = kb
        return kb
    
    def switch_knowledge_base(self, kb_id: str) -> KnowledgeBase:
        """
        切换到指定 knowledge_base
        
        Args:
            kb_id: 目标 knowledge_base ID
        
        Returns:
            KnowledgeBase: 切换后的 knowledge_base 实例
        """
        if kb_id not in self._meta_data:
            raise ValueError(f"Knowledge_base ID '{kb_id}' 不存在")
        
        # 初始化并设置为当前 knowledge_base
        kb = self._init_knowledge_base(kb_id)
        self._current_kb_id = kb_id
        self._save_meta()
        
        print(f"已切换到 knowledge_base: {self._meta_data[kb_id].name} (ID: {kb_id})")
        return kb
    
    def get_current_kb(self) -> Optional[KnowledgeBase]:
        """获取当前 knowledge_base 实例"""
        if self._current_kb_id is None:
            # 如果没有当前 knowledge_base，尝试使用第一个
            if self._meta_data:
                first_kb_id = list(self._meta_data.keys())[0]
                return self.switch_knowledge_base(first_kb_id)
            return None
        
        return self._init_knowledge_base(self._current_kb_id)
    
    def get_current_kb_info(self) -> Optional[KnowledgeBaseInfo]:
        """获取当前 knowledge_base 信息"""
        if self._current_kb_id is None:
            return None
        return self._meta_data.get(self._current_kb_id)
    
    def list_knowledge_bases(self) -> List[KnowledgeBaseInfo]:
        """列出所有 knowledge_base"""
        return list(self._meta_data.values())
    
    def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        获取指定 knowledge_base 实例（不切换当前）
        
        Args:
            kb_id: knowledge_base ID
        
        Returns:
            KnowledgeBase 实例，不存在则返回 None
        """
        if kb_id not in self._meta_data:
            return None
        return self._init_knowledge_base(kb_id)
    
    def get_knowledge_base_info(self, kb_id: str) -> Optional[KnowledgeBaseInfo]:
        """获取指定 knowledge_base 的元数据信息"""
        return self._meta_data.get(kb_id)
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        删除 knowledge_base
        
        Args:
            kb_id: 要删除的 knowledge_base ID
        
        Returns:
            bool: 是否删除成功
        """
        if kb_id not in self._meta_data:
            print(f"Knowledge_base ID '{kb_id}' 不存在")
            return False
        
        kb_info = self._meta_data[kb_id]
        kb_name = kb_info.name
        
        try:
            # 从内存中移除
            if kb_id in self._knowledge_bases:
                del self._knowledge_bases[kb_id]
            
            # 从元数据中移除
            del self._meta_data[kb_id]
            
            # 如果删除的是当前 knowledge_base，重置当前 knowledge_base
            if self._current_kb_id == kb_id:
                self._current_kb_id = None
                # 自动切换到第一个可用的 knowledge_base
                if self._meta_data:
                    self._current_kb_id = list(self._meta_data.keys())[0]
            
            self._save_meta()
            
            # 删除存储目录
            import shutil
            kb_path = self._get_kb_path(kb_id)
            if kb_path.exists():
                shutil.rmtree(kb_path)
            
            print(f"Knowledge_base '{kb_name}' (ID: {kb_id}) 已删除")
            return True
            
        except Exception as e:
            print(f"删除 knowledge_base 失败: {e}")
            return False
    
    def update_knowledge_base_info(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        更新 knowledge_base 元数据
        
        Args:
            kb_id: knowledge_base ID
            name: 新名称（可选）
            description: 新描述（可选）
        
        Returns:
            bool: 是否更新成功
        """
        if kb_id not in self._meta_data:
            return False
        
        kb_info = self._meta_data[kb_id]
        
        if name is not None:
            kb_info.name = name
        if description is not None:
            kb_info.description = description
        
        kb_info.updated_at = datetime.now().isoformat()
        
        self._save_meta()
        return True
    
    def refresh_doc_count(self, kb_id: str) -> int:
        """
        刷新 knowledge_base 文档数量
        
        Args:
            kb_id: knowledge_base ID
        
        Returns:
            int: 当前文档数量
        """
        if kb_id not in self._meta_data:
            return 0
        
        kb = self._init_knowledge_base(kb_id)
        count = kb.doc_count
        
        self._meta_data[kb_id].doc_count = count
        self._save_meta()
        
        return count


# ==================== 便捷使用方式 ====================

# 全局管理器实例（单例模式）
_kb_manager: Optional[KnowledgeBaseManager] = None


def get_kb_manager(
    vectordb_config: Optional[VectorDBConfig] = None,
    embedding_config: Optional[EmbeddingConfig] = None,
) -> KnowledgeBaseManager:
    """获取全局 KnowledgeBaseManager 实例"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager(vectordb_config, embedding_config)
    return _kb_manager


def get_current_kb() -> Optional[KnowledgeBase]:
    """便捷函数：获取当前 knowledge_base"""
    return get_kb_manager().get_current_kb()


if __name__ == '__main__':
    # 测试代码
    manager = KnowledgeBaseManager()
    
    # 列出所有 knowledge_base
    print("=== 所有 Knowledge_bases ===")
    for kb in manager.list_knowledge_bases():
        print(f"  - {kb.name} (ID: {kb.kb_id}, 文档数: {kb.doc_count})")
    
    # 创建新 knowledge_base
    print("\n=== 创建新 Knowledge_base ===")
    new_kb = manager.create_knowledge_base(
        name="产品文档库",
        description="存储产品相关文档",
    )
    print(f"创建成功: {new_kb.name} (ID: {new_kb.kb_id})")
    
    # 切换到新 knowledge_base 并添加文档
    print("\n=== 切换到新 Knowledge_base 并添加文档 ===")
    kb = manager.switch_knowledge_base(new_kb.kb_id)
    from vectorstore.base import Document
    kb.add_documents([
        Document(content="产品A使用手册", metadata={"type": "manual"}),
        Document(content="产品B技术规格", metadata={"type": "spec"}),
    ])
    
    # 刷新文档数
    manager.refresh_doc_count(new_kb.kb_id)
    
    # 再次列出
    print("\n=== 更新后的 Knowledge_bases ===")
    for kb_info in manager.list_knowledge_bases():
        current = " <-- 当前" if kb_info.kb_id == manager._current_kb_id else ""
        print(f"  - {kb_info.name} (ID: {kb_info.kb_id}, 文档数: {kb_info.doc_count}){current}")
    
    # 搜索
    print("\n=== 在当前 Knowledge_base 中搜索 ===")
    results = manager.get_current_kb().search("产品")
    for r in results:
        print(f"  - {r}")
