const express = require('express');
const Session = require('../models/Session');
const Member = require('../models/Member');
const { validateInput, validateName, validatePhone } = require('../middleware/validation');
const router = express.Router();

router.get('/session/:shareCode', async (req, res, next) => {
  try {
    const sessionDoc = await Session.findOne({ shareCode: req.params.shareCode });
    if (!sessionDoc) return res.status(404).json({ error: 'Link not found or expired' });
    res.json({ date: sessionDoc.date, status: sessionDoc.status });
  } catch (err) {
    next(err);
  }
});

router.get('/lookup', async (req, res, next) => {
  try {
    const phone = req.query.phone;
    if (!phone) return res.json({ found: false });
    
    if (!validatePhone(phone)) {
      return res.status(400).json({ error: 'Invalid phone format' });
    }

    const member = await Member.findOne({ phone });
    res.json(member ? { found: true, name: member.name } : { found: false });
  } catch (err) {
    next(err);
  }
});

router.post('/session/:shareCode/join', validateInput, async (req, res, next) => {
  try {
    const { name, phone } = req.body;
    
    if (!name || !phone) {
      return res.status(400).json({ error: 'Name and phone are required' });
    }

    if (!validateName(name) || !validatePhone(phone)) {
      return res.status(400).json({ error: 'Invalid name or phone format' });
    }

    const sessionDoc = await Session.findOne({ shareCode: req.params.shareCode });
    if (!sessionDoc) return res.status(404).json({ error: 'Link not found or expired' });
    if (sessionDoc.status === 'closed') return res.status(400).json({ error: 'This session is closed' });
    
    sessionDoc.pending.push({ name, phone });
    await sessionDoc.save();
    res.status(201).json({ message: 'Request sent. Wait for the owner to approve you.' });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
