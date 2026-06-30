const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

// ---------- Schemas ----------
const memberSchema = new mongoose.Schema({
  name: { type: String, required: true },
  phone: { type: String, default: '' },
  dateJoined: { type: Date, default: Date.now }
});
const Member = mongoose.model('Member', memberSchema);

const pendingSchema = new mongoose.Schema({
  name: { type: String, required: true },
  phone: { type: String, default: '' },
  requestedAt: { type: Date, default: Date.now }
});

const playerSchema = new mongoose.Schema({
  queueNumber: { type: Number, required: true },
  name: { type: String, required: true },
  phone: { type: String, default: '' },
  paid: { type: Boolean, default: false },
  addedAt: { type: Date, default: Date.now }
});

const sessionSchema = new mongoose.Schema({
  date: { type: Date, default: Date.now },
  status: { type: String, enum: ['open', 'closed'], default: 'open' },
  shareCode: { type: String, required: true, unique: true },
  queue: [playerSchema],
  pending: [pendingSchema]
});
const Session = mongoose.model('Session', sessionSchema);

// ---------- Helpers ----------
function generateShareCode() {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

function requireAuth(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  try {
    jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// ---------- Auth ----------
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  if (username !== process.env.OWNER_USERNAME || password !== process.env.OWNER_PASSWORD) {
    return res.status(401).json({ error: 'Incorrect username or password' });
  }
  const token = jwt.sign({ role: 'owner' }, process.env.JWT_SECRET, { expiresIn: '7d' });
  res.json({ token });
});

// ---------- Sessions (owner only) ----------
app.get('/api/sessions', requireAuth, async (req, res) => {
  const sessions = await Session.find().sort({ date: -1 });
  res.json(sessions);
});

app.post('/api/sessions', requireAuth, async (req, res) => {
  let open = await Session.findOne({ status: 'open' });
  if (open) return res.json(open);
  const session = new Session({ shareCode: generateShareCode(), queue: [], pending: [] });
  await session.save();
  res.status(201).json(session);
});

app.get('/api/sessions/:id', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  res.json(session);
});

app.post('/api/sessions/:id/walkin', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  if (session.status === 'closed') return res.status(400).json({ error: 'Session is closed' });

  const nextNumber = session.queue.length > 0
    ? Math.max(...session.queue.map(p => p.queueNumber)) + 1
    : 1;
  session.queue.push({ queueNumber: nextNumber, name: req.body.name, paid: false });
  await session.save();
  res.status(201).json(session);
});

app.patch('/api/sessions/:id/players/:playerId', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  const player = session.queue.id(req.params.playerId);
  if (!player) return res.status(404).json({ error: 'Player not found' });
  player.paid = !player.paid;
  await session.save();
  res.json(session);
});

app.patch('/api/sessions/:id/close', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  session.status = 'closed';
  await session.save();
  res.json(session);
});

// Approve / decline pending join requests
app.post('/api/sessions/:id/pending/:requestId/approve', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  const request = session.pending.id(req.params.requestId);
  if (!request) return res.status(404).json({ error: 'Request not found' });

  const nextNumber = session.queue.length > 0
    ? Math.max(...session.queue.map(p => p.queueNumber)) + 1
    : 1;
  session.queue.push({ queueNumber: nextNumber, name: request.name, phone: request.phone, paid: false });

  const phone = request.phone;
  const name = request.name;
  request.deleteOne();
  await session.save();

  if (phone) {
    const existingMember = await Member.findOne({ phone });
    if (!existingMember) {
      await new Member({ name, phone }).save();
    }
  }

  res.json(session);
});

app.post('/api/sessions/:id/pending/:requestId/decline', requireAuth, async (req, res) => {
  const session = await Session.findById(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  const request = session.pending.id(req.params.requestId);
  if (!request) return res.status(404).json({ error: 'Request not found' });
  request.deleteOne();
  await session.save();
  res.json(session);
});

// ---------- Members (owner only) ----------
app.get('/api/members', requireAuth, async (req, res) => {
  const members = await Member.find().sort({ name: 1 });
  res.json(members);
});

app.post('/api/members', requireAuth, async (req, res) => {
  const member = new Member({ name: req.body.name, phone: req.body.phone || '' });
  await member.save();
  res.status(201).json(member);
});

// ---------- Public join flow (no auth) ----------
app.get('/api/public/session/:shareCode', async (req, res) => {
  const session = await Session.findOne({ shareCode: req.params.shareCode });
  if (!session) return res.status(404).json({ error: 'Link not found or expired' });
  res.json({ date: session.date, status: session.status });
});

app.get('/api/public/lookup', async (req, res) => {
  const phone = req.query.phone;
  if (!phone) return res.json({ found: false });
  const member = await Member.findOne({ phone });
  res.json(member ? { found: true, name: member.name } : { found: false });
});

app.post('/api/public/session/:shareCode/join', async (req, res) => {
  const session = await Session.findOne({ shareCode: req.params.shareCode });
  if (!session) return res.status(404).json({ error: 'Link not found or expired' });
  if (session.status === 'closed') return res.status(400).json({ error: 'This session is closed' });

  const { name, phone } = req.body;
  if (!name || !phone) return res.status(400).json({ error: 'Name and phone are required' });

  session.pending.push({ name, phone });
  await session.save();
  res.status(201).json({ message: 'Request sent. Wait for the owner to approve you.' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));