from typing import final
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
import chromadb
from app.config import BASE_DIR

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_collection = None

_embedding_fn = None

# 本机装不了 torch / sentence-transformers 时，用关键词检索兜底
_embedding_available = True


def get_embedding_fn():
    global _embedding_fn, _embedding_available
    if _embedding_fn is not None:
        return _embedding_fn
    try:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
    except Exception as exc:  # ValueError: sentence_transformers 未安装
        _embedding_available = False
        print(f"[kb] 向量模型不可用，改用关键词检索：{exc}")
        return None
    return _embedding_fn


def get_collcetion() -> Collection:
    """向量库的初始化"""
    global _collection
    if _collection is not None:
        return _collection
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=get_embedding_fn()
    )
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="UTF-8").strip()
            if not text:
                continue
            docs.append(text)
            ids.append(path.stem)
            metas.append({"source": path.name})
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)
    _collection = col
    return col


def warmup():
    """启动的时候初始化向量库  启动预热"""
    if get_embedding_fn() is None:
        print("[kb] 未安装向量模型，知识库降级为关键词检索")
        return
    try:
        col = get_collcetion()
        if col.count() > 0:
            col.query(query_texts=["预热"], n_results=1)
    except Exception as exc:
        print(f"[kb] 预热跳过：{exc}")


def _read_kb():
    """读取 data/kb 下的 Markdown 资料"""
    docs = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="UTF-8").strip()
        if text:
            docs.append((path.name, text))
    return docs


def _bigrams(text: str):
    """中文按二元字组切分，英文/数字按词切分"""
    text = text.lower()
    grams = set()
    for i in range(len(text) - 1):
        gram = text[i : i + 2]
        if gram.strip() and not gram.isascii():
            grams.add(gram)
    for word in text.replace("\n", " ").split():
        if len(word) > 1 and word.isascii():
            grams.add(word)
    return grams


def _keyword_search(query: str, limit: int = 2):
    """没有向量模型时的兜底：按字组重合度给资料打分"""
    query_grams = _bigrams(query)
    if not query_grams:
        return []
    scored = []
    for name, text in _read_kb():
        doc_grams = _bigrams(text)
        hit = len(query_grams & doc_grams)
        score = hit / (len(query_grams) ** 0.5 + 1)
        # 完整的连续片段命中再加一点分
        if query.strip() and query.strip() in text:
            score += 1
        if score > 0:
            scored.append((score, name, text))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [(name, text) for _, name, text in scored[:limit]]


def search(query: str):
    """根据关键字去检索向量库"""
    if get_embedding_fn() is None:
        hits = _keyword_search(query)
        return "\n\n".join(f"[{name}]\n{text}" for name, text in hits)

    col = get_collcetion()
    if col.count() == 0:
        return ""
    limit = min(5, col.count())
    res = col.query(query_texts=[query], n_results=limit)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]

    """
    以下是检索出来的资料：
    [预约规则.md]

    # 实验室预约规则...

    
    [安全规范.md]

    安全规范....
    """
    score_parts = []
    for doc, metas, dist in zip(docs, metas, distances):
        # 0-1 越接近1表示越相关
        score = 1 / (1 + dist)
        if score < 0.5:
            continue
        name = metas.get("source") or ""
        score_parts.append({"score": score, "content": f"[{name}]\n{doc}"})
    print(f"检索出来的 score_parts：{score_parts}")
    score_parts.sort(key=lambda x: x["score"], reverse=True)
    final_parts = [item["content"] for item in score_parts[:2]]
    return "\n\n".join(final_parts)
