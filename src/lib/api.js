import { useAuth } from '@/composables/useAuth'
import router from '@/router'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

async function request(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const { token } = useAuth()
    headers.Authorization = `Bearer ${token.value}`
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && auth) {
    useAuth().logout()
    router.push({ name: 'login' })
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail ?? detail
    } catch {
      // response had no JSON body
    }
    throw new Error(detail)
  }

  if (res.status === 204) return null
  return res.json()
}

function nameFields({ firstName, middleName, lastName }) {
  return { first_name: firstName, middle_name: middleName || '', last_name: lastName }
}

async function downloadCsv(path, filename) {
  const { token } = useAuth()
  const res = await fetch(`${BASE}${path}`, { headers: { Authorization: `Bearer ${token.value}` } })
  if (res.status === 401) {
    useAuth().logout()
    router.push({ name: 'login' })
    return
  }
  if (!res.ok) throw new Error('Export failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function exportSessionCsv(id) {
  return downloadCsv(`/sessions/${id}/export`, `session-${id}.csv`)
}

export function exportMembersCsv() {
  return downloadCsv('/members/export', 'members.csv')
}

export function loginRequest(username, password) {
  return request('/auth/login', { method: 'POST', body: { username, password } })
}

export function getMe() {
  return request('/auth/me', { auth: true })
}

export function changePassword(currentPassword, newPassword) {
  return request('/auth/me', {
    method: 'PATCH',
    auth: true,
    body: { current_password: currentPassword, new_password: newPassword },
  })
}

export function updateProfile(username, firstName, lastName) {
  return request('/auth/me/profile', {
    method: 'PATCH',
    auth: true,
    body: { username, first_name: firstName || '', last_name: lastName || '' },
  })
}

export function suggestUsername(firstName, lastName) {
  const q = new URLSearchParams({ first_name: firstName || '', last_name: lastName || '' })
  return request(`/auth/me/username-suggestion?${q.toString()}`, { auth: true })
}

export function listSessions(params = {}) {
  const { status, dateFrom, dateTo, page, pageSize } = typeof params === 'string' ? { status: params } : params
  const search = new URLSearchParams()
  if (status) search.set('status', status)
  if (dateFrom) search.set('date_from', dateFrom)
  if (dateTo) search.set('date_to', dateTo)
  if (page) search.set('page', page)
  if (pageSize) search.set('page_size', pageSize)
  const query = search.toString()
  return request(`/sessions/${query ? `?${query}` : ''}`, { auth: true })
}

export function createSession() {
  return request('/sessions/', { method: 'POST', auth: true })
}

export function getSession(id, search) {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  return request(`/sessions/${id}${query}`, { auth: true })
}

export function closeSession(id) {
  return request(`/sessions/${id}/close`, { method: 'PATCH', auth: true })
}

export function setSessionFee(id, fee) {
  return request(`/sessions/${id}/fee`, { method: 'PATCH', auth: true, body: { fee } })
}

export function updateSession(id, meta) {
  return request(`/sessions/${id}`, { method: 'PATCH', auth: true, body: meta })
}

export function deleteSession(id) {
  return request(`/sessions/${id}`, { method: 'DELETE', auth: true })
}

export function addWalkin(sessionId, nameParts, phone) {
  return request(`/sessions/${sessionId}/walkin`, {
    method: 'POST',
    auth: true,
    body: { ...nameFields(nameParts), phone: phone || '' },
  })
}

export function togglePlayerPaid(sessionId, playerId) {
  return request(`/sessions/${sessionId}/players/${playerId}`, { method: 'PATCH', auth: true })
}

export function deletePlayer(sessionId, playerId) {
  return request(`/sessions/${sessionId}/players/${playerId}`, { method: 'DELETE', auth: true })
}

export function approveRequest(sessionId, requestId) {
  return request(`/sessions/${sessionId}/pending/${requestId}/approve`, { method: 'POST', auth: true })
}

export function declineRequest(sessionId, requestId) {
  return request(`/sessions/${sessionId}/pending/${requestId}/decline`, { method: 'POST', auth: true })
}

export function listMembers(params = {}) {
  const { search, page, pageSize } = typeof params === 'string' ? { search: params } : params
  const query = new URLSearchParams()
  if (search) query.set('search', search)
  if (page) query.set('page', page)
  if (pageSize) query.set('page_size', pageSize)
  const qs = query.toString()
  return request(`/members/${qs ? `?${qs}` : ''}`, { auth: true })
}

export function addMember(nameParts, phone) {
  return request('/members/', { method: 'POST', auth: true, body: { ...nameFields(nameParts), phone: phone || '' } })
}

export function getMemberHistory(id) {
  return request(`/members/${id}/history`, { auth: true })
}

export function updateMember(id, patch) {
  return request(`/members/${id}`, { method: 'PATCH', auth: true, body: patch })
}

export function deleteMember(id) {
  return request(`/members/${id}`, { method: 'DELETE', auth: true })
}

export function getDashboard() {
  return request('/dashboard/', { auth: true })
}

export function listOwners(search) {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  return request(`/owners/${query}`, { auth: true })
}

export function createOwner(username, password, firstName = '', lastName = '') {
  return request('/owners/', {
    method: 'POST',
    auth: true,
    body: { username, password, first_name: firstName || '', last_name: lastName || '' },
  })
}

export function deleteOwner(id) {
  return request(`/owners/${id}`, { method: 'DELETE', auth: true })
}

export function getPublicSession(shareCode) {
  return request(`/public/session/${shareCode}`)
}

export function submitJoin(shareCode, nameParts, phone) {
  return request(`/public/session/${shareCode}/join`, {
    method: 'POST',
    body: { ...nameFields(nameParts), phone },
  })
}

export function lookupByPhone(phone) {
  return request(`/public/lookup?phone=${encodeURIComponent(phone)}`)
}
