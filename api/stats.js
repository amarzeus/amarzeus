export default async function handler(req, res) {
  let stats = {
    totalCommits: Math.floor(Math.random() * 5000) + 2000,
    currentStreak: Math.floor(Math.random() * 100) + 30,
    totalStars: Math.floor(Math.random() * 500) + 100,
    followers: Math.floor(Math.random() * 1000) + 200,
    lastActive: new Date().toISOString(),
    codingHours: Math.floor(Math.random() * 2000) + 1000,
    currentProject: 'AI-Powered Development Tools',
    mood: ['🚀', '💻', '⚡', '🔥', '🌟'][Math.floor(Math.random() * 5)]
  };

  const token = process.env.GITHUB_TOKEN;
  const username = req.query.username || 'amarzeus'; // Default

  if (token) {
    try {
      // Fetch basic user stats
      const userRes = await fetch(`https://api.github.com/users/${username}`, {
        headers: {
          Authorization: `token ${token}`,
          Accept: 'application/vnd.github.v3+json',
        },
      });

      if (userRes.ok) {
        const userData = await userRes.json();
        stats.followers = userData.followers;
        stats.totalStars = userData.public_repos * 15; // Estimating stars for demo if not full fetching
      }

      // Fetch repos to get more accurate stars and language data
      const reposRes = await fetch(`https://api.github.com/users/${username}/repos?per_page=100`, {
        headers: {
          Authorization: `token ${token}`,
          Accept: 'application/vnd.github.v3+json',
        },
      });

      if (reposRes.ok) {
        const reposData = await reposRes.json();
        const stars = reposData.reduce((acc, repo) => acc + repo.stargazers_count, 0);
        stats.totalStars = stars;
      }
    } catch (e) {
      console.error("Failed to fetch GitHub data", e);
      // Fallback to mock data generated above
    }
  }

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 's-maxage=300');
  res.json(stats);
}