import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

function App() {
  const api = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const [items, setItems] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selected, setSelected] = useState(null);
  const [overlay, setOverlay] = useState(false);
  const [opacity, setOpacity] = useState(50);
  const [log, setLog] = useState([]);
  const [health, setHealth] = useState(null);
  const [page, setPage] = useState('studies');
  const [reviewer, setReviewer] = useState('');
  const [comment, setComment] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    try {
      const [studyResponse, auditResponse, healthResponse] = await Promise.all([
        fetch(`${api}/studies`), fetch(`${api}/audit-log`), fetch(`${api}/health`),
      ]);
      const nextItems = await studyResponse.json();
      setItems(nextItems);
      setLog(await auditResponse.json());
      setHealth(await healthResponse.json());
      setSelected(nextItems.find((item) => item.id === selectedId) || null);
    } catch {
      setMessage('Cannot connect to the API. Start it with python run.py serve.');
    }
  }

  useEffect(() => { load(); }, []);

  async function upload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    const response = await fetch(`${api}/upload`, { method: 'POST', body: form });
    if (!response.ok) {
      setMessage(`Upload failed: ${(await response.json()).detail || response.statusText}`);
      return;
    }
    const item = await response.json();
    setSelectedId(item.id);
    setSelected(item);
    setMessage('');
    await load();
  }

  async function review(decision) {
    if (!selected || !reviewer.trim()) {
      setMessage('Enter a reviewer name before recording a decision.');
      return;
    }
    const response = await fetch(`${api}/studies/${selected.id}/review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, reviewer: reviewer.trim(), comment }),
    });
    if (!response.ok) {
      setMessage(`Review failed: ${(await response.json()).detail || response.statusText}`);
      return;
    }
    setSelected(await response.json());
    setMessage('');
    await load();
  }

  const reviewed = selected && selected.status !== 'pending';
  return <>
    <header>
      <h1>AIML-02 Imaging Viewer</h1>
      <div>{health?.model_loaded ? `Model: ${health.model_version} | real` : 'Model: DEMO'}</div>
      <strong>For education only, not clinical use.</strong>
    </header>
    {!health?.model_loaded && <div className="demo-warning">DEMO MODEL - predictions are not meaningful</div>}
    <nav>
      <button onClick={() => setPage('studies')}>Studies</button>
      <button onClick={() => setPage('audit')}>Audit Log</button>
      <label className="upload">Upload scan<input type="file" accept="image/*,.dcm,application/dicom" onChange={upload} /></label>
      <button onClick={load}>Refresh</button>
    </nav>
    {message && <p className="message" role="status">{message}</p>}
    {page === 'audit' ? <main>
      <h2>Audit Log</h2>
      {log.map((entry) => <article key={entry.id}>
        {entry.when} | {entry.who} {entry.what} | Confidence {(entry.confidence * 100).toFixed(1)}% | {entry.comment}
      </article>)}
    </main> : <main className="layout">
      <aside>
        <h2>Studies</h2>
        {items.map((item) => <button
          className={`study ${item.id === selectedId ? 'selected' : ''}`}
          onClick={() => { setSelectedId(item.id); setSelected(item); setMessage(''); }} key={item.id}>
          <b>{item.name || item.filename}</b>
          <small>{item.prediction} | {(item.confidence * 100).toFixed(1)}%</small>
          <span className={`badge ${item.status}`}>{item.status}</span>
        </button>)}
      </aside>
      <section>
        {selected ? <>
          <h2>{selected.name || selected.filename}</h2>
          <p>Prediction: <b>{selected.prediction}</b> | Confidence: {(selected.confidence * 100).toFixed(1)}%</p>
          <div className="confidence-label">Predicted-class confidence</div>
          <div className="confidence" role="meter" aria-valuenow={selected.confidence * 100} aria-valuemin="0" aria-valuemax="100">
            <div style={{ width: `${Math.max(0, Math.min(100, selected.confidence * 100))}%` }} />
          </div>
          <small>Pneumonia probability: {(selected.pneumonia_probability * 100).toFixed(1)}%</small>
          <div className="scan">
            <img src={`${api}/studies/${selected.id}/image`} alt="Original scan" />
            {overlay && <img className="heat" style={{ opacity: opacity / 100 }} src={`${api}/studies/${selected.id}/heatmap`} alt="Grad-CAM heatmap overlay" />}
          </div>
          <div className="scan-controls">
            <label><input type="checkbox" checked={overlay} disabled={!health?.model_loaded} onChange={(event) => setOverlay(event.target.checked)} /> Show Grad-CAM overlay</label>
            <label>Overlay opacity <input aria-label="Overlay opacity" type="range" min="0" max="100" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label>
          </div>
          {!health?.model_loaded && <small>Grad-CAM is unavailable until a trained classifier is loaded.</small>}
          {reviewed ? <p className="decision">Decision recorded: {selected.status}</p> : <div className="review-controls">
            <label>Reviewer name<input value={reviewer} onChange={(event) => setReviewer(event.target.value)} /></label>
            <label>Comment<input value={comment} onChange={(event) => setComment(event.target.value)} /></label>
            <button onClick={() => review('approve')}>Approve</button>
            <button className="reject" onClick={() => review('reject')}>Reject</button>
          </div>}
        </> : <p>Choose a study or upload an image.</p>}
      </section>
    </main>}
  </>;
}

createRoot(document.getElementById('root')).render(<App />);
