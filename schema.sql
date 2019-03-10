DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS queries;


CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE notes (
  note_id TEXT,
  user_id INTEGER NOT NULL,
  time_stamp TEXT,
  note TEXT,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE queries (
  query_id TEXT,
  user_id INTEGER NOT NULL,
  time_stamp TEXT,
  query TEXT,
  FOREIGN KEY (user_id) REFERENCES users (id)
);
