const mongoose = require('mongoose');

const playerSchema = new mongoose.Schema({
  queueNumber: { type: Number, required: true },
  name: { type: String, required: true, trim: true, minlength: 2 },
  phone: { type: String, default: '', match: /^\d{10,15}$/ },
  paid: { type: Boolean, default: false },
  addedAt: { type: Date, default: Date.now }
});

const pendingSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true, minlength: 2 },
  phone: { type: String, default: '', match: /^\d{10,15}$/ },
  requestedAt: { type: Date, default: Date.now }
});

const sessionSchema = new mongoose.Schema({
  date: { type: Date, default: Date.now },
  status: { type: String, enum: ['open', 'closed'], default: 'open' },
  shareCode: { type: String, required: true, unique: true },
  queue: [playerSchema],
  pending: [pendingSchema]
});

module.exports = mongoose.model('Session', sessionSchema);
