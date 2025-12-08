from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import UserInteraction
from app.services import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


class RecommendationRequest(BaseModel):
    """Input schema for recommendation requests"""
    category: str  # movies, tv, youtube, tiktok
    searchQuery: str = Field(..., min_length=1, max_length=200)  # what the user is searching for
    region: str = "US"
    limit: int = Field(default=20, ge=1, le=50)

    @validator('searchQuery')
    def validate_search_query(cls, v):
        # Strip whitespace
        v = v.strip()
        if not v:
            raise ValueError('Search query cannot be empty')
        if len(v) > 200:
            raise ValueError('Search query too long (max 200 characters)')
        return v


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

        # Ensure results is a list
        if results is None:
            results = []

        if not isinstance(results, list):
            print(f"Warning: results is not a list, got {type(results)}")
            results = []

        return {
            "success": True,
            "count": len(results),
            "results": results,
            "search_query": request.searchQuery,
        }

    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in recommendations endpoint: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

        # Return a more helpful error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch recommendations: {str(e)}"
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
