import logging
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from utils.embeddings import get_embedding
from utils.query_processor import rewrite_query
from utils.hybrid_search import hybrid_search
from utils.reranker import rerank_chunks
from utils.llm import ask_llm

logger = logging.getLogger("chat")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    logger.info(f"Question: '{request.question[:80]}{'...' if len(request.question) > 80 else ''}'")
    logger.info(f"Filter: {request.filename_filter or 'all'} | History turns: {len(request.history or [])}")

    # Step 1: Rewrite query
    try:
        clean_question = rewrite_query(request.question)
        if clean_question != request.question:
            logger.info(f"Query rewritten: '{clean_question}'")
    except Exception as e:
        logger.warning(f"Query rewrite failed, using original: {e}")
        clean_question = request.question

    # Step 2: Embed
    try:
        query_embedding = get_embedding(clean_question)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question. Please try again.")

    # Step 3: Hybrid search
    try:
        raw_chunks = hybrid_search(
            query=clean_question,
            query_embedding=query_embedding,
            top_k=12,
            filename_filter=request.filename_filter
        )
        logger.info(f"Hybrid search returned {len(raw_chunks)} candidates")
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail="Document search failed. Please try again.")

    # Step 4: Rerank
    try:
        reranked = rerank_chunks(question=clean_question, chunks=raw_chunks, top_n=4)
        logger.info(f"Reranked to {len(reranked)} chunks")
    except Exception as e:
        logger.warning(f"Reranking failed, using raw results: {e}")
        reranked = raw_chunks[:request.top_k]

    # Step 5: Threshold filter
    filtered = [c for c in reranked if c["similarity_score"] >= request.similarity_threshold]
    logger.info(f"After threshold ({request.similarity_threshold}): {len(filtered)} chunks passed")

    # Step 6: LLM
    try:
        history = [{"role": m.role, "content": m.content} for m in (request.history or [])]
        result = ask_llm(clean_question, filtered, history=history)
        logger.info(f"Answer generated | had_context={result['had_context']} | model={result['model']}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer. Please try again.")

    return ChatResponse(
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
        had_context=result["had_context"],
        model=result["model"]
    )