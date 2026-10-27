"""
In-memory database that mimics the subset of the Motor (async MongoDB)
API that this application's routers actually use.

WHY THIS EXISTS
---------------
The platform must run for a reviewer / in a demo with NOTHING but a Groq API
key — no MongoDB account. When MONGODB_URL is empty or the cluster can't be
reached, `app.database` swaps in this MemoryDatabase. Because it exposes the
same async methods as a Motor database/collection, every router keeps calling
`db.users.find_one(...)`, `db.resumes.insert_one(...)`, etc. with no changes.

Supported surface (all that the routers use):
    db.command("ping")
    db.<collection>.create_index(...)            # no-op
    db.<collection>.insert_one(doc)              -> .inserted_id (ObjectId)
    db.<collection>.find_one(query)              -> doc | None
    db.<collection>.find(query).sort(k, dir).to_list(n)
    db.<collection>.update_one(query, {"$set":..})
    db.<collection>.find_one_and_update(query, {"$set":..}, return_document=True)
    db.<collection>.delete_one(query)            -> .deleted_count

Documents use real `bson.ObjectId` for `_id`, so router code that does
`ObjectId(id)` and queries `{"_id": ObjectId(...)}` works identically.
State is persisted to a local JSON file so it survives a reload mid-demo.
"""

import copy
import json
import logging
import os
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger(__name__)

_COLLECTIONS = ("users", "resumes", "interviews", "sessions")


# ──────────────────────────────────────────────────────────────────────────
# JSON persistence helpers (ObjectId + datetime aware)
# ──────────────────────────────────────────────────────────────────────────
def _encode(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return {"__oid__": str(obj)}
    if isinstance(obj, datetime):
        return {"__dt__": obj.isoformat()}
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def _decode(d: dict) -> Any:
    if "__oid__" in d:
        return ObjectId(d["__oid__"])
    if "__dt__" in d:
        return datetime.fromisoformat(d["__dt__"])
    return d


def _matches(doc: dict, query: dict) -> bool:
    """Equality-only matcher — the only query style the routers use."""
    for key, value in query.items():
        if doc.get(key) != value:
            return False
    return True


# ──────────────────────────────────────────────────────────────────────────
# Cursor
# ──────────────────────────────────────────────────────────────────────────
class MemoryCursor:
    def __init__(self, docs: List[dict]):
        self._docs = docs
        self._sort_key: Optional[str] = None
        self._sort_dir: int = 1

    def sort(self, key, direction: int = 1):
        # Motor accepts sort("field", -1) — that's all the routers use.
        self._sort_key = key
        self._sort_dir = direction
        return self

    async def to_list(self, length: Optional[int] = None) -> List[dict]:
        docs = self._docs
        if self._sort_key is not None:
            def _key(d):
                v = d.get(self._sort_key)
                # Normalize datetimes so naive and aware values can be compared
                # (seeded data is tz-aware; some writes used naive utcnow()).
                if isinstance(v, datetime):
                    if v.tzinfo is None:
                        v = v.replace(tzinfo=timezone.utc)
                    return (False, v.timestamp())
                return (v is None, v)
            docs = sorted(docs, key=_key, reverse=(self._sort_dir == -1))
        if length is not None:
            docs = docs[:length]
        return [copy.deepcopy(d) for d in docs]


# ──────────────────────────────────────────────────────────────────────────
# Collection
# ──────────────────────────────────────────────────────────────────────────
class MemoryCollection:
    def __init__(self, name: str, db: "MemoryDatabase"):
        self.name = name
        self._db = db
        self._docs: Dict[str, dict] = {}   # keyed by str(_id)

    # --- writes -----------------------------------------------------------
    async def insert_one(self, document: dict):
        doc = copy.deepcopy(document)
        if "_id" not in doc or doc["_id"] is None:
            doc["_id"] = ObjectId()
        self._docs[str(doc["_id"])] = doc
        self._db._save()
        return SimpleNamespace(inserted_id=doc["_id"], acknowledged=True)

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        for doc in self._docs.values():
            if _matches(doc, query):
                self._apply_update(doc, update)
                self._db._save()
                return SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            new_doc = {k: v for k, v in query.items()}
            self._apply_update(new_doc, update)
            return await self.insert_one(new_doc)
        return SimpleNamespace(matched_count=0, modified_count=0)

    async def find_one_and_update(self, query: dict, update: dict,
                                  return_document=True, **_kw):
        for doc in self._docs.values():
            if _matches(doc, query):
                self._apply_update(doc, update)
                self._db._save()
                # return_document truthy == ReturnDocument.AFTER
                return copy.deepcopy(doc)
        return None

    async def delete_one(self, query: dict):
        for key, doc in list(self._docs.items()):
            if _matches(doc, query):
                del self._docs[key]
                self._db._save()
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    @staticmethod
    def _apply_update(doc: dict, update: dict) -> None:
        if "$set" in update:
            doc.update(update["$set"])
        # support a raw replacement-style dict too (not used, but safe)
        for k, v in update.items():
            if not k.startswith("$"):
                doc[k] = v

    # --- reads ------------------------------------------------------------
    async def find_one(self, query: Optional[dict] = None) -> Optional[dict]:
        query = query or {}
        for doc in self._docs.values():
            if _matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query: Optional[dict] = None) -> MemoryCursor:
        query = query or {}
        matches = [d for d in self._docs.values() if _matches(d, query)]
        return MemoryCursor(matches)

    async def count_documents(self, query: Optional[dict] = None) -> int:
        query = query or {}
        return sum(1 for d in self._docs.values() if _matches(d, query))

    # --- schema (no-ops) --------------------------------------------------
    async def create_index(self, *args, **kwargs):
        return None


# ──────────────────────────────────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────────────────────────────────
class MemoryDatabase:
    def __init__(self, path: Optional[str] = None):
        self._path = path
        self._collections: Dict[str, MemoryCollection] = {
            name: MemoryCollection(name, self) for name in _COLLECTIONS
        }
        self._load()

    def __getattr__(self, name: str) -> MemoryCollection:
        # Only called for attributes not found normally (i.e. collection access).
        if name.startswith("_"):
            raise AttributeError(name)
        collections = self.__dict__.get("_collections")
        if collections is None:
            raise AttributeError(name)
        if name not in collections:
            collections[name] = MemoryCollection(name, self)
        return collections[name]

    async def command(self, *_args, **_kwargs) -> dict:
        # health check "ping"
        return {"ok": 1.0}

    # --- persistence ------------------------------------------------------
    def _save(self) -> None:
        if not self._path:
            return
        try:
            data = {
                name: list(col._docs.values())
                for name, col in self._collections.items()
            }
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, default=_encode)
            os.replace(tmp, self._path)
        except Exception as e:  # never let persistence crash a request
            logger.warning(f"MemoryDatabase save failed (ignored): {e}")

    def _load(self) -> None:
        if not self._path or not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f, object_hook=_decode)
            for name, docs in data.items():
                col = self._collections.setdefault(name, MemoryCollection(name, self))
                col._docs = {str(d["_id"]): d for d in docs}
            logger.info(f"MemoryDatabase loaded from {self._path}")
        except Exception as e:
            logger.warning(f"MemoryDatabase load failed (starting empty): {e}")
