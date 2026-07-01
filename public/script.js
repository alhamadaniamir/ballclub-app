const API = '/api';
let token = localStorage.getItem('token');
let currentSessionId = null;

function authHeaders() {
  return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token };
}

async function login() {
  const username = document.getElementById('username-input').value;
  const password = document.getElementById('password-input').value;
  const res = await fetch(API + '/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) {
    document.getElementById('login-error').style.display = 'block';
    return;
  }
  const data = await res.json();
  token = data.token;
  localStorage.setItem('token', token);
  showApp();
}

function showApp() {
  document.getElementById('login-screen').classList.remove('active');
  document.getElementById('app-screen').classList.add('active');
  switchTab('session');
}

function switchTab(name) {
  ['history','session','members'].forEach(function(t) {
    document.getElementById(t + '-tab').style.display = t === name ? 'block' : 'none';
    document.getElementById('nav-' + t).classList.toggle('active', t === name);
  });
  // Show empty state by default when switching to session tab to prevent flashing
  if (name === 'session') {
    document.getElementById('session-empty').style.display = 'block';
    document.getElementById('session-active').style.display = 'none';
  }
  if (name === 'history') loadHistory();
  if (name === 'session') loadSessionTab();
  if (name === 'members') loadMembers();
}

async function loadHistory() {
  const res = await fetch(API + '/sessions', { headers: authHeaders() });
  if (res.status === 401) return logout();
  const sessions = await res.json();
  const list = document.getElementById('sessions-list');
  if (sessions.length === 0) {
    list.innerHTML = '<div class="empty-state">No sessions yet. Go to the Session tab to start one.</div>';
    return;
  }
  list.innerHTML = sessions.map(function(s) {
    const date = new Date(s.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const paidCount = s.queue.filter(function(p){ return p.paid; }).length;
    const deleteBtn = s.status === 'closed' ? '<button class="delete-btn" onclick="deleteSession(\'' + s._id + '\')">Delete</button>' : '';
    return '<div class="session-card" onclick="openSession(\'' + s._id + '\')">' +
      '<div><div class="date">' + date + '</div><div class="meta">' + s.queue.length + ' players &middot; ' + paidCount + ' paid</div></div>' +
      '<div style="display: flex; gap: 8px; align-items: center;">' +
      '<span class="pill ' + s.status + '">' + s.status + '</span>' +
      deleteBtn +
      '</div></div>';
  }).join('');
}

async function loadSessionTab() {
  const res = await fetch(API + '/sessions', { headers: authHeaders() });
  const sessions = await res.json();
  const open = sessions.find(function(s){ return s.status === 'open'; });
  if (open) {
    currentSessionId = open._id;
    document.getElementById('session-empty').style.display = 'none';
    document.getElementById('session-active').style.display = 'block';
    renderSession(open);
  } else {
    currentSessionId = null;
    document.getElementById('session-empty').style.display = 'block';
    document.getElementById('session-active').style.display = 'none';
  }
}

async function startSession() {
  const res = await fetch(API + '/sessions', { method: 'POST', headers: authHeaders() });
  const sessionData = await res.json();
  currentSessionId = sessionData._id;
  document.getElementById('session-empty').style.display = 'none';
  document.getElementById('session-active').style.display = 'block';
  renderSession(sessionData);
}

async function openSession(id) {
  currentSessionId = id;
  switchTab('session');
  const res = await fetch(API + '/sessions/' + id, { headers: authHeaders() });
  const sessionData = await res.json();
  document.getElementById('session-empty').style.display = 'none';
  document.getElementById('session-active').style.display = 'block';
  renderSession(sessionData);
}

async function refreshCurrentSession() {
  const res = await fetch(API + '/sessions/' + currentSessionId, { headers: authHeaders() });
  const sessionData = await res.json();
  renderSession(sessionData);
}

function renderSession(sessionData) {
  const date = new Date(sessionData.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  document.getElementById('session-title').textContent = date + ' \u00b7 ' + sessionData.status;
  document.getElementById('close-btn').style.display = sessionData.status === 'closed' ? 'none' : 'inline-block';
  document.getElementById('link-text').textContent = window.location.origin + '/join.html?code=' + sessionData.shareCode;

  const pendingWrap = document.getElementById('pending-wrap');
  pendingWrap.style.display = sessionData.pending.length ? 'block' : 'none';
  document.getElementById('pending-list').innerHTML = sessionData.pending.map(function(p) {
    return '<div class="pending-row"><div style="display: flex; align-items: center; gap: 10px; flex: 1;"><div class="row-name">' + p.name + '<div class="row-sub">' + p.phone + '</div></div></div>' +
      '<div style="display: flex; gap: 8px;"><button class="approve-btn" onclick="approveRequest(\'' + p._id + '\')">Approve</button>' +
      '<button class="decline-btn" onclick="declineRequest(\'' + p._id + '\')">Decline</button></div></div>';
  }).join('');

  const playersList = document.getElementById('players-list');
  if (sessionData.queue.length === 0) {
    playersList.innerHTML = '<div class="empty-state">No approved players yet.</div>';
  } else {
    playersList.innerHTML = sessionData.queue.map(function(p) {
      return '<div class="player-row"><div style="display: flex; align-items: center; gap: 10px; flex: 1;"><div class="queue-num">' + p.queueNumber + '</div>' +
        '<div class="row-name">' + p.name + '</div></div>' +
        '<div style="display: flex; gap: 8px;"><button class="pay-toggle ' + (p.paid ? 'paid' : 'unpaid') + '" onclick="togglePaid(\'' + p._id + '\')">' + (p.paid ? 'Paid' : 'Unpaid') + '</button>' +
        '<button class="action-btn" onclick="deletePlayer(\'' + p._id + '\')">Delete</button></div></div>';
    }).join('');
  }
}

function copyLink() {
  const text = document.getElementById('link-text').textContent;
  navigator.clipboard.writeText(text);
  const btn = document.getElementById('copy-btn');
  btn.textContent = 'Copied';
  setTimeout(function(){ btn.textContent = 'Copy'; }, 1500);
}

async function approveRequest(requestId) {
  await fetch(API + '/sessions/' + currentSessionId + '/pending/' + requestId + '/approve', { method: 'POST', headers: authHeaders() });
  refreshCurrentSession();
}

async function declineRequest(requestId) {
  await fetch(API + '/sessions/' + currentSessionId + '/pending/' + requestId + '/decline', { method: 'POST', headers: authHeaders() });
  refreshCurrentSession();
}

async function addWalkin() {
  const input = document.getElementById('walkin-name');
  const name = input.value.trim();
  if (!name) return;
  try {
    const res = await fetch(API + '/sessions/' + currentSessionId + '/walkin', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ name: name }) });
    if (res.ok) {
      input.value = '';
      await refreshCurrentSession();
    }
  } catch (err) {
    console.error('Error adding player:', err);
  }
}

async function togglePaid(playerId) {
  await fetch(API + '/sessions/' + currentSessionId + '/players/' + playerId, { method: 'PATCH', headers: authHeaders() });
  refreshCurrentSession();
}

async function deletePlayer(playerId) {
  if (!confirm('Remove this player from the queue?')) return;
  try {
    const res = await fetch(API + '/sessions/' + currentSessionId + '/players/' + playerId, { method: 'DELETE', headers: authHeaders() });
    if (res.ok) {
      await refreshCurrentSession();
    }
  } catch (err) {
    console.error('Error deleting player:', err);
    alert('Failed to remove player');
  }
}

async function closeSession() {
  if (!confirm('Close this session? No more players can be added.')) return;
  try {
    const res = await fetch(API + '/sessions/' + currentSessionId + '/close', { method: 'PATCH', headers: authHeaders() });
    if (res.ok) {
      currentSessionId = null;
      document.getElementById('session-empty').style.display = 'block';
      document.getElementById('session-active').style.display = 'none';
      await loadHistory();
      switchTab('history');
    }
  } catch (err) {
    console.error('Error closing session:', err);
    alert('Failed to close session');
  }
}

async function deleteSession(sessionId) {
  if (!confirm('Are you sure you want to delete this session? This cannot be undone.')) return;
  try {
    const res = await fetch(API + '/sessions/' + sessionId, { method: 'DELETE', headers: authHeaders() });
    if (res.ok) {
      loadHistory();
    }
  } catch (err) {
    console.error('Error deleting session:', err);
    alert('Failed to delete session');
  }
}

async function loadMembers() {
  const res = await fetch(API + '/members', { headers: authHeaders() });
  const members = await res.json();
  const list = document.getElementById('members-list');
  if (members.length === 0) {
    list.innerHTML = '<div class="empty-state">No members yet.</div>';
    return;
  }
  list.innerHTML = members.map(function(m) {
    const initials = m.name.split(' ').map(function(w){ return w[0]; }).join('').substring(0,2).toUpperCase();
    return '<div class="player-row"><div class="queue-num">' + initials + '</div>' +
      '<div class="row-name">' + m.name + '<div class="row-sub">' + (m.phone || 'No phone') + '</div></div>' +
      '<button class="action-btn" onclick="deleteMember(\'' + m._id + '\')">Delete</button></div>';
  }).join('');
}

async function addMember() {
  const name = document.getElementById('member-name').value.trim();
  const phone = document.getElementById('member-phone').value.trim();
  if (!name) return;
  try {
    const res = await fetch(API + '/members', { method: 'POST', headers: authHeaders(), body: JSON.stringify({ name: name, phone: phone }) });
    if (res.ok) {
      document.getElementById('member-name').value = '';
      document.getElementById('member-phone').value = '';
      await loadMembers();
    }
  } catch (err) {
    console.error('Error adding member:', err);
  }
}

async function deleteMember(memberId) {
  if (!confirm('Delete this member from the directory?')) return;
  try {
    const res = await fetch(API + '/members/' + memberId, { method: 'DELETE', headers: authHeaders() });
    if (res.ok) {
      await loadMembers();
    }
  } catch (err) {
    console.error('Error deleting member:', err);
    alert('Failed to delete member');
  }
}

function logout() {
  localStorage.removeItem('token');
  token = null;
  document.getElementById('app-screen').classList.remove('active');
  document.getElementById('login-screen').classList.add('active');
}

// if (token) showApp();
// Always show login page first, then redirect after successful login
