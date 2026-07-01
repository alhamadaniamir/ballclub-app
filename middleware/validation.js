const validateName = (name) => {
  if (!name || typeof name !== 'string') return false;
  return name.trim().length >= 2 && name.trim().length <= 100;
};

const validatePhone = (phone) => {
  if (!phone || typeof phone !== 'string') return false;
  const cleanPhone = phone.replace(/\D/g, '');
  return cleanPhone.length >= 10 && cleanPhone.length <= 15;
};

const validateInput = (req, res, next) => {
  const { name, phone } = req.body;
  if (name !== undefined && !validateName(name)) {
    return res.status(400).json({ error: 'Invalid name. Must be 2-100 characters.' });
  }
  if (phone !== undefined && phone && !validatePhone(phone)) {
    return res.status(400).json({ error: 'Invalid phone. Must be 10-15 digits.' });
  }
  next();
};

const errorHandler = (err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal server error' });
};

module.exports = { validateInput, validateName, validatePhone, errorHandler };
