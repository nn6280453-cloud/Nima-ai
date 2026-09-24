/* ==================== app.js ==================== */
/*  Minimal Express server that: 1) mounts the bot router
 * 2) exposes a /ask endpoint that talks to OpenRouter
 * 3) has global error handling
 */

require('dotenv').config();          // loads .env file if present
const express = require('express');
const axios   = require('axios');
const botRouter = require('./botRouter');

const app = express();

/* 1️⃣  body‑parsing middleware – required for POST /ask  */
app.use(express.json());          // parses application/json
app.use(express.urlencoded({ extended: true }));  // parses application/x-www-form-urlencoded

/* 2️⃣  mount the WhatsApp‑bot router – keep your existing code  */
app.use('/api', botRouter);       // all paths inside botRouter start with /api/

/* 3️⃣  /ask – simple LLM proxy  */
app.post('/ask', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Missing "message" in request body' });
    }

    /* ----------  OpenRouter call  ---------- */
    const payload = {
      model: 'deepseek/deepseek-r1',          // you can change this if you wish
      messages: [{ role: 'user', content: message }],
      max_tokens: 1024
    };

    const headers = {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY || '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'}`, // <-- key
      'Content-Type': 'application/json'
    };

    const response = await axios.post(
      'https://openrouter.ai/api/v1/chat/completions',
      payload,
      { headers, timeout: 60000 }          // 60‑second timeout
    );

    if (!response.data?.choices?.[0]?.message?.content) {
      throw new Error('OpenRouter response missing reply');
    }

    res.json({ reply: response.data.choices[0].message.content });

  } catch (err) {
    console.error('POST /ask error:', err);
    /* 4️⃣  return a clean JSON error to the client  */
    res.status(500).json({ error: err.message || 'Internal server error' });
  }
});

/* 5️⃣  global error handler (optional but nice for uncaught errors) */
app.use((err, req, res, next) => {
  console.error('Uncaught error:', err);
  res.status(500).json({ error: 'Unexpected server error' });
});

/* 6️⃣  start listening  */
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server listening on port ${PORT}`));
