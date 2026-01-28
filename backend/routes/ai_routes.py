"""
AI Learning Routes
Self-learning AI system endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from middleware.auth import get_current_user, get_current_admin
from models.schemas import (
    AILearnRequest, AIGenerateRequest, WebSearchRequest,
    BatchCompareRequest, JobMatchRequest
)
from config.database import get_database

router = APIRouter(prefix="/ai", tags=["AI Learning"])

# Global AI instance (initialized in main.py)
self_learning_ai = None
hybrid_matcher = None

def set_ai_instances(ai_instance, matcher_instance):
    """Set AI instances (called from main.py)"""
    global self_learning_ai, hybrid_matcher
    self_learning_ai = ai_instance
    hybrid_matcher = matcher_instance

@router.post("/learn-from-external")
async def learn_from_external_ai(
    request: AILearnRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Learn from external AI responses (Copilot, ChatGPT, etc.)
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    result = await self_learning_ai.learn_from_other_ai(
        request.prompt,
        request.other_ai_response,
        request.ai_name,
        request.use_web_search
    )
    
    return result

@router.post("/generate-smart")
async def generate_with_learning(
    request: AIGenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate smart responses using past learnings
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    result = await self_learning_ai.generate_with_learning(
        request.prompt,
        request.context,
        request.use_web_search
    )
    
    return result

@router.post("/web-search")
async def web_search(
    request: WebSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search the web for real-time information
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    results = await self_learning_ai.web_search(request.query, request.max_results)
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }

@router.get("/analyze-project")
async def analyze_project(current_user: dict = Depends(get_current_admin)):
    """
    Analyze project structure (Admin only)
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    analysis = await self_learning_ai.analyze_project_structure()
    return analysis

@router.get("/project-context")
async def get_project_context(current_user: dict = Depends(get_current_user)):
    """
    Get current project context known by AI
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    return {
        "domain": self_learning_ai.project_domain,
        "analyzed": self_learning_ai.project_files_analyzed
    }

@router.get("/learning-stats")
async def get_learning_stats(current_user: dict = Depends(get_current_user)):
    """
    Get AI learning statistics
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    stats = await self_learning_ai.get_learning_stats()
    return stats

@router.post("/batch-compare")
async def batch_compare(
    request: BatchCompareRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Compare multiple AI responses to learn patterns
    """
    if not self_learning_ai:
        raise HTTPException(503, "AI Learning System not available")
    
    result = await self_learning_ai.compare_and_learn_batch(request.comparisons)
    return result

@router.post("/hybrid-match")
async def hybrid_job_match(
    request: JobMatchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Hybrid Rule + ML job matching with log learning
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Hybrid Matcher not available")
    
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"id": request.job_id})
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Get user profile
    user_profile = {
        "id": current_user.get("id"),
        "education": current_user.get("education"),
        "age": current_user.get("age"),
        "state": current_user.get("state"),
        "preferred_categories": current_user.get("preferred_categories", [])
    }
    
    # Perform hybrid matching
    result = await hybrid_matcher.match_job_to_user(job, user_profile, use_ml=True)
    
    return result

@router.post("/update-match-outcome")
async def update_match_outcome(
    job_id: str,
    outcome: str,  # 'applied', 'ignored', 'saved'
    current_user: dict = Depends(get_current_user)
):
    """
    Update match outcome for learning
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Hybrid Matcher not available")
    
    await hybrid_matcher.update_match_outcome(job_id, current_user["id"], outcome)
    
    return {"message": "Outcome recorded for learning"}
