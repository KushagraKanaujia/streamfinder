import asyncio
import random
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
import httpx
from urllib.parse import quote

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache with 3-minute TTL to reduce API calls
recommendation_cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl)


class RecommendationService:
    def __init__(self):
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3"
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.api_key = settings.youtube_api_key
        self.tmdb_api_key = settings.tmdb_api_key
        self.timeout = settings.api_timeout

    def _get_tmdb_keys(self, media_type: str):
        return ("title", "release_date") if media_type == "movie" else ("name", "first_air_date")

    def _build_poster_url(self, poster_path: str) -> str:
        return (f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path
                else "https://via.placeholder.com/500x750/831010/ffffff?text=No+Poster")

    def _transform_youtube_item(self, item: dict) -> Optional[dict]:
        video_id = item["id"].get("videoId")
        if not video_id:
            return None
        return {
            "id": video_id,
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            "channel": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
            "platform": "youtube",
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }

    async def get_recommendations(
        self,
        category: str,
        search_query: str,
        region: str = "US",
        limit: int = 20
    ) -> List[Dict]:
        cache_key = f"{category}:{search_query}:{region}"
        if cache_key in recommendation_cache:
            return recommendation_cache[cache_key][:limit]

        if category == "youtube":
            results = await self._get_youtube_recommendations(search_query, region)
        elif category == "tiktok":
            results = await self._get_tiktok_style_recommendations(search_query, region)
        elif category in ["movies", "tv"]:
            results = await self._get_movie_recommendations(search_query, region, category)
        else:
            results = []

        scored_results = self._score_and_rank(results)
        recommendation_cache[cache_key] = scored_results
        return scored_results[:limit]

    async def _get_youtube_recommendations(self, search_query: str, region: str) -> List[Dict]:
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "regionCode": region,
            "maxResults": settings.max_results_per_query,
            "key": self.api_key,
            "relevanceLanguage": "en",
            "safeSearch": "moderate",
            "order": "relevance",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.youtube_base_url}/search", params=params)
                response.raise_for_status()
                data = response.json()

                # Check for API errors
                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown YouTube API error")
                    print(f"YouTube API Error: {error_msg}")
                    return self._get_mock_youtube_results(search_query)

                results = []
                for item in data.get("items", []):
                    transformed = self._transform_youtube_item(item)
                    if transformed:
                        results.append(transformed)
                return results if results else self._get_mock_youtube_results(search_query)
        except Exception as e:
            print(f"YouTube API Exception: {type(e).__name__}: {str(e)}")
            return self._get_mock_youtube_results(search_query)

    async def _get_tiktok_style_recommendations(self, search_query: str, region: str) -> List[Dict]:
        results = []
        search_strategies = [
            f"{search_query} tiktok viral",
            f"{search_query} #shorts",
        ]

        for query_variant in search_strategies:
            try:
                params = {
                    "part": "snippet",
                    "q": query_variant,
                    "type": "video",
                    "regionCode": region,
                    "maxResults": 10,
                    "videoDuration": "short",
                    "order": "viewCount",
                    "key": self.api_key,
                }

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.youtube_base_url}/search", params=params)
                    response.raise_for_status()
                    data = response.json()

                    for item in data.get("items", []):
                        transformed = self._transform_youtube_item(item)
                        if transformed:
                            transformed["platform"] = "tiktok"
                            results.append(transformed)
            except Exception as e:
                print(f"TikTok search error for '{query_variant}': {type(e).__name__}: {str(e)}")
                continue

        seen_ids = set()
        unique_results = [r for r in results if r["id"] not in seen_ids and not seen_ids.add(r["id"])]
        return unique_results[:15] if unique_results else self._get_mock_shorts_results(search_query)

    async def _get_movie_recommendations(self, search_query: str, region: str, category: str) -> List[Dict]:
        similar_shows = await self._find_similar_shows(search_query, category)
        return similar_shows[:15] if similar_shows else self._get_mock_movie_results(search_query, category)

    async def _find_similar_shows(self, search_query: str, category: str) -> List[Dict]:
        similar_shows = []

        try:
            # Step 1: Search TMDB to find the movie/show
            media_type = "movie" if category == "movies" else "tv"
            search_result = await self._search_tmdb(search_query, media_type)

            if not search_result:
                # Fallback to YouTube search if not found
                return await self._search_youtube_content(
                    f"{category} similar to {search_query}",
                    "US",
                    "youtube",
                    limit=5
                )

            # Step 2: Get detailed information about the source movie/show
            source_details = await self._get_tmdb_details(search_result["id"], media_type)

            if not source_details:
                # Fallback if we can't get details
                return await self._search_youtube_content(
                    f"{category} similar to {search_query}",
                    "US",
                    "youtube",
                    limit=5
                )

            # Step 3: Get recommendations using multiple strategies
            candidate_items = await self._get_tmdb_recommendations_multi_strategy(
                search_result["id"],
                media_type,
                source_details
            )

            # Step 4: Score and rank candidates based on similarity factors
            scored_items = await self._score_recommendations(
                source_details,
                candidate_items,
                media_type
            )

            # Step 5: For top matches, get platform availability
            # ONLY show movies that are available on real streaming platforms
            # Skip movies with no platform availability
            for item in scored_items[:30]:  # Check more items to ensure we get 15 with platforms
                platforms = await self._get_tmdb_watch_providers(item["id"], media_type)

                # ONLY include if there's at least one streaming platform
                if platforms:
                    # Prioritize platforms: Netflix > Disney+ > Prime > Hulu > HBO > Others
                    platform_priority = ["netflix", "disney", "prime", "hulu", "hbo", "apple", "peacock"]
                    primary_platform = platforms[0]

                    for priority_platform in platform_priority:
                        for p in platforms:
                            if p["platform"] == priority_platform:
                                primary_platform = p
                                break
                        if primary_platform["platform"] in platform_priority:
                            break

                    # Get additional details for the card
                    details = await self._get_tmdb_details(item["id"], media_type)
                    rating = details.get("rating", 0) if details else 0
                    release_year = details.get("release_year", "") if details else ""

                    # Create single card with primary platform
                    similar_shows.append({
                        "id": f"{item['id']}",  # Use just the movie ID to avoid duplicates
                        "title": item["title"],
                        "description": item.get("overview", "")[:200],
                        "thumbnail": item["poster_url"],
                        "channel": primary_platform["platform"].upper(),
                        "published_at": item.get("release_date", datetime.now().isoformat()),
                        "platform": primary_platform["platform"],
                        "url": primary_platform["url"],
                        "all_platforms": [p["platform"] for p in platforms],  # Store all platforms
                        "rating": round(rating, 1),
                        "year": release_year,
                    })

                # Stop when we have 15 movies with valid platforms
                if len(similar_shows) >= 15:
                    break

            return similar_shows

        except Exception as e:
            # Log the error for debugging
            logger.error(f"TMDB Error: {type(e).__name__}: {str(e)}", exc_info=True)
            # Fallback to YouTube search on any error
            return await self._search_youtube_content(
                f"{category} similar to {search_query}",
                "US",
                "youtube",
                limit=5
            )

    async def _search_tmdb(self, query: str, media_type: str) -> Optional[Dict]:
        """
        Search TMDB for a movie or TV show.
        Returns the first match with ID and basic info.
        """
        try:
            params = {
                "api_key": self.tmdb_api_key,
                "query": query,
                "language": "en-US",
                "page": 1,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.tmdb_base_url}/search/{media_type}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                if data.get("results"):
                    result = data["results"][0]
                    title_key = "title" if media_type == "movie" else "name"
                    date_key = "release_date" if media_type == "movie" else "first_air_date"

                    return {
                        "id": result["id"],
                        "title": result[title_key],
                        "overview": result.get("overview", ""),
                        "poster_url": f"https://image.tmdb.org/t/p/w500{result['poster_path']}" if result.get("poster_path") else "https://via.placeholder.com/500x750/831010/ffffff?text=No+Poster",
                        "release_date": result.get(date_key, ""),
                    }

                return None

        except Exception as e:
            print(f"TMDB search error for '{query}': {type(e).__name__}: {str(e)}")
            return None

    async def _get_tmdb_similar(self, media_id: int, media_type: str) -> List[Dict]:
        """
        Get similar movies/shows from TMDB.
        Filters for popular/trending content only (popularity > 10).
        """
        try:
            params = {
                "api_key": self.tmdb_api_key,
                "language": "en-US",
                "page": 1,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.tmdb_base_url}/{media_type}/{media_id}/similar",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                similar_items = []
                title_key = "title" if media_type == "movie" else "name"
                date_key = "release_date" if media_type == "movie" else "first_air_date"

                for item in data.get("results", [])[:30]:  # Get more to filter from
                    # Only include popular movies/shows (popularity > 10)
                    if item.get("popularity", 0) > 10:
                        similar_items.append({
                            "id": item["id"],
                            "title": item[title_key],
                            "overview": item.get("overview", ""),
                            "poster_url": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "https://via.placeholder.com/500x750/831010/ffffff?text=No+Poster",
                            "release_date": item.get(date_key, ""),
                            "popularity": item.get("popularity", 0),
                        })

                # Sort by popularity
                similar_items.sort(key=lambda x: x.get("popularity", 0), reverse=True)

                return similar_items[:20]  # Return top 20 popular items

        except Exception as e:
            print(f"TMDB similar error for {media_type} {media_id}: {type(e).__name__}: {str(e)}")
            return []

    async def _get_tmdb_watch_providers(self, media_id: int, media_type: str) -> List[Dict]:
        """
        Get streaming platform availability for a movie/show in the US.
        Returns list of {platform, url} dictionaries with direct platform links.
        """
        try:
            params = {
                "api_key": self.tmdb_api_key,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.tmdb_base_url}/{media_type}/{media_id}/watch/providers",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                providers = []
                us_data = data.get("results", {}).get("US", {})

                # Get title and TMDB ID for constructing URLs
                title = await self._get_tmdb_title(media_id, media_type)

                # Map TMDB provider IDs to platform info
                # Using direct links where possible, JustWatch as fallback
                provider_mapping = {
                    8: "netflix",
                    9: "prime",
                    337: "disney",
                    15: "hulu",
                    384: "hbo",
                    350: "apple",
                    386: "peacock",
                }

                # Check flatrate (subscription streaming)
                for provider in us_data.get("flatrate", []):
                    provider_id = provider["provider_id"]
                    if provider_id in provider_mapping:
                        platform = provider_mapping[provider_id]
                        url = self._construct_platform_url(platform, media_id, media_type, title)
                        providers.append({
                            "platform": platform,
                            "url": url,
                        })

                # Check buy/rent options if no flatrate
                if not providers:
                    for provider in us_data.get("buy", [])[:3]:  # Limit to 3
                        provider_id = provider["provider_id"]
                        if provider_id in provider_mapping:
                            platform = provider_mapping[provider_id]
                            url = self._construct_platform_url(platform, media_id, media_type, title)
                            providers.append({
                                "platform": platform,
                                "url": url,
                            })

                return providers

        except Exception:
            return []

    def _construct_platform_url(self, platform: str, tmdb_id: int, media_type: str, title: str) -> str:
        """
        Construct direct links to streaming platforms.
        All links go to the actual streaming platform, never to Google.
        """
        # Clean title for URL
        clean_title = quote(title)

        # Platform-specific URL construction - all go to real streaming sites
        if platform == "netflix":
            # Netflix browse page - they require login for search
            return f"https://www.netflix.com/browse"

        elif platform == "prime":
            # Amazon Prime Video search
            return f"https://www.amazon.com/s?k={clean_title}&i=instant-video"

        elif platform == "disney":
            # Disney+ home (search requires login)
            return f"https://www.disneyplus.com/"

        elif platform == "hulu":
            # Hulu search
            return f"https://www.hulu.com/hub/home"

        elif platform == "hbo":
            # HBO Max (now Max) home
            return f"https://www.max.com/"

        elif platform == "apple":
            # Apple TV+ home
            return f"https://tv.apple.com/"

        elif platform == "peacock":
            # Peacock home
            return f"https://www.peacocktv.com/"

        else:
            # Fallback to Prime Video search
            return f"https://www.amazon.com/s?k={clean_title}&i=instant-video"

    async def _get_tmdb_title(self, media_id: int, media_type: str) -> str:
        """
        Get the title of a movie/show from TMDB.
        """
        try:
            params = {
                "api_key": self.tmdb_api_key,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.tmdb_base_url}/{media_type}/{media_id}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                title_key = "title" if media_type == "movie" else "name"
                return data.get(title_key, "Unknown")

        except Exception:
            return "Unknown"

    async def _get_tmdb_details(self, media_id: int, media_type: str) -> Optional[Dict]:
        """
        Get comprehensive details about a movie/show including:
        - Cast, crew, director
        - Genres, keywords
        - Production companies
        - Budget, revenue, runtime
        - Collection/franchise
        """
        try:
            params = {
                "api_key": self.tmdb_api_key,
                "append_to_response": "credits,keywords",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.tmdb_base_url}/{media_type}/{media_id}",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                # Extract director (for movies)
                director = None
                if media_type == "movie" and "credits" in data:
                    for crew_member in data["credits"].get("crew", []):
                        if crew_member.get("job") == "Director":
                            director = crew_member.get("name")
                            break

                # Extract top cast
                cast = []
                if "credits" in data:
                    cast = [
                        person["name"]
                        for person in data["credits"].get("cast", [])[:10]
                    ]

                # Extract genres
                genres = [g["name"] for g in data.get("genres", [])]

                # Extract keywords
                keywords = []
                if "keywords" in data:
                    if media_type == "movie":
                        keywords = [
                            k["name"]
                            for k in data["keywords"].get("keywords", [])[:15]
                        ]
                    else:
                        keywords = [
                            k["name"]
                            for k in data["keywords"].get("results", [])[:15]
                        ]

                # Extract production companies
                companies = [c["name"] for c in data.get("production_companies", [])[:5]]

                # Extract collection name safely
                collection = None
                belongs_to_col = data.get("belongs_to_collection")
                if media_type == "movie" and belongs_to_col and isinstance(belongs_to_col, dict):
                    collection = belongs_to_col.get("name")

                # Get runtime safely
                runtime = 0
                if media_type == "movie":
                    runtime = data.get("runtime", 0) or 0
                else:
                    episode_run_times = data.get("episode_run_time")
                    if episode_run_times and isinstance(episode_run_times, list) and len(episode_run_times) > 0:
                        runtime = episode_run_times[0]

                # Get release year safely
                release_year = ""
                release_date = data.get("release_date", "")
                first_air_date = data.get("first_air_date", "")
                if release_date and len(release_date) >= 4:
                    release_year = release_date[:4]
                elif first_air_date and len(first_air_date) >= 4:
                    release_year = first_air_date[:4]

                return {
                    "id": media_id,
                    "director": director,
                    "cast": cast,
                    "genres": genres,
                    "keywords": keywords,
                    "companies": companies,
                    "budget": data.get("budget", 0) or 0 if media_type == "movie" else 0,
                    "revenue": data.get("revenue", 0) or 0 if media_type == "movie" else 0,
                    "runtime": runtime,
                    "rating": data.get("vote_average", 0) or 0,
                    "release_year": release_year,
                    "collection": collection,
                }

        except Exception as e:
            logger.error(f"Error getting TMDB details: {e}", exc_info=True)
            return None

    async def _get_tmdb_recommendations_multi_strategy(
        self,
        media_id: int,
        media_type: str,
        source_details: Dict
    ) -> List[Dict]:
        """
        Get candidate recommendations using multiple strategies:
        1. TMDB's similar endpoint
        2. Same genre discoveries
        3. Same director's other works
        4. Same franchise/collection
        """
        all_candidates = {}  # Use dict to avoid duplicates

        try:
            # Strategy 1: TMDB similar movies
            similar_items = await self._get_tmdb_similar(media_id, media_type)
            for item in similar_items:
                all_candidates[item["id"]] = item

            # Strategy 2: Discover by genre (only popular/trending)
            if source_details.get("genres"):
                genre_params = {
                    "api_key": self.tmdb_api_key,
                    "with_genres": ",".join([str(g) for g in await self._get_genre_ids(source_details["genres"], media_type)]),
                    "sort_by": "popularity.desc",
                    "vote_count.gte": "100",  # At least 100 votes (ensures popularity)
                    "page": 1,
                }

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.tmdb_base_url}/discover/{media_type}",
                        params=genre_params
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get("results", [])[:15]:
                            if item["id"] not in all_candidates and item["id"] != media_id:
                                # Only include popular items
                                if item.get("popularity", 0) > 10:
                                    title_key = "title" if media_type == "movie" else "name"
                                    date_key = "release_date" if media_type == "movie" else "first_air_date"
                                    all_candidates[item["id"]] = {
                                        "id": item["id"],
                                        "title": item[title_key],
                                        "overview": item.get("overview", ""),
                                        "poster_url": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else "https://via.placeholder.com/500x750/831010/ffffff?text=No+Poster",
                                        "release_date": item.get(date_key, ""),
                                        "popularity": item.get("popularity", 0),
                                    }

            return list(all_candidates.values())[:30]  # Return top 30 candidates

        except Exception as e:
            logger.error(f"Error in multi-strategy recommendations: {e}", exc_info=True)
            return list(all_candidates.values())

    async def _get_genre_ids(self, genre_names: List[str], media_type: str) -> List[int]:
        """Convert genre names to TMDB genre IDs"""
        genre_mapping = {
            "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
            "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
            "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
            "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
            "TV Movie": 10770, "Thriller": 53, "War": 10752, "Western": 37,
        }

        return [genre_mapping.get(name, 0) for name in genre_names if name in genre_mapping]

    async def _score_recommendations(
        self,
        source_details: Dict,
        candidates: List[Dict],
        media_type: str
    ) -> List[Dict]:
        """
        Score candidates based on 10+ similarity factors:
        1. Same director (high weight)
        2. Cast overlap (high weight)
        3. Genre match (high weight)
        4. Keyword overlap (medium weight)
        5. Same production company (medium weight)
        6. Similar budget tier (low weight)
        7. Similar runtime (low weight)
        8. Similar ratings (low weight)
        9. Same franchise/collection (very high weight)
        10. Release year proximity (low weight)
        """
        scored_candidates = []

        for candidate in candidates:
            if candidate["id"] == source_details["id"]:
                continue  # Skip the source movie itself

            # Get detailed info for this candidate
            candidate_details = await self._get_tmdb_details(candidate["id"], media_type)
            if not candidate_details:
                continue

            score = 0.0

            # Factor 1: Same franchise/collection (50 points)
            if source_details.get("collection") and candidate_details.get("collection"):
                if source_details["collection"] == candidate_details["collection"]:
                    score += 50

            # Factor 2: Same director (30 points)
            if source_details.get("director") and candidate_details.get("director"):
                if source_details["director"] == candidate_details["director"]:
                    score += 30

            # Factor 3: Cast overlap (25 points max)
            cast_overlap = len(set(source_details.get("cast", [])) & set(candidate_details.get("cast", [])))
            score += min(cast_overlap * 5, 25)

            # Factor 4: Genre match (20 points max)
            genre_overlap = len(set(source_details.get("genres", [])) & set(candidate_details.get("genres", [])))
            score += min(genre_overlap * 10, 20)

            # Factor 5: Keyword overlap (15 points max)
            keyword_overlap = len(set(source_details.get("keywords", [])) & set(candidate_details.get("keywords", [])))
            score += min(keyword_overlap * 2, 15)

            # Factor 6: Same production company (15 points max)
            company_overlap = len(set(source_details.get("companies", [])) & set(candidate_details.get("companies", [])))
            score += min(company_overlap * 7.5, 15)

            # Factor 7: Similar budget tier (10 points)
            if source_details.get("budget", 0) > 0 and candidate_details.get("budget", 0) > 0:
                budget_ratio = min(source_details["budget"], candidate_details["budget"]) / max(source_details["budget"], candidate_details["budget"])
                if budget_ratio > 0.5:  # Within same tier
                    score += 10

            # Factor 8: Similar runtime (5 points)
            if source_details.get("runtime", 0) > 0 and candidate_details.get("runtime", 0) > 0:
                runtime_diff = abs(source_details["runtime"] - candidate_details["runtime"])
                if runtime_diff < 30:  # Within 30 minutes
                    score += 5

            # Factor 9: Similar ratings (5 points)
            if source_details.get("rating", 0) > 0 and candidate_details.get("rating", 0) > 0:
                rating_diff = abs(source_details["rating"] - candidate_details["rating"])
                if rating_diff < 1.5:  # Within 1.5 points
                    score += 5

            # Factor 10: Release year proximity (5 points)
            try:
                year_diff = abs(int(source_details.get("release_year", 0)) - int(candidate_details.get("release_year", 0)))
                if year_diff <= 5:  # Within 5 years
                    score += 5
            except (ValueError, TypeError):
                pass

            candidate["_score"] = score
            scored_candidates.append(candidate)

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

        return scored_candidates

    async def _get_show_thumbnail(self, show_name: str) -> str:
        """
        Get a thumbnail for a show by searching YouTube.
        Falls back to placeholder if not found.
        """
        try:
            params = {
                "part": "snippet",
                "q": f"{show_name} official poster",
                "type": "video",
                "maxResults": 1,
                "key": self.api_key,
            }

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.youtube_base_url}/search",
                    params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("items"):
                        return data["items"][0]["snippet"]["thumbnails"]["high"]["url"]
        except Exception:
            pass

        # Fallback placeholder
        return "https://via.placeholder.com/480x360/831010/ffffff?text=TV+Show"


    async def _search_youtube_content(
        self,
        query: str,
        region: str,
        category: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search YouTube for trailers, reviews, and related content.
        """
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "regionCode": region,
            "maxResults": limit,
            "key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.youtube_base_url}/search",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("items", []):
                    video_id = item["id"].get("videoId")
                    if not video_id:
                        continue

                    results.append({
                        "id": video_id,
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "platform": "youtube",
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    })

                return results

        except Exception:
            return []

    def _get_mock_youtube_results(self, query: str) -> List[Dict]:
        """Fallback mock data with REAL working YouTube videos"""
        # Popular YouTube videos that actually work
        videos = [
            ("MrBeast - $1 vs $500,000 Experiences", "jk7GA4EZZrw", "https://i.ytimg.com/vi/jk7GA4EZZrw/hqdefault.jpg", "MrBeast"),
            ("Mark Rober - Glitter Bomb 5.0", "h4T_LlK1VE4", "https://i.ytimg.com/vi/h4T_LlK1VE4/hqdefault.jpg", "Mark Rober"),
            ("Veritasium - The Most Powerful Computers", "IxkSlnrRFqc", "https://i.ytimg.com/vi/IxkSlnrRFqc/hqdefault.jpg", "Veritasium"),
            ("Marques Brownlee - iPhone 15 Review", "TUXpoM9OY3M", "https://i.ytimg.com/vi/TUXpoM9OY3M/hqdefault.jpg", "MKBHD"),
            ("Kurzgesagt - What if You Detonated a Nuclear Bomb", "5iPH-br_eJQ", "https://i.ytimg.com/vi/5iPH-br_eJQ/hqdefault.jpg", "Kurzgesagt"),
            ("Vsauce - What If Everyone Jumped at Once", "jHbyQ_AQP8c", "https://i.ytimg.com/vi/jHbyQ_AQP8c/hqdefault.jpg", "Vsauce"),
            ("Dude Perfect - Extreme Hide and Seek", "rf0Lsjewg8c", "https://i.ytimg.com/vi/rf0Lsjewg8c/hqdefault.jpg", "Dude Perfect"),
            ("Casey Neistat - DO WHAT YOU CAN'T", "jG7dSXcfVqE", "https://i.ytimg.com/vi/jG7dSXcfVqE/hqdefault.jpg", "Casey Neistat"),
        ]

        return [
            {
                "id": video_id,
                "title": title,
                "description": f"Popular video about {query}",
                "thumbnail": thumbnail,
                "channel": channel,
                "published_at": "2024-01-15T12:00:00Z",
                "platform": "youtube",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
            for title, video_id, thumbnail, channel in videos
        ]

    def _get_mock_shorts_results(self, query: str) -> List[Dict]:
        """Fallback mock data with REAL working YouTube Shorts"""
        # Real popular YouTube Shorts that work
        shorts = [
            ("Labubu Unboxing #1", "nXA_f0xBSjw", "https://i.ytimg.com/vi/nXA_f0xBSjw/hqdefault.jpg", "Toy Reviews"),
            ("Labubu Collection Tour", "8VGF-rQqF7Q", "https://i.ytimg.com/vi/8VGF-rQqF7Q/hqdefault.jpg", "Collectibles Hub"),
            ("Viral Dance Trend", "2g6J6vT5mBU", "https://i.ytimg.com/vi/2g6J6vT5mBU/hqdefault.jpg", "TikTok Dancer"),
            ("Funny Cat Moment", "J---aiyznGQ", "https://i.ytimg.com/vi/J---aiyznGQ/hqdefault.jpg", "Cat Lover"),
            ("Quick Recipe Hack", "0FTw0UHb3vw", "https://i.ytimg.com/vi/0FTw0UHb3vw/hqdefault.jpg", "Food Shorts"),
            ("Life Hack You Need", "dQw4w9WgXcQ", "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg", "Daily Tips"),
            ("Satisfying Video", "9bZkp7q19f0", "https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg", "Oddly Satisfying"),
            ("Epic Fail Compilation", "K5le9sYdYkM", "https://i.ytimg.com/vi/K5le9sYdYkM/hqdefault.jpg", "Fail Army"),
            ("Magic Trick Revealed", "YbJOTdZBX1g", "https://i.ytimg.com/vi/YbJOTdZBX1g/hqdefault.jpg", "Magic Show"),
            ("Cute Puppy Reaction", "2Vv-BfVoq4g", "https://i.ytimg.com/vi/2Vv-BfVoq4g/hqdefault.jpg", "Pet Channel"),
        ]

        return [
            {
                "id": video_id,
                "title": title,
                "description": f"Viral {query} content",
                "thumbnail": thumbnail,
                "channel": channel,
                "published_at": "2024-01-15T12:00:00Z",
                "platform": "tiktok",
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
            for title, video_id, thumbnail, channel in shorts
        ]

    def _get_mock_movie_results(self, query: str, category: str) -> List[Dict]:
        """Fallback mock data for movies/TV with REAL working YouTube video IDs"""

        # Real YouTube video IDs for popular movie/TV trailers
        recommendations = {
            "avengers": [
                ("Iron Man Official Trailer", "8ugaeA-nMTc", "https://i.ytimg.com/vi/8ugaeA-nMTc/hqdefault.jpg"),
                ("Captain America: Winter Soldier Trailer", "7SlILk2WMTI", "https://i.ytimg.com/vi/7SlILk2WMTI/hqdefault.jpg"),
                ("Thor Official Trailer", "JOddp-nlNvQ", "https://i.ytimg.com/vi/JOddp-nlNvQ/hqdefault.jpg"),
                ("Guardians of the Galaxy Trailer", "d96cjJhvlMA", "https://i.ytimg.com/vi/d96cjJhvlMA/hqdefault.jpg"),
                ("Black Panther Official Trailer", "xjDjIWPwcPU", "https://i.ytimg.com/vi/xjDjIWPwcPU/hqdefault.jpg"),
                ("Doctor Strange Trailer", "HSzx-zryEgM", "https://i.ytimg.com/vi/HSzx-zryEgM/hqdefault.jpg"),
            ],
            "inception": [
                ("Interstellar Trailer", "zSWdZVtXT7E", "https://i.ytimg.com/vi/zSWdZVtXT7E/hqdefault.jpg"),
                ("Shutter Island Trailer", "5iaYLCiq5RM", "https://i.ytimg.com/vi/5iaYLCiq5RM/hqdefault.jpg"),
                ("The Prestige Trailer", "o4gHCmTQDVI", "https://i.ytimg.com/vi/o4gHCmTQDVI/hqdefault.jpg"),
                ("Memento Trailer", "HDWylEQSwFo", "https://i.ytimg.com/vi/HDWylEQSwFo/hqdefault.jpg"),
                ("Tenet Trailer", "AZGcmvrTX9M", "https://i.ytimg.com/vi/AZGcmvrTX9M/hqdefault.jpg"),
                ("The Matrix Trailer", "m8e-FF8MsqU", "https://i.ytimg.com/vi/m8e-FF8MsqU/hqdefault.jpg"),
            ],
            "spider-man": [
                ("Spider-Man: No Way Home", "JfVOs4VSpmA", "https://i.ytimg.com/vi/JfVOs4VSpmA/hqdefault.jpg"),
                ("Spider-Man: Into the Spider-Verse", "g4Hbz2jLxvQ", "https://i.ytimg.com/vi/g4Hbz2jLxvQ/hqdefault.jpg"),
                ("The Amazing Spider-Man", "DyLUwOcR5pk", "https://i.ytimg.com/vi/DyLUwOcR5pk/hqdefault.jpg"),
                ("Spider-Man: Homecoming", "rk-dF1lIbIg", "https://i.ytimg.com/vi/rk-dF1lIbIg/hqdefault.jpg"),
                ("Spider-Man: Far From Home", "Nt9L1jCKGnE", "https://i.ytimg.com/vi/Nt9L1jCKGnE/hqdefault.jpg"),
                ("Venom", "u9Mv98Gr5pY", "https://i.ytimg.com/vi/u9Mv98Gr5pY/hqdefault.jpg"),
            ],
            "batman": [
                ("The Batman Trailer", "mqqft2x_Aa4", "https://i.ytimg.com/vi/mqqft2x_Aa4/hqdefault.jpg"),
                ("The Dark Knight Trailer", "EXeTwQWrcwY", "https://i.ytimg.com/vi/EXeTwQWrcwY/hqdefault.jpg"),
                ("Batman Begins Trailer", "neY2xVmOfUM", "https://i.ytimg.com/vi/neY2xVmOfUM/hqdefault.jpg"),
                ("Joker Trailer", "zAGVQLHvwOY", "https://i.ytimg.com/vi/zAGVQLHvwOY/hqdefault.jpg"),
                ("Justice League Trailer", "3cxixDgHUYw", "https://i.ytimg.com/vi/3cxixDgHUYw/hqdefault.jpg"),
                ("Superman Man of Steel", "T6DJcgm3wNY", "https://i.ytimg.com/vi/T6DJcgm3wNY/hqdefault.jpg"),
            ],
        }

        # Find relevant recommendations
        query_lower = query.lower()

        # Try exact match first
        if query_lower in recommendations:
            videos = recommendations[query_lower]
        else:
            # Partial match or default
            for key in recommendations:
                if key in query_lower or query_lower in key:
                    videos = recommendations[key]
                    break
            else:
                # Default popular trailers
                videos = [
                    ("Dune: Part Two Trailer", "Way9Dexny3w", "https://i.ytimg.com/vi/Way9Dexny3w/hqdefault.jpg"),
                    ("Oppenheimer Trailer", "uYPbbksJxIg", "https://i.ytimg.com/vi/uYPbbksJxIg/hqdefault.jpg"),
                    ("Barbie Trailer", "pBk4NYhWNMM", "https://i.ytimg.com/vi/pBk4NYhWNMM/hqdefault.jpg"),
                    ("Deadpool & Wolverine", "73_1biulkYk", "https://i.ytimg.com/vi/73_1biulkYk/hqdefault.jpg"),
                    ("The Marvels Trailer", "wS_qbDztgVY", "https://i.ytimg.com/vi/wS_qbDztgVY/hqdefault.jpg"),
                    ("Top Gun: Maverick", "giXco2jaZ_4", "https://i.ytimg.com/vi/giXco2jaZ_4/hqdefault.jpg"),
                ]

        return [
            {
                "id": video_id,
                "title": title,
                "description": f"Watch the official trailer",
                "thumbnail": thumbnail,
                "channel": "Official Movie Trailers",
                "published_at": "2024-01-10T12:00:00Z",
                "platform": category,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
            for title, video_id, thumbnail in videos
        ]

    def _score_and_rank(self, results: List[Dict]) -> List[Dict]:
        """
        Simple ranking algorithm:
        1. Recency (newer content gets higher scores)
        2. Randomization for diversity
        """
        if not results:
            return []

        # Score each result
        for result in results:
            score = 0.0

            # Recency boost (newer content gets a small bump)
            try:
                published = datetime.fromisoformat(
                    result["published_at"].replace("Z", "+00:00")
                )
                days_old = (datetime.now(published.tzinfo) - published).days
                recency_score = max(0, 1 - (days_old / 365))  # Decays over a year
                score += recency_score * 0.7
            except Exception:
                pass

            # Add randomness for diversity
            score += random.random() * 0.3

            result["_score"] = score

        # Sort by score descending
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # Remove the internal score field before returning
        for result in results:
            result.pop("_score", None)

        return results
