async function fetchPlayers(){
  const res = await fetch('/api/players');
  const players = await res.json();
  const container = document.getElementById('players');
  container.innerHTML = '';
  players.forEach((p, idx) => {
    const col = document.createElement('div');
    col.className = 'col-12';
    col.innerHTML = `
      <div class="card">
        <div class="card-body d-flex justify-content-between align-items-center">
          <div>
            <div class="h5 mb-1">${idx + 1}. ${p.name || ('Player ' + (p.number || (idx+1)))}</div>
            <div class="small text-muted">Joined: ${new Date(p.created_at).toLocaleString()}</div>
          </div>
          <div class="text-end d-flex flex-column align-items-end">
            <span class="badge ${p.paid? 'badge-paid':'badge-unpaid'} mb-2">${p.paid? 'Paid':'Unpaid'}</span>
            <div class="d-grid">
              <button class="btn btn-sm btn-outline-primary toggle-pay">Toggle</button>
            </div>
          </div>
        </div>
      </div>
    `;
    const btn = col.querySelector('.toggle-pay');
    btn.addEventListener('click', async ()=>{
      await fetch(`/api/players/${p.id}/pay`, {method:'PUT', headers:{'content-type':'application/json'}});
      fetchPlayers();
    });
    container.appendChild(col);
  });
}

document.getElementById('addForm').addEventListener('submit', async e =>{
  e.preventDefault();
  const name = document.getElementById('name').value.trim();
  if (!name) return;
  await fetch('/api/players', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({name})});
  document.getElementById('addForm').reset();
  fetchPlayers();
});

fetchPlayers();
