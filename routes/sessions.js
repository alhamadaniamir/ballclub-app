const express = require('express');
const Session = require('../models/Session');
const Member = require('../models/Member');
const { requireAuth } = require('../middleware/auth');
const { getNextQueueNumber, generateShareCode } = require('../utils/helpers');
const { validateInput } = require('../middleware/validation');
const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const sessions = await Session.find().sort({ date: -1 });
    res.json(sessions);
  } catch (err) {
    next(err);
  }
});

router.post('/', requireAuth, async (req, res, next) => {
  try {
    let open = await Session.findOne({ status: 'open' });
    if (open) return res.json(open);
    const sessionDoc = new Session({ shareCode: generateShareCode(), queue: [], pending: [] });
    await sessionDoc.save();
    res.status(201).json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.get('/:id', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.patch('/:id/close', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    sessionDoc.status = 'closed';
    await sessionDoc.save();
    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.delete('/:id', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findByIdAndDelete(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    res.json({ message: 'Session deleted' });
  } catch (err) {
    next(err);
  }
});

router.post('/:id/walkin', requireAuth, validateInput, async (req, res, next) => {
  try {
    const { name, phone } = req.body;
    if (!name) return res.status(400).json({ error: 'Name is required' });

    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    if (sessionDoc.status === 'closed') return res.status(400).json({ error: 'Session is closed' });

    const nextNumber = getNextQueueNumber(sessionDoc.queue);
    sessionDoc.queue.push({ queueNumber: nextNumber, name, phone: phone || '', paid: false });
    await sessionDoc.save();
    res.status(201).json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.patch('/:id/players/:playerId', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    const player = sessionDoc.queue.id(req.params.playerId);
    if (!player) return res.status(404).json({ error: 'Player not found' });
    player.paid = !player.paid;
    await sessionDoc.save();
    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.delete('/:id/players/:playerId', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    const player = sessionDoc.queue.id(req.params.playerId);
    if (!player) return res.status(404).json({ error: 'Player not found' });
    player.deleteOne();
    await sessionDoc.save();
    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.post('/:id/pending/:requestId/approve', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    const request = sessionDoc.pending.id(req.params.requestId);
    if (!request) return res.status(404).json({ error: 'Request not found' });

    const nextNumber = getNextQueueNumber(sessionDoc.queue);
    sessionDoc.queue.push({ queueNumber: nextNumber, name: request.name, phone: request.phone, paid: false });

    const phone = request.phone;
    const name = request.name;
    request.deleteOne();
    await sessionDoc.save();

    if (phone) {
      const existingMember = await Member.findOne({ phone });
      if (!existingMember) {
        await new Member({ name, phone }).save();
      }
    }

    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

router.post('/:id/pending/:requestId/decline', requireAuth, async (req, res, next) => {
  try {
    const sessionDoc = await Session.findById(req.params.id);
    if (!sessionDoc) return res.status(404).json({ error: 'Session not found' });
    const request = sessionDoc.pending.id(req.params.requestId);
    if (!request) return res.status(404).json({ error: 'Request not found' });
    request.deleteOne();
    await sessionDoc.save();
    res.json(sessionDoc);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
