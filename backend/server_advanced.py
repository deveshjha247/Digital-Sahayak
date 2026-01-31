"""
Advanced Routes - DS-Search & Self-Learning AI
==============================================
Separated from main server.py to keep under 50KB

Size: ~35KB | Contains: DS-Search, Self-Learning AI endpoints
Logging: logs/advanced_routes.log
"""

import gc
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(LOG_DIR / 'advanced_routes.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Router for advanced AI endpoints
advanced_router = APIRouter()

# Global instances (lazy loaded)
ds_search = None
self_learning_ai = None


def setup_advanced_routes(app, api_router, db, openai_client, get_current_user, SelfLearningAI):
    """
    Setup advanced routes with dependencies
    Called from main server.py on startup
    """
    global ds_search, self_learning_ai
    
    # Lazy import DS-Search
    from ai.search import get_ds_search_instance, DSSearch
    
    # ===================== DS-SEARCH ENDPOINTS =====================
    
    @app.post("/api/ask")
    async def ds_search_ask(request: Request, current_user: dict = Depends(get_current_user)):
        """DS-Search: User query endpoint"""
        global ds_search
        try:
            data = await request.json()
            text = data.get('text', '').strip()
            
            if not text:
                raise HTTPException(400, "Text query is required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            user_profile = await db.users.find_one({"id": current_user['id']})
            language = user_profile.get('preferred_language', 'hi') if user_profile else 'hi'
            
            response = await ds_search.search(
                query=text,
                user_id=current_user['id'],
                user_context={"profile": user_profile},
                language=language
            )
            
            gc.collect()  # Clean up after search
            
            return {
                "success": response.success,
                "answer": response.formatted_response,
                "sources": [r.to_dict() for r in response.results[:5]],
                "confidence": response.search_score,
                "intent": response.intent,
                "source_type": response.source,
                "metadata": response.metadata
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search error: {e}")
            raise HTTPException(500, f"Search error: {str(e)}")

    @app.post("/api/search/fetch")
    async def ds_search_fetch(request: Request, current_user: dict = Depends(get_current_user)):
        """DS-Search: Manual URL fetch endpoint"""
        global ds_search
        try:
            data = await request.json()
            url = data.get('url', '').strip()
            keyword = data.get('keyword', '').strip()
            
            if not url and not keyword:
                raise HTTPException(400, "URL or keyword is required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            if url:
                result = await ds_search.fetch_url(url, current_user['id'])
                return result
            else:
                user_profile = await db.users.find_one({"id": current_user['id']})
                language = user_profile.get('preferred_language', 'hi') if user_profile else 'hi'
                
                response = await ds_search.search(
                    query=keyword,
                    user_id=current_user['id'],
                    language=language
                )
                
                return {
                    "success": response.success,
                    "results": [r.to_dict() for r in response.results],
                    "summary": response.formatted_response
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search fetch error: {e}")
            raise HTTPException(500, f"Fetch error: {str(e)}")

    @app.get("/api/search/cache/status")
    async def ds_search_cache_status(current_user: dict = Depends(get_current_user)):
        """DS-Search: Get cache status"""
        global ds_search
        try:
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            status = await ds_search.get_cache_status()
            return {"success": True, "cache": status}
            
        except Exception as e:
            logger.error(f"DS-Search cache status error: {e}")
            raise HTTPException(500, f"Cache error: {str(e)}")

    # ===================== DS-SEARCH ADMIN ENDPOINTS =====================

    @app.post("/api/admin/sources/add")
    async def ds_search_add_source(request: Request, current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Add a trusted source"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            data = await request.json()
            domain = data.get('domain', '').strip()
            name = data.get('name', '').strip()
            source_type = data.get('source_type', 'aggregator')
            priority = data.get('priority', 5)
            categories = data.get('categories', [])
            
            if not domain or not name:
                raise HTTPException(400, "Domain and name are required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            success = await ds_search.add_trusted_source(
                domain=domain, name=name, source_type=source_type,
                priority=priority, categories=categories
            )
            
            return {"success": success, "message": f"Source {domain} added" if success else "Failed"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search add source error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.patch("/api/admin/sources/{domain}")
    async def ds_search_update_source(domain: str, request: Request, current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Update or block a source"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            data = await request.json()
            action = data.get('action', '')
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            if action == 'block':
                reason = data.get('reason', '')
                success = await ds_search.block_domain(domain, reason)
                return {"success": success, "message": f"Domain {domain} blocked"}
            
            return {"success": False, "message": "Invalid action"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search update source error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.get("/api/admin/sources")
    async def ds_search_list_sources(current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: List all trusted sources"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            sources = await ds_search.get_sources_list()
            return {"success": True, "sources": sources, "count": len(sources)}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search list sources error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.get("/api/admin/search/logs")
    async def ds_search_logs(limit: int = 100, current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Get search logs"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            logs = await ds_search.get_search_logs(limit)
            return {"success": True, "logs": logs, "count": len(logs)}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search logs error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.post("/api/admin/search/api/enable")
    async def ds_search_enable_api(request: Request, current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Enable paid search API"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            data = await request.json()
            api_type = data.get('api_type', '')
            api_key = data.get('api_key', '')
            daily_limit = data.get('daily_limit', 100)
            
            if not api_type or not api_key:
                raise HTTPException(400, "API type and key are required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            ds_search.enable_search_api(api_type, api_key, daily_limit)
            return {"success": True, "message": f"Search API ({api_type}) enabled"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search enable API error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.post("/api/admin/search/api/disable")
    async def ds_search_disable_api(current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Disable paid search API"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            ds_search.disable_search_api()
            return {"success": True, "message": "Search API disabled"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search disable API error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.get("/api/admin/search/api/status")
    async def ds_search_api_status(current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Get search API status"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            status = ds_search.get_api_status()
            return {"success": True, "api_status": status}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search API status error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    @app.delete("/api/admin/search/cache")
    async def ds_search_clear_cache(current_user: dict = Depends(get_current_user)):
        """DS-Search Admin: Clear all search caches"""
        global ds_search
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if ds_search is None:
                ds_search = await get_ds_search_instance(db)
            
            result = await ds_search.clear_cache()
            return {"success": True, "message": "All caches cleared", "result": result}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DS-Search clear cache error: {e}")
            raise HTTPException(500, f"Error: {str(e)}")

    # ===================== SELF-LEARNING AI ENDPOINTS =====================

    @api_router.post("/ai/learn-from-external")
    async def learn_from_external_ai(request: Request, current_user: dict = Depends(get_current_user)):
        """Learn from external AI responses"""
        try:
            data = await request.json()
            prompt = data.get('prompt')
            other_response = data.get('other_ai_response')
            ai_name = data.get('ai_name', 'External AI')
            use_web_search = data.get('use_web_search', False)
            
            if not prompt or not other_response:
                raise HTTPException(400, "prompt and other_ai_response are required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            result = await self_learning_ai.learn_from_other_ai(
                prompt, other_response, ai_name, use_web_search
            )
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Learning error: {str(e)}")

    @api_router.post("/ai/generate-smart")
    async def generate_with_learning(request: Request, current_user: dict = Depends(get_current_user)):
        """Generate smart responses using past learnings"""
        try:
            data = await request.json()
            prompt = data.get('prompt')
            context = data.get('context', '')
            use_web_search = data.get('use_web_search', False)
            
            if not prompt:
                raise HTTPException(400, "prompt is required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            result = await self_learning_ai.generate_with_learning(
                prompt, context, use_web_search
            )
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Generation error: {str(e)}")

    @api_router.post("/ai/batch-compare")
    async def batch_compare_learning(request: Request, current_user: dict = Depends(get_current_user)):
        """Compare multiple AI responses to learn best patterns"""
        try:
            data = await request.json()
            comparisons = data.get('comparisons', [])
            
            if not comparisons:
                raise HTTPException(400, "comparisons are required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            result = await self_learning_ai.compare_and_learn_batch(comparisons)
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Batch learning error: {str(e)}")

    @api_router.get("/ai/learning-stats")
    async def get_learning_statistics(current_user: dict = Depends(get_current_user)):
        """Get AI learning statistics"""
        try:
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            stats = await self_learning_ai.get_learning_stats()
            return stats
            
        except Exception as e:
            raise HTTPException(500, f"Stats error: {str(e)}")

    @api_router.post("/ai/improve-job-matching")
    async def improve_job_matching_with_ai(request: Request, current_user: dict = Depends(get_current_user)):
        """Improve job matching using AI learning"""
        try:
            data = await request.json()
            job_id = data.get('job_id')
            external_suggestions = data.get('external_suggestions')
            use_web_search = data.get('use_web_search', False)
            
            if not job_id:
                raise HTTPException(400, "job_id is required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            job = await db.jobs.find_one({"id": job_id})
            if not job:
                raise HTTPException(404, "Job not found")
            
            user_profile = {
                "education": current_user.get('education'),
                "age": current_user.get('age'),
                "state": current_user.get('state'),
                "preferred_categories": current_user.get('preferred_categories', [])
            }
            
            result = await self_learning_ai.auto_improve_job_matching(
                job, user_profile, external_suggestions, use_web_search
            )
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Job matching error: {str(e)}")

    @api_router.post("/ai/web-search")
    async def web_search_endpoint(request: Request, current_user: dict = Depends(get_current_user)):
        """Search the web for real-time information"""
        try:
            data = await request.json()
            query = data.get('query')
            max_results = data.get('max_results', 3)
            
            if not query:
                raise HTTPException(400, "query is required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            results = await self_learning_ai.web_search(query, max_results)
            return {"query": query, "results": results, "count": len(results)}
            
        except Exception as e:
            raise HTTPException(500, f"Web search error: {str(e)}")

    @api_router.get("/ai/analyze-project")
    async def analyze_project_structure(current_user: dict = Depends(get_current_user)):
        """Analyze project structure (Admin only)"""
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            analysis = await self_learning_ai.analyze_project_structure()
            return analysis
            
        except Exception as e:
            raise HTTPException(500, f"Project analysis error: {str(e)}")

    @api_router.get("/ai/project-context")
    async def get_project_context(current_user: dict = Depends(get_current_user)):
        """Get current project context known by AI"""
        try:
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            return {
                "domain": self_learning_ai.project_domain,
                "analyzed": self_learning_ai.project_files_analyzed
            }
            
        except Exception as e:
            raise HTTPException(500, f"Context error: {str(e)}")

    @api_router.post("/ai/hybrid-match")
    async def hybrid_job_matching(request: Request, current_user: dict = Depends(get_current_user)):
        """Hybrid Rule + ML based job matching"""
        try:
            data = await request.json()
            job_id = data.get('job_id')
            use_ml = data.get('use_ml', True)
            
            if not job_id:
                raise HTTPException(400, "job_id is required")
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            job = await db.jobs.find_one({"id": job_id})
            if not job:
                raise HTTPException(404, "Job not found")
            
            user_profile = {
                "id": current_user.get('id'),
                "education": current_user.get('education'),
                "age": current_user.get('age'),
                "state": current_user.get('state'),
                "preferred_categories": current_user.get('preferred_categories', []),
                "experience_years": current_user.get('experience_years', 0)
            }
            
            result = await self_learning_ai.hybrid_job_matching(job, user_profile, use_ml)
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Hybrid matching error: {str(e)}")

    @api_router.post("/ai/learn-from-logs")
    async def learn_from_interaction_logs(request: Request, current_user: dict = Depends(get_current_user)):
        """Analyze interaction logs to learn patterns (Admin only)"""
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            data = await request.json()
            days = data.get('days', 7)
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            result = await self_learning_ai.learn_from_logs(days)
            return result
            
        except Exception as e:
            raise HTTPException(500, f"Log learning error: {str(e)}")

    @api_router.post("/ai/add-rule")
    async def add_custom_matching_rule(request: Request, current_user: dict = Depends(get_current_user)):
        """Add a custom matching rule (Admin only)"""
        try:
            if not current_user.get('is_admin'):
                raise HTTPException(403, "Admin access required")
            
            data = await request.json()
            
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            success = await self_learning_ai.add_custom_rule(data)
            
            if success:
                return {"success": True, "message": "Rule added successfully"}
            else:
                raise HTTPException(500, "Failed to add rule")
            
        except Exception as e:
            raise HTTPException(500, f"Add rule error: {str(e)}")

    @api_router.get("/ai/rules")
    async def get_matching_rules(current_user: dict = Depends(get_current_user)):
        """Get all active matching rules"""
        try:
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            rules = await self_learning_ai.get_active_rules()
            return {"rules": rules, "count": len(rules)}
            
        except Exception as e:
            raise HTTPException(500, f"Get rules error: {str(e)}")

    @api_router.get("/ai/heuristic-weights")
    async def get_heuristic_weights(current_user: dict = Depends(get_current_user)):
        """Get current heuristic matching weights"""
        try:
            if not self_learning_ai:
                raise HTTPException(503, "AI Learning System not available")
            
            return {
                "weights": self_learning_ai.heuristic_weights,
                "total": sum(self_learning_ai.heuristic_weights.values())
            }
            
        except Exception as e:
            raise HTTPException(500, f"Get weights error: {str(e)}")

    # Initialize self_learning_ai if openai_client available
    if openai_client:
        self_learning_ai = SelfLearningAI(openai_client, db)
        logger.info("Self-Learning AI System initialized")
    
    logger.info("Advanced routes setup complete")
    return self_learning_ai


# Export
__all__ = ['setup_advanced_routes', 'advanced_router']
