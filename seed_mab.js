const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

const MAB_LOG = process.env.MAB_LOG || path.join(process.env.HOME || '.', '.claude', 'projects', '-home-marzomir-Documents-Mab-log', 'd65672a6-53a0-4ec4-81b8-c7572faa0c7c.jsonl');
const DB_PATH = path.join(__dirname, 'data', 'ballclub.db');

if (!fs.existsSync(MAB_LOG)) {
  console.error('Mab log not found at', MAB_LOG);
  process.exit(1);
}

const raw = fs.readFileSync(MAB_LOG, 'utf8');
const lines = raw.split('\n').filter(Boolean);

// Extract "text" fields recursively from parsed JSON objects
function collectTexts(obj, out) {
  if (!obj) return;
  if (typeof obj === 'string') return out.push(obj);
  if (Array.isArray(obj)) return obj.forEach(i => collectTexts(i, out));
  if (typeof obj === 'object') {
    for (const k of Object.keys(obj)) {
      if (k === 'text' && typeof obj[k] === 'string') out.push(obj[k]);
      else collectTexts(obj[k], out);
    }
  }
}

const texts = [];
for (const line of lines) {
  try {
    const obj = JSON.parse(line);
    collectTexts(obj, texts);
  } catch (e) {
    // ignore parse errors
  }
}

// Find numbers in texts
const nums = new Set();
for (const t of texts) {
  const m = t.match(/\b(\d{1,4})\b/g);
  if (m) m.forEach(x => nums.add(Number(x)));
}

const db = new sqlite3.Database(DB_PATH);

db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE,
    name TEXT,
    paid INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
  )`);

  const insert = db.prepare('INSERT OR IGNORE INTO players (number, name, paid) VALUES (?, ?, ?)');

  if (nums.size === 0) {
    console.log('No numeric player IDs found in Mab log — inserting sample players 1..5');
    for (let i = 1; i <= 5; i++) insert.run(i, `Player ${i}`, 0);
  } else {
    console.log('Seeding players from Mab log numbers:', Array.from(nums).slice(0,50));
    for (const n of nums) insert.run(n, `Player ${n}`, 0);
  }

  insert.finalize(() => {
    console.log('Seeding complete.');
    db.close();
  });
});
