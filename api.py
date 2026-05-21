"""
CIPHER REST API
Exposes the code review pipeline as a FastAPI endpoint.
Run with: uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.ingestion import RepositoryIngestor
from pipeline.parser import ASTParser, build_call_graph
from pipeline.reviewer import LLMReviewer, compute_health_score
from utils.token_counter import batch_code_blocks

app = FastAPI(
    title="CIPHER API",
    description="Autonomous AI Code Review Agent REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    repo_url: str
    max_batches: int = 10


class ReviewResponse(BaseModel):
    repo_url: str
    total_findings: int
    health_score: int
    findings: list[dict]


@app.get("/health")
def health_check():
    return {"status": "operational", "version": "1.0.0"}


@app.post("/review", response_model=ReviewResponse)
def review_repository(request: ReviewRequest):
    try:
        ingestor = RepositoryIngestor(request.repo_url)
        temp_dir = ingestor.clone_and_get_path()
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    code_blocks = ASTParser.extract_code_blocks(temp_dir.name)
    call_graph = build_call_graph(temp_dir.name)
    temp_dir.cleanup()

    if not code_blocks:
        return ReviewResponse(
            repo_url=request.repo_url,
            total_findings=0,
            health_score=100,
            findings=[],
        )

    batches = batch_code_blocks(code_blocks)[: request.max_batches]

    try:
        reviewer = LLMReviewer()
        all_reviews = reviewer.analyze_all_batches(batches, call_graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    health = compute_health_score(all_reviews)

    return ReviewResponse(
        repo_url=request.repo_url,
        total_findings=len(all_reviews),
        health_score=health["score"],
        findings=[r.model_dump() for r in all_reviews],
    )
