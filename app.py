import streamlit as st
import os
import json
import sqlite3
from agents.source_scout import scout_and_vet_sources
from agents.article_fetcher import fetch_articles
from agents.summarizer import summarize_article
from agents.translator import translate_summary

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'clearfeed.db')
SOURCES_JSON = os.path.join(os.path.dirname(__file__), 'data', 'sources.json')

# Ensure DB exists
if not os.path.exists(DB_PATH):
    from db import schema
    schema.init_db(DB_PATH)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_all_sources():
    with open(SOURCES_JSON, 'r') as f:
        json_sources = json.load(f)
    db_sources = load_sources(DB_PATH)
    # Merge sources (simple union by URL)
    all_sources = {s['url']: s for s in json_sources}
    for s in db_sources:
        all_sources[s['url']] = s
    return list(all_sources.values())

st.set_page_config(page_title='Clearfeed', layout='wide')
st.title('📰 Clearfeed: Curated news for what you care about')

# --- Page selector ---
page = st.sidebar.radio('Navigate', ['Source Scout', 'News Feed', 'Manage Sources'])

import datetime

def normalize_timestamp(ts):
    if not ts:
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    try:
        # Try parsing common formats
        dt = None
        for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):  # RSS, ISO, fallback
            try:
                dt = datetime.datetime.strptime(ts, fmt)
                break
            except Exception:
                continue
        if dt is None:
            # Try fromisoformat (Python 3.7+)
            try:
                dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except Exception:
                pass
        if dt is None:
            return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
        return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    except Exception:
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

if page == 'Manage Sources':
    st.header('Manage News Sources')
    if st.button('Reset Feed (Delete All Articles)', type='primary'):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM articles')
        conn.commit()
        conn.close()
        st.success('All articles have been deleted from your feed.')
        st.rerun()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, url, category, trust_score FROM sources ORDER BY name')
    sources = cur.fetchall()
    conn.close()
    if not sources:
        st.info('No sources in your database.')
    else:
        for src in sources:
            col1, col2, col3, col4, col5, col6 = st.columns([2,3,4,2,2,2])
            col1.write(src['name'])
            col2.write(src['category'])
            col3.write(src['url'])
            col4.write(f"Trust: {src['trust_score']}")
            if col5.button('Remove', key=f"remove_{src['id']}"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('DELETE FROM sources WHERE id = ?', (src['id'],))
                conn.commit()
                conn.close()
                st.success(f"Source '{src['name']}' removed.")
                st.rerun()
    st.markdown('---')

elif page == 'Source Scout':

    # --- Scouting new sources ---
    grouped_topics = {
        'Sports': ['Football', 'Cricket', 'Tennis', 'Basketball', 'Baseball', 'Formula 1', 'Olympics', 'Golf', 'Hockey'],
        'Health': [
            'Diabetes', 'Cancer', 'Mental Health', 'Heart Disease', 'COVID-19', 'Nutrition', 'Fitness', 'Obesity', "Alzheimer's",
            'Malaria', 'HIV/AIDS', 'Tuberculosis', 'Dengue', 'Zika', 'Ebola', 'Polio', 'Measles', 'Influenza', 'Asthma', 'Arthritis', 'Epilepsy', 'Autism', 'Parkinson\'s', 'Multiple Sclerosis', 'Lupus', 'Cystic Fibrosis', 'Rare Diseases'
        ],
        'Technology': ['Artificial Intelligence', 'Cybersecurity', 'Gadgets', 'Software Development', 'Space', 'Blockchain', 'Startups'],
        'Science': ['Astronomy', 'Physics', 'Biology', 'Climate Change', 'Genetics', 'Chemistry'],
        'World': ['Asia', 'Europe', 'Americas', 'Africa', 'Middle East', 'Oceania'],
        'Business': ['Stock Market', 'Startups', 'Economy', 'Personal Finance', 'Real Estate', 'Cryptocurrency'],
        'Education': ['EdTech', 'Higher Education', 'K-12', 'Online Learning'],
        'Politics': ['Elections', 'Policy', 'International Relations', 'Government'],
        'Entertainment': ['Movies', 'Music', 'Television', 'Celebrities', 'Gaming'],
        'Climate': ['Global Warming', 'Renewable Energy', 'Wildlife', 'Pollution']
    }
    # Flat list of all subtopics
    all_subtopics = [sub for subs in grouped_topics.values() for sub in subs]
    # Map subtopic to group for backend
    topic_to_group = {}
    for group, subtopics in grouped_topics.items():
        for sub in subtopics:
            topic_to_group[sub] = group
    import json
    SELECTED_TOPICS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'selected_topics.json')
    # Load previously selected topics if available
    if os.path.exists(SELECTED_TOPICS_PATH):
        try:
            with open(SELECTED_TOPICS_PATH, 'r') as f:
                default_selected_topics = json.load(f)
        except Exception:
            default_selected_topics = []
    else:
        default_selected_topics = []
    selected_topics = st.multiselect('Search and select topics of interest:', all_subtopics, default=default_selected_topics, key='topic_multiselect')
    # Persist selected topics on change
    if set(selected_topics) != set(default_selected_topics):
        try:
            with open(SELECTED_TOPICS_PATH, 'w') as f:
                json.dump(selected_topics, f)
        except Exception as e:
            st.warning(f'Could not persist selected topics: {e}')
    if selected_topics:
        st.markdown('**Currently selected topics:** ' + ', '.join(f'`{t}`' for t in selected_topics))
    else:
        st.warning('Please select at least one topic to scout news sources.')
    if 'vetted_sources' not in st.session_state:
        st.session_state['vetted_sources'] = []
    if st.button('Scout and Vet News Sources'):
        all_sources = []
        seen_urls = set()
        # Map subtopic to group
        topic_to_group = {}
        for group, subtopics in grouped_topics.items():
            for sub in subtopics:
                topic_to_group[sub] = group
        for topic in selected_topics:
            group = topic_to_group.get(topic)
            print(f"[DEBUG] User selected topic: {topic} (group: {group})")
            with st.spinner(f'Scouting news sources for "{topic}"...'):
                sources = scout_and_vet_sources(topic, group)
            print(f"[DEBUG] Sources found for {topic}: {sources}")
            for src in sources:
                if src['url'] not in seen_urls:
                    all_sources.append(src)
                    seen_urls.add(src['url'])
        if not all_sources:
            st.warning('No sources found for these topics. Try others.')
        else:
            st.session_state['vetted_sources'] = all_sources
            st.info(f"Found {len(all_sources)} unique, vetted sources for selected topics. Select which to use.")
    if st.session_state['vetted_sources']:
        sources = st.session_state['vetted_sources']
        st.info(f"Found {len(sources)} unique, vetted sources. Select which to use.")
        if st.button('Show Vetted Sources Table', key='show_vetted_sources_table_btn'):
            st.dataframe(sources)
        if st.button('Save Vetted Sources to Database', key='save_vetted_sources_btn'):
            conn = get_db_connection()
            cur = conn.cursor()
            added = 0
            for src in sources:
                try:
                    cur.execute('INSERT OR IGNORE INTO sources (name, url, category, trust_score, user_added) VALUES (?, ?, ?, ?, ?)',
                        (src['name'], src['url'], src['category'], src['trust_score'], 1))
                    added += cur.rowcount
                except Exception as e:
                    st.warning(f"Could not save source {src['name']}: {e}")
            conn.commit()
            conn.close()
            st.success(f"Saved {added} new sources to the database.")
    st.markdown('---')
    st.markdown('#### Or fetch news from your saved sources below:')

    # --- Load sources from database ---
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name, url, category, trust_score FROM sources ORDER BY name')
    db_sources = [dict(row) for row in cur.fetchall()]
    conn.close()

    if db_sources:
        if selected_topics:
            st.markdown(f"**Topics currently selected:** {' | '.join(selected_topics)}")
        st.info(f"{len(db_sources)} sources found in your database. Select which to use.")
        source_names = [s['name'] for s in db_sources]
        selected_sources = st.multiselect('Select news sources to fetch from:', source_names, default=source_names, key='db_source_multiselect')
        print(f"[DEBUG] User selected sources from DB: {selected_sources}")
        if not selected_sources:
            st.warning('Please select at least one news source to continue.')
        if st.button('Fetch & Summarize News from DB Sources', key='fetch_summarize_news_db_btn'):
            chosen = [s for s in db_sources if s['name'] in selected_sources]
            print(f"[DEBUG] Fetching articles from DB sources: {chosen}")
            st.info('Fetching articles...')
            MAX_ARTICLES = 20
            articles = fetch_articles(chosen, max_articles=MAX_ARTICLES)
            print(f"[DEBUG] Articles fetched: {articles}")
            if not articles:
                st.warning('No articles could be fetched from the selected sources.')
            else:
                st.info('Summarizing articles...')
                for art in articles:
                    print(f"[DEBUG] Summarizing article: {art.get('title')}")
                    summary = summarize_article(art['raw_text'])
                    image_url = art.get('image_url') or 'https://placehold.co/120x80?text=No+Image'
                    col_img, col_txt = st.columns([1,4])
                    with col_img:
                        st.image(image_url, width=120)
                    with col_txt:
                        st.markdown(f"### [{art['title']}]({art['url']})\n**Source:** {art['source_name']}\n\n{summary}")
                    # Save to DB immediately
                    try:
                        print(f"[DB] Attempting to save article: {art.get('title')} from source: {art.get('source_name')}")
                        conn = get_db_connection()
                        cur = conn.cursor()
                        print(f"[DB] Looking up source_id for source: {art.get('source_name')}")
                        cur.execute('SELECT id FROM sources WHERE name = ? LIMIT 1', (art.get('source_name'),))
                        source_row = cur.fetchone()
                        source_id = source_row['id'] if source_row else None
                        print(f"[DB] Found source_id: {source_id}")
                        if source_id:
                            print(f"[DB] Inserting article into DB: {art.get('title')} ({art.get('url')})")
                            cur.execute('''
                                INSERT INTO articles (source_id, title, url, image_url, published_at, raw_text, summary, language, tags)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (source_id, art['title'], art['url'], art.get('image_url', ''), normalize_timestamp(art.get('published')), art['raw_text'], summary, 'en', ','.join(art.get('tags', []))))
                            conn.commit()
                            print(f"[DB] Article saved (or duplicate ignored): {art.get('title')} ({art.get('url')})")
                        else:
                            print(f"[DB] Source not found for article: {art.get('title')} (source: {art.get('source_name')})")
                        conn.close()
                    except Exception as e:
                        print(f"[DB ERROR] Could not save article '{art.get('title')}': {e}")

elif page == 'News Feed':
    st.header('📰 My Saved News Feed')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT a.title, a.url, a.image_url, a.summary, a.published_at, s.name as source_name
        FROM articles a
        JOIN sources s ON a.source_id = s.id
        ORDER BY a.published_at DESC, a.id DESC
        LIMIT 50
    ''')
    rows = cur.fetchall()
    conn.close()
    if not rows:
        st.info('No news articles saved yet. Fetch and summarize some news first!')
    else:
        for row in rows:
            image_url = row['image_url'] or 'https://placehold.co/120x80?text=No+Image'
            col_img, col_txt = st.columns([1,4])
            with col_img:
                st.image(image_url, width=120)
            with col_txt:
                st.markdown(f"### [{row['title']}]({row['url']})")
                st.write(f"**Source:** {row['source_name']}  ")
                st.write(f"**Published:** {row['published_at'] or 'N/A'}  ")
                st.write(row['summary'] or '[No summary available]')
            st.markdown('---')
