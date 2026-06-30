const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const DB_PATH = path.join(__dirname, 'data', 'ballclub.db');
const db = new sqlite3.Database(DB_PATH);

db.serialize(() => {
  // users
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'admin',
    created_at DATETIME DEFAULT (datetime('now'))
  )`);

  // games
  db.run(`CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    date TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT (datetime('now'))
  )`);

  // game_players snapshot
  db.run(`CREATE TABLE IF NOT EXISTS game_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    player_id INTEGER,
    position INTEGER,
    paid_override INTEGER,
    created_at DATETIME DEFAULT (datetime('now'))
  )`);

  // payments/audit logs
  db.run(`CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT,
    details TEXT,
    timestamp DATETIME DEFAULT (datetime('now'))
  )`);

  console.log('Migrations complete');
  db.close();
});
