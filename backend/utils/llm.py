import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()
client = OpenAI()


def build_rag_prompt(question: str, chunks: List[Dict]) -> str:
    if not chunks:
        return question

    context_parts = []
    for i, chunk in enumerate(chunks):
        filename = chunk["metadata"]["filename"]
        chunk_idx = chunk["metadata"]["chunk_index"]
        text = chunk["text"]
        context_parts.append(
            f"--- Source {i+1}: {filename} (chunk {chunk_idx}) ---\n{text}"
        )

    context_block = "\n\n".join(context_parts)

    return f"""Here is the relevant context retrieved from the documents:

{context_block}

---

Based ONLY on the context above, answer the following question. If the answer isn't in the context, say so honestly.

Question: {question}"""


def ask_llm(question: str, chunks: List[Dict], history: List[Dict] = None) -> Dict:
    """
    history: list of {"role": "user"/"assistant", "content": "..."} dicts
             representing the conversation so far (not including current question)
    """
    had_context = len(chunks) > 0
    history = history or []

    system_prompt = """You are Quill, a precise document intelligence assistant. You answer questions strictly based on the provided document context.

Rules:
1. Answer ONLY using information from the provided context
2. If the context doesn't contain the answer, say: "I couldn't find relevant information in the uploaded documents."
3. Never fabricate facts, statistics, or information not in the context
4. Be concise and clear
5. You may reference previous messages in the conversation for context and follow-up questions
6. When relevant, mention which source the information came from"""

    if not had_context:
        return {
            "answer": "I couldn't find relevant information in the uploaded documents to answer this question.",
            "sources": [],
            "model": "none",
            "had_context": False
        }

    # Build message list: system + history + current RAG prompt
    messages = [{"role": "system", "content": system_prompt}]

    # Add prior conversation turns (cap at last 10 to avoid token explosion)
    for turn in history[-10:]:
        messages.append({"role": turn["role"], "content": turn["content"]})

    # Current turn with RAG context injected
    messages.append({"role": "user", "content": build_rag_prompt(question, chunks)})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=1500,
        messages=messages
    )

    answer = response.choices[0].message.content

    sources = [
        {
            "filename": chunk["metadata"]["filename"],
            "chunk_index": chunk["metadata"]["chunk_index"],
            "similarity_score": chunk["similarity_score"]
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
        "model": response.model,
        "had_context": True
    }