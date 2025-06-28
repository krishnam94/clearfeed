-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT
);

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    url TEXT UNIQUE,
    category TEXT,
    trust_score REAL,
    user_added BOOLEAN DEFAULT 0
);

-- User sources (many-to-many)
CREATE TABLE IF NOT EXISTS user_sources (
    user_id INTEGER,
    source_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    title TEXT,
    url TEXT,
    image_url TEXT,
    published_at TEXT,
    raw_text TEXT,
    summary TEXT,
    language TEXT,
    tags TEXT,
    FOREIGN KEY(source_id) REFERENCES sources(id)
);
