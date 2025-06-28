import requests
from utils.rss_parser import parse_rss
from newspaper import Article

def fetch_articles(sources, max_articles=50):
    articles = []
    for src in sources:
        if len(articles) >= max_articles:
            return articles
        filter_topic = src.get('filter_topic')
        if 'rss' in src['url'].lower():
            feed_articles = parse_rss(src['url'])
            filtered = []
            if filter_topic:
                keyword = filter_topic.lower()
                for a in feed_articles:
                    title = a.get('title', '').lower()
                    summary = a.get('summary', '').lower()
                    tags = a.get('tags', '').lower() if 'tags' in a else ''
                    if keyword in title or keyword in summary or keyword in tags:
                        filtered.append(a)
            else:
                filtered = feed_articles
            per_source_count = 0
            for a in filtered:
                if len(articles) >= max_articles or per_source_count >= 5:
                    break
                art = {'title': a['title'], 'url': a['link'], 'source_name': src['name']}
                try:
                    article = Article(a['link'])
                    article.download()
                    article.parse()
                    art['raw_text'] = article.text
                    # Use newspaper3k's top_image as fallback if image_url not set
                    if not art.get('image_url'):
                        art['image_url'] = getattr(article, 'top_image', None)
                except Exception:
                    art['raw_text'] = a.get('summary', '')
                articles.append(art)
                per_source_count += 1
        else:
            # Direct URL (fallback)
            per_source_count = 0
            try:
                if len(articles) >= max_articles or per_source_count >= 5:
                    break
                article = Article(src['url'])
                article.download()
                article.parse()
                art = {'title': article.title, 'url': src['url'], 'raw_text': article.text, 'source_name': src['name']}
                if filter_topic:
                    # Only include if keyword appears in title or text
                    keyword = filter_topic.lower()
                    if keyword not in (article.title or '').lower() and keyword not in (article.text or '').lower():
                        continue
                articles.append(art)
                per_source_count += 1
            except Exception:
                continue
    return articles
