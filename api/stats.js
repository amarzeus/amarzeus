export default async function handler(req, res) {
  const stats = {
    totalCommits: Math.floor(Math.random() * 5000) + 2000,
    currentStreak: Math.floor(Math.random() * 100) + 30,
    totalStars: Math.floor(Math.random() * 500) + 100,
    followers: Math.floor(Math.random() * 1000) + 200,
    lastActive: new Date().toISOString(),
    codingHours: Math.floor(Math.random() * 2000) + 1000,
    currentProject: 'AI-Powered Development Tools',
    mood: ['🚀', '💻', '⚡', '🔥', '🌟'][Math.floor(Math.random() * 5)]
  };

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=300');
  res.json(stats);
}