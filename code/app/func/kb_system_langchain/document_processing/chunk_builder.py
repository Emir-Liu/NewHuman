"""ChunkSegment → ChunkInfo 构建"""

import uuid
from datetime import datetime
from typing import List, Optional

from func.kb_system_langchain.models import ChunkInfo
from func.kb_system_langchain.document_processing.types import ChunkSegment


def build_chunk_infos(
    segments: List[ChunkSegment],
    *,
    doc_id: str,
    file_name: str,
    title: str,
    effective_time: Optional[str] = None,
    expiration_time: Optional[str] = None,
    now: Optional[str] = None,
) -> List[ChunkInfo]:
    now = now or datetime.now().isoformat()
    chunk_infos: List[ChunkInfo] = []
    for seg in segments:
        chunk_infos.append(ChunkInfo(
            id=str(uuid.uuid4()),
            doc_id=doc_id,
            content=seg.content,
            name=file_name,
            title=title,
            index=seg.index,
            create_time=now,
            effective_time=effective_time,
            expiration_time=expiration_time,
            bool_delete=0,
            bool_enable=1,
            page=0,
            token=len(seg.content),
            chunk_mode=seg.chunk_mode,
            answer=seg.answer,
        ))
    return chunk_infos
