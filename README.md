# Clearfeed

A humane, AI-powered personalized news feed app built with Streamlit, Python, and SQLite.

## Features
- **Topic-first news discovery**: Select topics (e.g., sports, diseases, tech) and let Clearfeed scout the best news sources for you.
- **AI-powered source scouting**: Uses SerpApi and feed discovery to find and vet high-quality RSS feeds.
- **Article summarization**: Summarizes news using OpenAI GPT models.
- **Cover images**: Displays article thumbnails for a visually rich feed.
- **Source management**: Add, remove, and manage vetted news sources.
- **Persistent preferences**: Your topic selections are saved across sessions.

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/clearfeed.git
cd clearfeed
```

### 2. Set up your environment
```bash
python3 -m venv clearfeed-env
source clearfeed-env/bin/activate
pip install -r requirements.txt
```

### 3. Set environment variables
Create a `.env` file or export the following variables:
```
OPENAI_API_KEY=your-openai-api-key
SERPAPI_KEY=your-serpapi-key
```
**Do NOT commit your API keys to GitHub!**

### 4. Run the app
```bash
streamlit run app.py
```

## Project Structure
```
clearfeed/
├── app.py
├── agents/
│   ├── source_scout.py
│   ├── article_fetcher.py
│   ├── summarizer.py
│   └── translator.py
├── data/
│   └── sources.json
├── db/
│   ├── schema.sql
│   └── clearfeed.db (auto-created)
├── utils/
│   ├── rss_parser.py
│   └── logger.py
├── prompts/
│   └── summary_prompt.txt
├── requirements.txt
└── README.md
```

## Notes
- Requires OpenAI API key for summarization (set `OPENAI_API_KEY` env variable)
- SQLite DB auto-initializes on first run
- Add/remove sources and extend functionality as needed

## License
MIT
