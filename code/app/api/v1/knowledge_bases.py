"""
知识库 API 接口
参考 Dify API: https://docs.dify.ai/api-reference/knowledge-bases/
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Form

from schema.knowledge_base_model import (
    BaseResponse,
    CreateKnowledgeBaseRequest,
    UpdateKnowledgeBaseRequest,
    UpdateDocumentRequest,
    CreateChunksRequest,
    UpdateChunkRequest,
    RetrieveRequest,
    KnowledgeBaseItem,
    KnowledgeBaseListContext,
    DocumentItem,
    DocumentListContext,
    ChunkItem,
    ChunkListContext,
    RetrieveContext,
    RetrieveRecord,
)
from service.knowledge_base_service import knowledge_base_service

router = APIRouter(prefix="/datasets", tags=["知识库"])

# ==================== 知识库管理 ====================


@router.post("", response_model=BaseResponse)
async def create_knowledge_base(request: CreateKnowledgeBaseRequest):
    """
    创建知识库

    **请求体**:
    ```json
    {
        "name": "我的知识库",
        "description": "知识库描述",
        "label": "inquiry",
        "bool_activate": 1
    }
    ```
    """
    try:
        result = knowledge_base_service.create_knowledge_base(
            name=request.name,
            description=request.description,
            label=request.label,
            bool_activate=request.bool_activate,
        )
        return BaseResponse(success=True, stateCode=200, stateMsg="", context=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识库失败: {str(e)}")


@router.get("", response_model=BaseResponse)
async def list_knowledge_bases(
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
    label: Optional[str] = Query(default=None, description="标签筛选"),
):
    """
    知识库列表查询

    **查询参数**:
    - page: 页码，从1开始
    - limit: 每页数量，最大100
    - label: 按标签筛选 (inquiry/business_des/business_data)
    """
    try:
        result = knowledge_base_service.list_knowledge_bases(
            page=page,
            limit=limit,
            label=label,
        )
        return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset_id}", response_model=BaseResponse)
async def get_knowledge_base(dataset_id: str):
    """
    获取知识库详情
    """
    kb_info = knowledge_base_service.get_knowledge_base(dataset_id)
    if kb_info is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="", context=kb_info)


@router.patch("/{dataset_id}", response_model=BaseResponse)
async def update_knowledge_base(dataset_id: str, request: UpdateKnowledgeBaseRequest):
    """
    更新知识库信息

    **请求体**:
    ```json
    {
        "name": "新名称",
        "description": "新描述"
    }
    ```
    """
    try:
        result = knowledge_base_service.update_knowledge_base(
            kb_id=dataset_id,
            name=request.name,
            description=request.description,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Dataset not found.")
        return BaseResponse(success=True, stateCode=200, stateMsg="", context=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dataset_id}", response_model=BaseResponse)
async def delete_knowledge_base(dataset_id: str):
    """
    删除知识库（软删除）
    """
    success = knowledge_base_service.delete_knowledge_base(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context={})


# ==================== 文档管理 ====================


@router.post("/{dataset_id}/document/create-by-file", response_model=BaseResponse)
async def upload_document(
    dataset_id: str,
    file: UploadFile = File(..., description="上传的文件"),
    effective_time: str = Form(default="", description="生效时间"),
    expiration_time: str = Form(default="", description="失效时间"),
    parse_mode: str = Form(
        default="",
        description="解析方式：留空=auto按后缀默认；table=Excel解析为行字典列表",
    ),
    chunk_mode: str = Form(
        default="",
        description="切片方式：留空=auto默认切分；row=表格一行一切片；qa=Q向量化A入metadata",
    ),
    q_column: str = Form(default="", description="QA模式 Q 列名（可选）"),
    a_column: str = Form(default="", description="QA模式 A 列名（可选）"),
):
    """
    上传文档到知识库（统一入口）

    **支持格式**: .txt, .md, .pdf, .docx, .xlsx, .xls

    **parse_mode（解析方式）**:
    - 留空 / auto：按后缀默认（Excel→行字典列表，其余→纯文本）
    - table：Excel 解析为行字典列表

    **chunk_mode（切片方式）**:
    - 留空 / auto：文本→智能切分；表格→一行一切片
    - row：表格一行一切片（JSON 序列化每行）
    - qa：Q 列向量化，A 列写入 metadata（需 Excel 且含 Q/A 列）

    **示例**:
    - 普通 PDF：不传 parse_mode / chunk_mode
    - QA Excel：`chunk_mode=qa`
    - 业务 Excel 按行：`parse_mode=table&chunk_mode=row`
    """
    kb_info = knowledge_base_service.get_knowledge_base(dataset_id)
    if kb_info is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    from func.kb_system_langchain.document_loader import DocumentLoader

    file_name = file.filename or "unknown"
    chunk_mode_norm = (chunk_mode or "").strip().lower()

    if chunk_mode_norm == DocumentLoader.CHUNK_MODE_QA:
        if not DocumentLoader.is_qa_excel_supported(file_name):
            raise HTTPException(
                status_code=400,
                detail=f"qa 切片方式仅支持 Excel: {', '.join(DocumentLoader.QA_EXCEL_EXTENSIONS)}",
            )
    elif not DocumentLoader.is_supported(file_name):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，支持: {', '.join(DocumentLoader.SUPPORTED_EXTENSIONS)}",
        )

    try:
        if parse_mode:
            DocumentLoader.normalize_parse_mode(parse_mode)
        if chunk_mode:
            DocumentLoader.normalize_chunk_mode(chunk_mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        content = await file.read()
        result = knowledge_base_service.upload_document(
            kb_id=dataset_id,
            file_content=content,
            file_name=file_name,
            effective_time=effective_time,
            expiration_time=expiration_time,
            parse_mode=parse_mode,
            chunk_mode=chunk_mode,
            q_column=q_column,
            a_column=a_column,
        )
        return BaseResponse(
            success=True,
            stateCode=200,
            stateMsg="success",
            context={"document": result},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/{dataset_id}/documents", response_model=BaseResponse)
async def list_documents(
    dataset_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
):
    """
    文档列表查询
    """
    kb_info = knowledge_base_service.get_knowledge_base(dataset_id)
    if kb_info is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    result = knowledge_base_service.list_documents(
        kb_id=dataset_id,
        page=page,
        limit=limit,
    )
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)


@router.get("/{dataset_id}/documents/{document_id}", response_model=BaseResponse)
async def get_document(dataset_id: str, document_id: str):
    """获取文档详情"""
    doc_info = knowledge_base_service.get_document(document_id)
    if doc_info is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="", context={"document": doc_info})


@router.post("/{dataset_id}/documents/{document_id}/update-by-text", response_model=BaseResponse)
async def update_document(
    dataset_id: str,
    document_id: str,
    request: UpdateDocumentRequest,
):
    """
    更新文档信息
    """
    doc_info = knowledge_base_service.get_document(document_id)
    if doc_info is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    effective_time = None
    expiration_time = None
    if request.doc_metadata:
        for meta in request.doc_metadata:
            if meta.name == "effective_time":
                effective_time = meta.value
            elif meta.name == "expiration_time":
                expiration_time = meta.value

    result = knowledge_base_service.update_document(
        doc_id=document_id,
        name=request.name,
        effective_time=effective_time,
        expiration_time=expiration_time,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return BaseResponse(
        success=True,
        stateCode=200,
        stateMsg="success",
        context={"document": result},
    )


@router.delete("/{dataset_id}/documents/{document_id}", response_model=BaseResponse)
async def delete_document(dataset_id: str, document_id: str):
    """
    删除文档（软删除）
    """
    success = knowledge_base_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document Not Exists.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context={})


@router.post("/{dataset_id}/documents/{document_id}/update-vector", response_model=BaseResponse)
async def re_vectorize_document(dataset_id: str, document_id: str):
    """
    重新向量化文档
    """
    success = knowledge_base_service.re_vectorize_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context={})


# ==================== 切片管理 ====================


@router.post("/{dataset_id}/documents/{document_id}/segments", response_model=BaseResponse)
async def create_chunks(
    dataset_id: str,
    document_id: str,
    request: CreateChunksRequest,
):
    """
    创建切片

    **请求体**:
    ```json
    {
        "segments": [
            {
                "content": "切片内容",
                "chunk_metadata": [
                    {"name": "effective_time", "cn_name": "生效时间", "value": "2026-01-01", "type": "str"}
                ]
            }
        ]
    }
    ```
    """
    doc_info = knowledge_base_service.get_document(document_id)
    if doc_info is None:
        raise HTTPException(status_code=405, detail="Document not found.")

    try:
        result = knowledge_base_service.create_chunks(
            doc_id=document_id,
            segments=[seg.model_dump() for seg in request.segments],
        )
        return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建切片失败: {str(e)}")


@router.get(
    "/{dataset_id}/documents/{document_id}/segments",
    response_model=BaseResponse,
)
async def list_chunks(
    dataset_id: str,
    document_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
):
    """
    切片列表查询
    """
    result = knowledge_base_service.list_chunks(
        doc_id=document_id,
        page=page,
        limit=limit,
    )
    if result.get("total", 0) == 0:
        # 检查文档是否存在
        doc_info = knowledge_base_service.get_document(document_id)
        if doc_info is None:
            raise HTTPException(status_code=405, detail="Document not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)


@router.get(
    "/{dataset_id}/documents/{document_id}/segments/{segment_id}",
    response_model=BaseResponse,
)
async def get_chunk(dataset_id: str, document_id: str, segment_id: str):
    """获取切片详情"""
    chunk = knowledge_base_service.get_chunk(segment_id, document_id)
    if chunk is None:
        raise HTTPException(status_code=407, detail="Chunk not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="", context={"data": [chunk]})


@router.post(
    "/{dataset_id}/documents/{document_id}/segments/{segment_id}",
    response_model=BaseResponse,
)
async def update_chunk(
    dataset_id: str,
    document_id: str,
    segment_id: str,
    request: UpdateChunkRequest,
):
    """
    更新切片

    **请求体**:
    ```json
    {
        "segment": {
            "content": "新内容",
            "metadata": [],
            "enabled": true
        }
    }
    ```
    """
    content = None
    enabled = None
    chunk_metadata = None
    if request.segment:
        content = request.segment.get("content")
        enabled = request.segment.get("enabled")
        chunk_metadata = request.segment.get("metadata") or request.segment.get("chunk_metadata")

    result = knowledge_base_service.update_chunk(
        chunk_id=segment_id,
        doc_id=document_id,
        content=content,
        enabled=enabled,
        chunk_metadata=chunk_metadata,
    )
    if result is None:
        raise HTTPException(status_code=407, detail="Chunk not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context={"data": [result]})


@router.delete(
    "/{dataset_id}/documents/{document_id}/segments/{segment_id}",
    response_model=BaseResponse,
)
async def delete_chunk(dataset_id: str, document_id: str, segment_id: str):
    """
    删除切片
    """
    success = knowledge_base_service.delete_chunk(segment_id, document_id)
    if not success:
        raise HTTPException(status_code=407, detail="Chunk not found.")
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context={})


# ==================== 检索 ====================


@router.post("/{dataset_id}/retrieve", response_model=BaseResponse)
async def retrieve_knowledge_base(dataset_id: str, request: RetrieveRequest):
    """
    知识库检索

    **请求体**:
    ```json
    {
        "query": "查询文本",
        "external_retrieval_model": {
            "top_k": 5,
            "score_threshold": 1.0,
            "score_threshold_enabled": false
        }
    }
    ```
    """
    kb_info = knowledge_base_service.get_knowledge_base(dataset_id)
    if kb_info is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    model = request.external_retrieval_model or RetrieveRequest.model_fields[
        "external_retrieval_model"
    ].default

    result = knowledge_base_service.search(
        kb_id=dataset_id,
        query=request.query,
        top_k=model.top_k if hasattr(model, 'top_k') else 5,
        score_threshold=model.score_threshold if hasattr(model, 'score_threshold') else None,
        score_threshold_enabled=model.score_threshold_enabled if hasattr(model, 'score_threshold_enabled') else False,
    )
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)


@router.post("/retrieve-by-label", response_model=BaseResponse)
async def retrieve_by_label(request: RetrieveRequest, label: str = Query(default="inquiry")):
    """
    按标签联合检索（跨多个知识库）
    """
    model = request.external_retrieval_model or RetrieveRequest.model_fields[
        "external_retrieval_model"
    ].default

    result = knowledge_base_service.search_by_label(
        query=request.query,
        label=label,
        top_k=model.top_k if hasattr(model, 'top_k') else 5,
        score_threshold=model.score_threshold if hasattr(model, 'score_threshold') else None,
        score_threshold_enabled=model.score_threshold_enabled if hasattr(model, 'score_threshold_enabled') else False,
    )
    return BaseResponse(success=True, stateCode=200, stateMsg="success", context=result)
