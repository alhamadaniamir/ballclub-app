const express = require('express');
const session = require('express-session');
const SQLiteStore = require('connect-sqlite3')(session);
const cors = require('cors');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');

const DB_PATH = path.join(__dirname, 'data', 'ballclub.db');
const db = new sqlite3.Database(DB_PATH);

// ensure players table exists
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE,
    name TEXT,
    paid INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
  )`);
});

const app = express();
app.use(cors());
app.use(express.json());
app.use(session({
  store: new SQLiteStore({ db: 'sessions.sqlite', dir: './data' }),
  secret: process.env.SESSION_SECRET || 'change_this_secret',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000, sameSite: 'lax' }
}));
app.use(express.static(path.join(__dirname, 'public')));

// simple auth helpers
function requireAuth(req, res, next) {
  if (req.session && req.session.userId) return next();
  return res.status(401).json({ error: 'unauthorized' });
}

// List players (first-come, first-serve)
app.get('/api/players', (req, res) => {
  db.all('SELECT * FROM players ORDER BY created_at ASC, id ASC', (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Add player (always append to the end of the queue; ignore client-supplied number)
app.post('/api/players', (req, res) => {
  const { name, paid } = req.body || {};

  // find current max number and assign next
  db.get('SELECT MAX(number) as maxn FROM players', (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    const next = (row && row.maxn) ? (row.maxn + 1) : 1;
    const stmt = db.prepare('INSERT INTO players (number, name, paid) VALUES (?, ?, ?)');
    stmt.run(next, name || `Player ${next}`, paid ? 1 : 0, function (e) {
      if (e) return res.status(400).json({ error: e.message });
      db.get('SELECT * FROM players WHERE id = ?', [this.lastID], (ex, row2) => {
        if (ex) return res.status(500).json({ error: ex.message });
        res.status(201).json(row2);
      });
    });
  });
});

// Toggle/mark paid
app.put('/api/players/:id/pay', (req, res) => {
  const id = req.params.id;
  const { paid } = req.body; // optional, if omitted toggle
  db.get('SELECT paid FROM players WHERE id = ?', [id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Player not found' });
    const newPaid = typeof paid === 'number' ? (paid ? 1 : 0) : (row.paid ? 0 : 1);
    db.run('UPDATE players SET paid = ? WHERE id = ?', [newPaid, id], function (e) {
      if (e) return res.status(500).json({ error: e.message });
      db.get('SELECT * FROM players WHERE id = ?', [id], (ex, updated) => {
        if (ex) return res.status(500).json({ error: ex.message });
        res.json(updated);
      });
    });
  });
});

// Auth routes
app.post('/api/login', (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) return res.status(400).json({ error: 'username and password required' });
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!user) return res.status(401).json({ error: 'invalid' });
    bcrypt.compare(password, user.password_hash, (e, ok) => {
      if (e) return res.status(500).json({ error: e.message });
      if (!ok) return res.status(401).json({ error: 'invalid' });
      req.session.userId = user.id;
      req.session.username = user.username;
      res.json({ ok: true });
    });
  });
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

// Protected: create game snapshot from current queue
app.post('/api/games', requireAuth, (req, res) => {
  const { title, date, notes } = req.body || {};
  db.run('INSERT INTO games (title, date, notes) VALUES (?, ?, ?)', [title || 'Game', date || new Date().toISOString(), notes || ''], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    const gameId = this.lastID;
    // snapshot current queue
    db.all('SELECT id as player_id, number, name FROM players ORDER BY created_at ASC, id ASC', (err2, rows) => {
      if (err2) return res.status(500).json({ error: err2.message });
      const insert = db.prepare('INSERT INTO game_players (game_id, player_id, position, paid_override) VALUES (?, ?, ?, ?)');
      rows.forEach((r, idx) => insert.run(gameId, r.player_id || null, idx + 1, 0));
      insert.finalize(() => {
        res.status(201).json({ gameId, players: rows.length });
      });
    });
  });
});

// Who am I (session check)
app.get('/api/whoami', (req, res) => {
  if (req.session && req.session.userId) {
    db.get('SELECT id, username, role FROM users WHERE id = ?', [req.session.userId], (err, user) => {
      if (err) return res.status(500).json({ error: err.message });
      if (!user) return res.status(404).json({ error: 'user not found' });
      res.json({ user });
    });
  } else {
    res.status(200).json({ user: null });
  }
});

// List games (history)
app.get('/api/games', requireAuth, (req, res) => {
  db.all('SELECT * FROM games ORDER BY date DESC, id DESC', (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

// Get game detail and its players (snapshot)
app.get('/api/games/:id', requireAuth, (req, res) => {
  const gameId = req.params.id;
  db.get('SELECT * FROM games WHERE id = ?', [gameId], (err, game) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!game) return res.status(404).json({ error: 'game not found' });
    const sql = `SELECT gp.position, gp.paid_override, p.id as player_id, p.number, p.name, p.paid as live_paid
                 FROM game_players gp
                 LEFT JOIN players p ON p.id = gp.player_id
                 WHERE gp.game_id = ?
                 ORDER BY gp.position ASC`;
    db.all(sql, [gameId], (e, rows) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json({ game, players: rows });
    });
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on http://localhost:${PORT}`));
