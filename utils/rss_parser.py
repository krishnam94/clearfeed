import feedparser

def parse_rss(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        # Robust timestamp extraction
        pub_fields = [
            ('published_parsed', entry.get('published_parsed')),
            ('updated_parsed', entry.get('updated_parsed')),
            ('issued_parsed', entry.get('issued_parsed')),
            ('created_parsed', entry.get('created_parsed')),
            ('published', entry.get('published')),
            ('updated', entry.get('updated')),
            ('pubDate', entry.get('pubDate')),
            ('date', entry.get('date')),
            ('issued', entry.get('issued')),
            ('created', entry.get('created')),
        ]
        pub_val = ''
        pub_raw = {}
        import time, datetime
        for k, v in pub_fields:
            if v:
                pub_raw[k] = v
                if isinstance(v, (tuple, time.struct_time)):
                    try:
                        pub_val = datetime.datetime(*v[:6], tzinfo=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
                        break
                    except Exception:
                        continue
                elif isinstance(v, str) and v.strip():
                    pub_val = v.strip()
                    break
        articles.append({
            'title': entry.get('title', ''),
            'link': entry.get('link', ''),
            'summary': entry.get('summary', ''),
            'published': pub_val,
            'published_raw': pub_raw
        })
    return articles
