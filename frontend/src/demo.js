// Demo mode: serves the same bundled sample data as the backend
// (backend/app/sample_data.json) so the UI works with zero API keys
// and no running server. Every entry is a real public YouTube video.
import SAMPLE_DATA from '../../backend/app/sample_data.json'

const toResult = (entry, platform, description) => ({
  id: entry.id,
  title: entry.title,
  description,
  thumbnail: `https://i.ytimg.com/vi/${entry.id}/hqdefault.jpg`,
  channel: entry.channel,
  published_at: '2024-01-15T12:00:00Z',
  platform,
  url: `https://www.youtube.com/watch?v=${entry.id}`,
  sample: true,
})

export function getDemoRecommendations({ category, searchQuery }) {
  const query = (searchQuery || '').trim().toLowerCase()
  if (category === 'youtube') {
    return SAMPLE_DATA.youtube.map((e) => toResult(e, 'youtube', `Sample result for "${searchQuery}" (demo mode)`))
  }
  if (category === 'tiktok') {
    return SAMPLE_DATA.shorts.map((e) => toResult(e, 'tiktok', `Sample result for "${searchQuery}" (demo mode)`))
  }
  const groups = category === 'movies' ? SAMPLE_DATA.movies : SAMPLE_DATA.tv
  let videos = groups[query]
  if (!videos) {
    const key = Object.keys(groups).find((k) => k !== 'default' && (query.includes(k) || k.includes(query)))
    videos = key ? groups[key] : groups.default
  }
  return videos.map((e) => toResult(e, 'youtube', 'Official trailer on YouTube (demo sample data)'))
}
