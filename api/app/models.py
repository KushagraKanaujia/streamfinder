from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float

from app.database import Base


class UserInteraction(Base):
    """
    Tracks user interactions for future improvements.
    Every filter choice and click gets logged here so we can build
    better recommendations over time.
    """

    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # What they were looking for
    category = Column(String, index=True)  # movies, tv, youtube, tiktok
    search_query = Column(String)  # what the user searched for
    region = Column(String, index=True)

    # What we showed them
    recommendations = Column(JSON)  # List of video IDs

    # What they actually clicked
    clicked_video_id = Column(String, nullable=True)
    clicked_position = Column(Integer, nullable=True)  # Which result # they clicked

    # Session tracking
    session_id = Column(String, index=True)

    def __repr__(self):
        return f"<Interaction {self.id} - {self.category} at {self.timestamp}>"
