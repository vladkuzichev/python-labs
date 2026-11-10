from pydantic import BaseModel, ConfigDict


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doc_id: int
    title: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    total: int
    took_ms: float
    results: list[ResultOut]


class DocumentOut(BaseModel):
    doc_id: int
    path: str
    title: str
    text: str


class StatsOut(BaseModel):
    documents: int
    vocabulary: int
    tokens: int
    index_bytes: int
    uptime_s: float
