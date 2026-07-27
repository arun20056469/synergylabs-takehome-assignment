from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .logger import append_query_event
from .vector_store import SQLiteVectorStore


FALLBACK_ANSWER = "I do not have sufficient information in the provided context to answer this question."


@dataclass
class RAGPipeline:
    store: SQLiteVectorStore
    settings: Settings

    def _offline_answer(self, question: str, chunks: list[dict[str, Any]]) -> str:
        terms = set(re.findall(r"[a-z0-9]{2,}", question.lower()))
        candidates: list[tuple[int, str, dict[str, Any]]] = []
        for chunk in chunks:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk["text"]):
                overlap = len(terms & set(re.findall(r"[a-z0-9]{2,}", sentence.lower())))
                if overlap:
                    candidates.append((overlap, sentence.strip(), chunk))
        if not candidates:
            return FALLBACK_ANSWER
        candidates.sort(key=lambda value: value[0], reverse=True)
        selected: list[str] = []
        seen: set[str] = set()
        for _, sentence, chunk in candidates:
            if sentence not in seen:
                selected.append(f"{sentence} [Doc: {chunk['source']}, Chunk: {chunk['id'][:12]}]")
                seen.add(sentence)
            if len(selected) == 1:
                break
        return " ".join(selected)

    @staticmethod
    def _generation_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
        context = "\n\n".join(
            f"[Doc: {chunk['source']}, Chunk: {chunk['id']}]\n{chunk['text']}" for chunk in chunks
        )
        return f"""Answer the user's question using only the supplied context. Cite every factual sentence using its supplied [Doc: ..., Chunk: ...] marker. Do not use outside knowledge. If the context is insufficient, return exactly: {FALLBACK_ANSWER}

Context:
{context}

Question: {question}"""

    def _openai_answer(self, question: str, chunks: list[dict[str, Any]]) -> tuple[str, int, int]:
        from openai import OpenAI
        prompt = self._generation_prompt(question, chunks)
        response = OpenAI().chat.completions.create(
            model=self.settings.generation_model,
            temperature=0,
            messages=[{"role": "system", "content": "You are a precise, grounded retrieval assistant."},
                      {"role": "user", "content": prompt}],
        )
        usage = response.usage
        return (response.choices[0].message.content or FALLBACK_ANSWER,
                usage.prompt_tokens if usage else len(prompt.split()),
                usage.completion_tokens if usage else 0)

    def query(self, question: str, top_k: int | None = None, metadata_filter: dict[str, str] | None = None) -> dict[str, Any]:
        start = time.perf_counter()
        retrieved = self.store.search(question, top_k or self.settings.top_k, metadata_filter)
        retrieval_ms = (time.perf_counter() - start) * 1000
        generation_ms = 0.0
        if not retrieved or retrieved[0]["score"] < self.settings.min_similarity:
            answer, generated = FALLBACK_ANSWER, False
            prompt_tokens = completion_tokens = 0
        else:
            generation_start = time.perf_counter()
            if self.settings.generation_provider == "offline":
                answer = self._offline_answer(question, retrieved)
                prompt_tokens = sum(len(item["text"].split()) for item in retrieved) + len(question.split())
                completion_tokens = len(answer.split())
            elif self.settings.generation_provider == "openai":
                answer, prompt_tokens, completion_tokens = self._openai_answer(question, retrieved)
            else:
                raise ValueError("RAG_GENERATION_PROVIDER must be 'offline' or 'openai'.")
            generated = answer != FALLBACK_ANSWER
            generation_ms = (time.perf_counter() - generation_start) * 1000
        result = {
            "answer": answer,
            "citations": [{"chunk_id": item["id"], "source": item["source"], "score": item["score"]} for item in retrieved],
            "retrieved_chunks": retrieved,
            "telemetry": {
                "retrieval_latency_ms": round(retrieval_ms, 3),
                "generation_latency_ms": round(generation_ms, 3),
                "chunk_count": len(retrieved),
                "prompt_tokens_estimate": prompt_tokens,
                "completion_tokens_estimate": completion_tokens,
                "generation_provider": self.settings.generation_provider,
            },
        }
        append_query_event(self.settings.log_path, {"query": question, "metadata_filter": metadata_filter, **result["telemetry"]})
        return result
