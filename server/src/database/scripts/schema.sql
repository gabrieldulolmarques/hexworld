CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session (
    id TEXT PRIMARY KEY NOT NULL,
    user_id TEXT NOT NULL REFERENCES user (id),
    token TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS map (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    editor_code TEXT UNIQUE NOT NULL,
    viewer_code TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_map (
    user_id TEXT NOT NULL REFERENCES user (id),
    map_id TEXT NOT NULL REFERENCES map (id),
    role TEXT NOT NULL CHECK (
        role IN ('owner', 'editor', 'viewer')
    ) DEFAULT 'viewer',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, map_id)
);

CREATE TABLE IF NOT EXISTS tile (
    id TEXT PRIMARY KEY NOT NULL,
    map_id TEXT NOT NULL REFERENCES map (id),
    q INTEGER NOT NULL,
    r INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (map_id, q, r)
);

CREATE TABLE IF NOT EXISTS structure (
    tile_id TEXT PRIMARY KEY REFERENCES tile (id),
    type TEXT NOT NULL,
    author_id TEXT REFERENCES user (id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS road (
    id TEXT PRIMARY KEY NOT NULL,
    tile_id TEXT NOT NULL REFERENCES tile (id),
    color TEXT NOT NULL,
    author_id TEXT REFERENCES user (id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS description (
    tile_id TEXT PRIMARY KEY REFERENCES tile (id),
    text TEXT NOT NULL,
    author_id TEXT REFERENCES user (id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);