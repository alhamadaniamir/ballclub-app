const mongoose = require('mongoose');

const memberSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true, minlength: 2 },
  phone: { type: String, default: '', match: /^\d{10,15}$/ },
  dateJoined: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Member', memberSchema);
