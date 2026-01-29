# sentiment.py
import feedparser
import re
from datetime import datetime

# 关键词词库 (可根据需要扩展)
BULLISH_WORDS = {'bullish', 'moon', 'pump', 'buy', 'rally', 'surge', 'gain', 'green', 'breakout', 'uptrend', 'hodl', 'lambo', 'diamond hands'}
BEARISH_WORDS = {'bearish', 'dump', 'crash', 'sell', 'red', 'drop', 'fear', 'panic', 'bear', 'downtrend', 'rekt', 'paper hands'}

def fetch_reddit_sentiment(subreddit='cryptocurrency', limit=10):
    """
    抓取 Reddit 指定 subreddit 的热门帖子标题并分析情绪
    """
    url = f'https://www.reddit.com/r/{subreddit}/hot/.rss?limit={limit}'
    headers = {'User-Agent': 'CryptoMateProBot/1.0 by Ryan'} 
    try:
        feed = feedparser.parse(url, request_headers=headers)
        if feed.bozo: # bozo_exception indicates a parsing error
             return {'error': f"Feed parsing error: {feed.bozo_exception}"}
    except Exception as e:
        return {'error': str(e)}

    total_score = 0
    analyzed_posts = []

    for entry in feed.entries:
        title = entry.title.lower()
        words = re.findall(r'\b\w+\b', title) # 提取单词
        bullish_count = sum(1 for w in words if w in BULLISH_WORDS)
        bearish_count = sum(1 for w in words if w in BEARISH_WORDS)
        post_score = bullish_count - bearish_count
        total_score += post_score
        analyzed_posts.append({'title': entry.title, 'score': post_score})

    num_posts = len(analyzed_posts)
    if num_posts == 0:
        return {'score': 0, 'total_posts': 0, 'classification': 'neutral', 'posts': [], 'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

    avg_score = total_score / num_posts

    if avg_score > 0.3:
        classification = 'bullish'
    elif avg_score < -0.3:
        classification = 'bearish'
    else:
        classification = 'neutral'

    return {
        'score': round(avg_score, 3),
        'total_posts': num_posts,
        'classification': classification,
        'posts': analyzed_posts,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    }
