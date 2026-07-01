const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const router = express.Router();

router.post('/login', async (req, res, next) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    if (username !== process.env.OWNER_USERNAME) {
      return res.status(401).json({ error: 'Incorrect username or password' });
    }

    const passwordMatch = await bcrypt.compare(password, process.env.OWNER_PASSWORD_HASH);
    if (!passwordMatch) {
      return res.status(401).json({ error: 'Incorrect username or password' });
    }

    const token = jwt.sign({ role: 'owner' }, process.env.JWT_SECRET, { expiresIn: '7d' });
    res.json({ token });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
