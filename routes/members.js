const express = require('express');
const Member = require('../models/Member');
const { requireAuth } = require('../middleware/auth');
const { validateInput } = require('../middleware/validation');
const router = express.Router();

router.get('/', requireAuth, async (req, res, next) => {
  try {
    const members = await Member.find().sort({ name: 1 });
    res.json(members);
  } catch (err) {
    next(err);
  }
});

router.post('/', requireAuth, validateInput, async (req, res, next) => {
  try {
    const { name, phone } = req.body;
    if (!name) return res.status(400).json({ error: 'Name is required' });

    const member = new Member({ name, phone: phone || '' });
    await member.save();
    res.status(201).json(member);
  } catch (err) {
    if (err.name === 'ValidationError') {
      return res.status(400).json({ error: 'Invalid input data' });
    }
    next(err);
  }
});

router.patch('/:id', requireAuth, validateInput, async (req, res, next) => {
  try {
    const member = await Member.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true });
    if (!member) return res.status(404).json({ error: 'Member not found' });
    res.json(member);
  } catch (err) {
    if (err.name === 'ValidationError') {
      return res.status(400).json({ error: 'Invalid input data' });
    }
    next(err);
  }
});

router.delete('/:id', requireAuth, async (req, res, next) => {
  try {
    const member = await Member.findByIdAndDelete(req.params.id);
    if (!member) return res.status(404).json({ error: 'Member not found' });
    res.json({ message: 'Member deleted' });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
