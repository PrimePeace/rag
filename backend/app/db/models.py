from enum import Enum

class DocumentStatus(str, Enum):
    """
    文档类型枚举，生命周期状态

    uploading: 上传的文档,已写入 COS,入库前状态
    parsing: 正在解析的文档,入库前状态,Docling 工具解析中
    indexing: 正在索引的文档,切分+ 向量化+ 写 chunks 中
    ready: 已完成索引的文档，可被检索
    failed: 索引失败的文档，任意阶段失败
    """

    UPLOADING = "uploading"  # 上传的文档
    PARSING = "parsing"  # 正在解析的文档
    INDEXING = "indexing"  # 正在索引的文档
    READY = "ready"  # 已完成索引的文档
    FAILED = "failed"  # 索引失败的文档



# Document 模型
"""
file_hash 字段用文件内容的 sha256,并且加 unique=True 索引。之后的 service层只要查一下这个
字段就能做幂等,同一份文件上传N次只入库一次
storage_provider="cos” 留出未来扩展其他对象存储服务的空间
relationship 的 cascade="all, delete-orphan" + passive_deletes=True A键的 ON DE
LETECASCADE,删文档时自动连带删掉所有chunk,不用业务代码手动清理
"""

from datetime import datetime
from uuid import uuid4,UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from sqlalchemy.dialects.postgresql import JSONB,UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    # sha256 十六进制串长度 64，唯一约束保证文件级幂等
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True,index=True)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    storage_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="cos")
    cos_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    cos_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    cos_region: Mapped[str] = mapped_column(String(64),nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        String(32), nullable=False, default=DocumentStatus.UPLOADING
        )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),nullable=False
        )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
        )
    
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", 
        cascade="all, delete-orphan", 
        passive_deletes=True
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 维度由 settings.embedding_dim 控制，迁移时同步固化
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim), nullable=False)

    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # md5(content), 第 12 章增量索引依据
    chunk_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[Document] = relationship(back_populates="chunks")
