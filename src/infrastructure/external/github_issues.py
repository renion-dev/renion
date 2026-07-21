import asyncio
import aiohttp
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def fetch_issues(repo: str, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Отримує Issues з публічного репозиторію GitHub.
    repo: "owner/repo" (наприклад, "microsoft/vscode")
    limit: кількість Issues (максимум 100)
    Повертає список Issue з полями: title, body, comments, reactions, labels, html_url, created_at.
    """
    url = f"https://api.github.com/repos/{repo}/issues"
    params = {
        "state": "open",
        "sort": "comments",
        "direction": "desc",
        "per_page": min(limit, 100)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    issues = []
                    for issue in data:
                        # Пропускаємо Pull Requests (вони теж приходять в Issues)
                        if "pull_request" in issue:
                            continue
                        issues.append({
                            "title": issue.get("title", "No title"),
                            "body": issue.get("body", ""),
                            "comments": issue.get("comments", 0),
                            "reactions": issue.get("reactions", {}).get("total_count", 0),
                            "labels": [label["name"] for label in issue.get("labels", [])],
                            "html_url": issue.get("html_url", ""),
                            "created_at": issue.get("created_at", ""),
                            "source": f"github:{repo}",
                            "type": "github_issue"
                        })
                    logger.info(f"✅ Fetched {len(issues)} issues from {repo}")
                    return issues
                elif resp.status == 403:
                    logger.warning(f"⚠️ Rate limit exceeded for GitHub API (repo: {repo})")
                    return []
                else:
                    logger.error(f"❌ GitHub API error {resp.status} for {repo}")
                    return []
    except Exception as e:
        logger.error(f"❌ Error fetching issues from {repo}: {e}")
        return []
