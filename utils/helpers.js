function generateShareCode() {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

function getNextQueueNumber(queue) {
  return queue.length > 0 ? Math.max(...queue.map(p => p.queueNumber)) + 1 : 1;
}

module.exports = { generateShareCode, getNextQueueNumber };
