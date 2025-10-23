from datetime import datetime
import hashlib
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query,Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import BaseModel




@asynccontextmanager
async def life_span(app:FastAPI):
    print("Server has started!!!")
    yield 
    print("Server is shuting down !!!")




version = "v1"
app = FastAPI(
    title="String analyzer API",
    description="Project for an Intern company about String Analyzing",
    version=version,
    lifespan=life_span
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

store: Dict[str, Dict[str, Any]] = {}

# ======= Helpers =======
def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def is_palindrome(value: str) -> bool:
    s = "".join(c.lower() for c in value if c.isalnum())
    return s == s[::-1]

def word_count(value: str) -> int:
    return len(value.strip().split())

def contains_char(value: str, ch: str) -> bool:
    return ch.lower() in value.lower()

def build_properties(value: str) -> Dict[str, Any]:
    return {
            "length": len(value),
            "is_palindrome": value.lower() == value[::-1].lower(),
            "unique_characters": len(set(value)),
            "word_count": len(value.split()),
            "sha256_hash": sha256_hash(value),
            "character_frequency_map": {char: value.count(char) for char in set(value)}
    }

# ======= Schemas =======
class StringCreate(BaseModel):
    value: str

class StringResponse(BaseModel):
    id: str
    value: str
    properties: Dict[str, Any]
    created_at: str

# ======= 1. Create String =======
@app.post("/strings", response_model=StringResponse, status_code=201)
def create_string(data: StringCreate):
    if not isinstance(data.value, str):
        raise HTTPException(status_code=422, detail='Invalid data type for "value" (must be string)')
    if data.value in store:
        raise HTTPException(status_code=409, detail="String already exists in the system")

    record = {
        "id": sha256_hash(data.value),
        "value": data.value,
        "properties": build_properties(data.value),
        "created_at": now_iso(),
    }
    store[data.value] = record
    return record

# ======= 2. Get Specific String =======
@app.get("/strings/{string_value}", response_model=StringResponse)
def get_string(string_value: str):
    if string_value not in store:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    return store[string_value]

# ======= 3. Get All Strings with Filtering =======
@app.get("/strings")
def get_all_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None),
    max_length: Optional[int] = Query(None),
    word_count: Optional[int] = Query(None),
    contains_character: Optional[str] = Query(None),
):
    try:
        filtered = []
        for rec in store.values():
            v = rec["value"]
            props = rec["properties"]

            if is_palindrome is not None and props["is_palindrome"] != is_palindrome:
                continue
            if min_length is not None and len(v) < min_length:
                continue
            if max_length is not None and len(v) > max_length:
                continue
            if word_count is not None and props["word_count"] != word_count:
                continue
            if contains_character is not None and not contains_char(v, contains_character):
                continue

            filtered.append(rec)

        return {
            "data": filtered,
            "count": len(filtered),
            "filters_applied": {
                "is_palindrome": is_palindrome,
                "min_length": min_length,
                "max_length": max_length,
                "word_count": word_count,
                "contains_character": contains_character,
            },
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query parameter values or types")

# ======= 4. Natural Language Filtering =======
@app.get("/strings/filter-by-natural-language")
def filter_by_natural_language(query: str):
    q = query.lower()
    filters = {}

    # Simple heuristics for mapping
    if "palindrome" in q:
        filters["is_palindrome"] = True
    if "longer than" in q:
        try:
            num = int(q.split("longer than")[1].split()[0])
            filters["min_length"] = num + 1
        except Exception:
            pass
    if "containing the letter" in q:
        ch = q.split("containing the letter")[1].strip().split()[0]
        filters["contains_character"] = ch
    if "single word" in q:
        filters["word_count"] = 1

    # Apply filters
    try:
        results = []
        for rec in store.values():
            v = rec["value"]
            p = rec["properties"]
            ok = True
            for k, val in filters.items():
                if k == "is_palindrome" and p["is_palindrome"] != val:
                    ok = False
                elif k == "min_length" and len(v) < val:
                    ok = False
                elif k == "contains_character" and not contains_char(v, val):
                    ok = False
                elif k == "word_count" and p["word_count"] != val:
                    ok = False
            if ok:
                results.append(rec)

        return {
            "data": results,
            "count": len(results),
            "interpreted_query": {"original": query, "parsed_filters": filters},
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")

# ======= 5. Delete String =======
@app.delete("/strings/{string_value}", status_code=204)
def delete_string(string_value: str):
    if string_value not in store:
        raise HTTPException(status_code=404, detail="String does not exist in the system")
    del store[string_value]
    return None




