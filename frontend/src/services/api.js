/**
 * StoreLens AI API Client
 */
const API_BASE = '/api';

export async function getCatalog(query = '', category = '') {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (category && category !== 'All') params.append('category', category);
  
  const res = await fetch(`${API_BASE}/catalog?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch catalog: ${res.statusText}`);
  return res.json();
}

export async function onboardVideo(file = null, useSample = false) {
  const formData = new FormData();
  if (file) {
    formData.append('video', file);
  }
  if (useSample) {
    formData.append('use_sample', 'true');
  }

  const res = await fetch(`${API_BASE}/onboard-video`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Video onboarding failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendVoiceUpdate({ audioBlob = null, transcript = '' }) {
  const formData = new FormData();
  if (audioBlob) {
    formData.append('audio', audioBlob, 'recording.webm');
  }
  if (transcript) {
    formData.append('transcript', transcript);
  }

  const res = await fetch(`${API_BASE}/voice-update`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Voice update failed: ${res.statusText}`);
  }
  return res.json();
}

export async function resetCatalog(seed = false) {
  const res = await fetch(`${API_BASE}/reset?seed=${seed}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Reset failed: ${res.statusText}`);
  return res.json();
}
