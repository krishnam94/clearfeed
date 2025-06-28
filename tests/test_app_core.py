import os
import sqlite3
import tempfile
import pytest
from agents.source_scout import scout_and_vet_sources
from agents.article_fetcher import fetch_articles

DB_SCHEMA = os.path.join(os.path.dirname(__file__), '../db/schema.sql')

# --- Helpers ---
def create_temp_db():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    conn = sqlite3.connect(tmp.name)
    with open(DB_SCHEMA, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    return tmp.name, conn

def insert_source(conn, name="Test Source", url="http://test.com/rss", category="Test", trust_score=5.0):
    cur = conn.cursor()
    cur.execute('INSERT INTO sources (name, url, category, trust_score, user_added) VALUES (?, ?, ?, ?, 1)',
                (name, url, category, trust_score))
    conn.commit()
    return cur.lastrowid

# --- Tests ---
def test_db_source_loading():
    db_path, conn = create_temp_db()
    source_id = insert_source(conn)
    cur = conn.cursor()
    cur.execute('SELECT name, url, category, trust_score FROM sources')
    sources = cur.fetchall()
    assert len(sources) == 1
    assert sources[0][0] == "Test Source"
    conn.close()
    os.unlink(db_path)

def test_scout_and_save_source():
    # This test will skip if no SERPAPI_KEY is set
    import os
    if not os.environ.get('SERPAPI_KEY'):
        pytest.skip("SERPAPI_KEY not set")
    sources = scout_and_vet_sources("Technology")
    assert isinstance(sources, list)
    assert len(sources) > 0
    assert 'name' in sources[0]
    assert 'url' in sources[0]

def test_fetch_articles_from_source():
    # Uses a known RSS feed for testing
    sources = [{
        'name': 'Reuters Technology',
        'url': 'http://feeds.reuters.com/reuters/technologyNews',
        'category': 'Technology',
        'trust_score': 7.0
    }]
    articles = fetch_articles(sources, max_articles=2)
    assert isinstance(articles, list)
    assert len(articles) <= 2
    if articles:
        assert 'title' in articles[0]
        assert 'url' in articles[0]
        assert 'raw_text' in articles[0]

def test_article_save_and_load():
    db_path, conn = create_temp_db()
    source_id = insert_source(conn)
    cur = conn.cursor()
    cur.execute('''INSERT INTO articles (source_id, title, url, published_at, raw_text, summary, language, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (source_id, 'Test Article', 'http://test.com/article', '2025-01-01', 'Raw text', 'Summary', 'English', 'Test'))
    conn.commit()
    cur.execute('''SELECT title, url, summary FROM articles WHERE source_id = ?''', (source_id,))
    articles = cur.fetchall()
    assert len(articles) == 1
    assert articles[0][0] == 'Test Article'
    conn.close()
    os.unlink(db_path)

# To run: pytest tests/test_app_core.py
