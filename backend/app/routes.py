from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UserInteraction
from app.services import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


class RecommendationRequest(BaseModel):
    """Input schema for recommendation requests"""
    category: str  # movies, tv, youtube, tiktok
    searchQuery: str  # what the user is searching for
    region: str = "US"
    limit: int = 20


class InteractionLog(BaseModel):
    """Schema for logging user interactions"""
    category: str
    searchQuery: str
    region: str
    recommendations: List[str]  # Video IDs
    clicked_video_id: Optional[str] = None
    clicked_position: Optional[int] = None
    session_id: str


@router.get("/health")
async def health_check():
    """
    Quick endpoint to verify the API is running.
    Frontend pings this on startup.
    """
    return {"status": "healthy", "service": "QuickFlicks API"}


@router.post("/recommendations")
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main recommendation endpoint.
    Takes user preferences and returns personalized video suggestions.
    """
    try:
        # Validate category
        valid_categories = ["movies", "tv", "youtube", "tiktok"]
        if request.category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )

        # Get recommendations from the service
        results = await recommendation_service.get_recommendations(
            category=request.category,
            search_query=request.searchQuery,
            region=request.region,
            limit=request.limit
        )

        return {
            "success": True,
            "count": len(results),
            "results": results,
            "search_query": request.searchQuery,
        }

    except Exception as e:
        # Log the error but don't expose internal details to users
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch recommendations. Please try again."
        )


@router.post("/interactions")
async def log_interaction(
    interaction: InteractionLog,
    db: AsyncSession = Depends(get_db)
):
    """
    Log user interactions for future improvements.
    Called when users filter, view results, or click on videos.
    """
    try:
        # Create database record
        db_interaction = UserInteraction(
            category=interaction.category,
            search_query=interaction.searchQuery,
            region=interaction.region,
            recommendations=interaction.recommendations,
            clicked_video_id=interaction.clicked_video_id,
            clicked_position=interaction.clicked_position,
            session_id=interaction.session_id,
        )

        db.add(db_interaction)
        await db.commit()

        return {"success": True, "message": "Interaction logged"}

    except Exception:
        # Interaction logging is non-critical, so we fail silently
        # Don't block the user experience if logging fails
        return {"success": False, "message": "Logging failed"}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Get platform statistics (for internal monitoring).
    Shows what categories are most popular, click-through rates, etc.
    """
    try:
        from sqlalchemy import select, func

        # Count total interactions
        result = await db.execute(
            select(func.count(UserInteraction.id))
        )
        total_interactions = result.scalar()

        # Count by category
        result = await db.execute(
            select(
                UserInteraction.category,
                func.count(UserInteraction.id)
            ).group_by(UserInteraction.category)
        )
        category_counts = dict(result.fetchall())

        # Count clicks
        result = await db.execute(
            select(func.count(UserInteraction.id)).where(
                UserInteraction.clicked_video_id.isnot(None)
            )
        )
        total_clicks = result.scalar()

        return {
            "total_interactions": total_interactions,
            "total_clicks": total_clicks,
            "click_through_rate": (
                round(total_clicks / total_interactions * 100, 2)
                if total_interactions > 0 else 0
            ),
            "category_breakdown": category_counts,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch stats"
        )
