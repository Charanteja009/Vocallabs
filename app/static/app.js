const form = document.querySelector('#form'), result = document.querySelector('#result'), loading = document.querySelector('#loading'), submit = document.querySelector('#submit');
const esc = s => String(s ?? 'Not stated').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c]));

form.addEventListener('submit', async event => {
  event.preventDefault(); result.hidden = true; loading.hidden = false; submit.disabled = true;
  try {
    const response = await fetch('/api/reconcile', { method: 'POST', body: new FormData(form) });
    const data = await response.json(); if (!response.ok) throw Error(data.detail || 'Could not reconcile evidence.');
    render(data);
  } catch (err) {
    result.innerHTML = `<article class="error"><b>No decision issued</b><p>${esc(err.message)}</p><small>Sakshi did not invent a payment recommendation.</small></article>`; result.hidden = false;
  } finally { loading.hidden = true; submit.disabled = false; }
});

document.querySelector('#evaluate').addEventListener('click', async () => {
  const target = document.querySelector('#evaluation'); target.textContent = 'Running safety evaluation…';
  try { const data = await (await fetch('/api/evaluate')).json(); target.innerHTML = `<b>${data.passed}/${data.case_count} cases passed · ${data.decision_accuracy}% accuracy · ${data.unsafe_approvals} unsafe approvals</b>`; }
  catch { target.textContent = 'Evaluation unavailable. Check the local server.'; }
});

function render(data) {
  const x = data.result, conflicts = x.conflicts || [], evidence = x.provenance || [], items = (data.document.items || []).map(i => `<li><b>${esc(i.name)}</b><span>${esc(i.quantity)} ${esc(i.unit)} · ${Math.round(Number(i.confidence || 0) * 100)}% document readability</span></li>`).join('');
  const rows = evidence.map(e => `<li><b>${esc(e.field)}${e.item ? ` — ${esc(e.item)}` : ''}</b><span>${esc(e.value)} · ${esc(e.source)}${e.timestamp ? ` · ${esc(e.timestamp)}` : ''} · ${esc(e.quality)}</span></li>`).join('');
  const quality = x.evidence_quality || { level: 'LOW', score: 0, factors: [] };
  const timing = data.observability?.timings_ms || {};
  result.innerHTML = `<article class="verdict ${esc(x.decision)}"><div><p class="eyebrow">RECONCILIATION #${esc(data.id)}</p><h2>${esc(x.decision).replaceAll('_', ' ')}</h2><p>${esc(x.reasoning_summary)}</p><small>Final state enforced by: ${esc(x.decision_basis)}</small></div><strong>${esc(quality.level)}<small>evidence quality · ${esc(quality.score)}/100</small></strong></article>
  <div class="results"><article class="card"><p class="eyebrow">DOCUMENT CLAIM</p><h3>${esc(data.document.supplier?.value)} · ${esc(data.document.date?.value)}</h3><ul>${items || '<li>No readable items</li>'}</ul></article><article class="card"><p class="eyebrow">VOICE CLAIM</p><blockquote>“${esc(data.transcript)}”</blockquote></article></div>
  <article class="card conflicts"><p class="eyebrow">${conflicts.length ? 'CONFLICTS FOUND' : 'EVIDENCE ALIGNMENT'}</p>${conflicts.length ? conflicts.map(c => `<div class="conflict"><b>${esc(c.field)}</b><p>Challan: ${esc(c.document_claim)}<br>Voice note: ${esc(c.voice_claim)}</p><small>${esc(c.why)}</small></div>`).join('') : '<p>No material conflict was identified. Human review remains required before payment.</p>'}<div class="question"><b>Ask next</b><p>${esc(x.review_question)}</p></div></article>
  <div class="results"><article class="card"><p class="eyebrow">EVIDENCE TRAIL</p><ul>${rows || '<li>No evidence trail available</li>'}</ul></article><article class="card"><p class="eyebrow">OBSERVABILITY</p><p>Vision: ${esc(timing.vision_ms ?? '—')} ms<br>Speech: ${esc(timing.transcription_ms ?? '—')} ms<br>Reconciliation: ${esc(timing.reconciliation_ms ?? '—')} ms<br>Total: ${esc(data.observability?.total_ms ?? '—')} ms</p><label class="voice-language">Voice language<select id="voice-language"><option value="hi-IN">Hindi / Hinglish</option><option value="te-IN">Telugu</option><option value="ml-IN">Malayalam</option><option value="kn-IN">Kannada</option><option value="en-IN">English</option></select></label><label class="voice-language">Voice<select id="voice-choice"></select></label><label class="voice-language">Speaking style<select id="voice-rate"><option value="0.88">Calm and clear</option><option value="0.96">Natural</option><option value="1.05">Faster</option></select></label><button class="secondary" id="listen" type="button">Listen to review</button><button class="secondary" id="packet" type="button">Download review packet</button></article></div>`;
  document.querySelector('#packet').addEventListener('click', () => downloadPacket(data));
  document.querySelector('#listen').addEventListener('click', () => speakReview(data));
  document.querySelector('#voice-language').addEventListener('change', updateVoiceOptions);
  updateVoiceOptions(); window.speechSynthesis.onvoiceschanged = updateVoiceOptions;
  result.hidden = false; result.scrollIntoView({ behavior: 'smooth' });
}

async function downloadPacket(data) {
  const response = await fetch('/api/review-packet', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  const blob = await response.blob(), link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `sakshi-review-${data.id}.json`; link.click(); URL.revokeObjectURL(link.href);
}

function speakReview(data) {
  if (!('speechSynthesis' in window)) { alert('Voice playback is not supported in this browser.'); return; }
  window.speechSynthesis.cancel();
  const result = data.result, conflicts = result.conflicts || [];
  const language = document.querySelector('#voice-language').value;
  const message = localizedReview(language, result, conflicts);
  const utterance = new SpeechSynthesisUtterance(message);
  const voices = window.speechSynthesis.getVoices();
  const selected = document.querySelector('#voice-choice').value;
  utterance.voice = voices.find(v => v.voiceURI === selected) || voices.find(v => v.lang.toLowerCase().startsWith(language.toLowerCase())) || voices.find(v => v.lang.toLowerCase().startsWith('en-in')) || null;
  utterance.lang = utterance.voice?.lang || language; utterance.rate = Number(document.querySelector('#voice-rate').value); utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

function updateVoiceOptions() {
  const language = document.querySelector('#voice-language')?.value, select = document.querySelector('#voice-choice');
  if (!language || !select || !('speechSynthesis' in window)) return;
  const voices = window.speechSynthesis.getVoices();
  const matching = voices.filter(v => v.lang.toLowerCase().startsWith(language.toLowerCase())) || [];
  const choices = matching.length ? matching : voices.filter(v => v.lang.toLowerCase().startsWith('en-in'));
  const previous = select.value;
  select.innerHTML = choices.length ? choices.map(v => `<option value="${esc(v.voiceURI)}">${esc(v.name)}${v.localService ? ' (device voice)' : ''}</option>`).join('') : '<option value="">Default device voice</option>';
  if ([...select.options].some(option => option.value === previous)) select.value = previous;
}

function localizedReview(language, result, conflicts) {
  const blocked = result.decision !== 'RECOMMEND_PROCEED';
  const hasQuantity = conflicts.some(c => /quantity|count|unit/i.test(c.field));
  const hasDamage = conflicts.some(c => /condition|damage|wet|broken/i.test(c.field));
  const issueCount = conflicts.length;
  const copy = {
    'hi-IN': { title: 'Sakshi review.', hold: 'Payment hold par rakhiye.', proceed: 'Evidence theek hai, lekin final payment approval supervisor karega.', pending: 'Analysis complete nahi ho saka. Payment pending rakhiye.', quality: 'Evidence quality', issues: 'issue mile hain.', none: 'Koi direct conflict identify nahi hua.', qty: 'Agla step: foreman ke saath delivered material ko physically count kijiye.', damage: 'Agla step: damaged material inspect karke photo lijiye.', other: 'Agla step: source evidence ko supervisor ke saath verify kijiye.' },
    'te-IN': { title: 'సాక్షి సమీక్ష.', hold: 'చెల్లింపును నిలిపివేయండి.', proceed: 'ఆధారాలు సరిపోతున్నాయి, కానీ తుది చెల్లింపు అనుమతి సూపర్వైజర్‌దే.', pending: 'విశ్లేషణ పూర్తికాలేదు. చెల్లింపును పెండింగ్‌లో ఉంచండి.', quality: 'ఆధారాల నాణ్యత', issues: 'సమస్యలు గుర్తించబడ్డాయి.', none: 'నేరుగా ఏ విభేదం గుర్తించబడలేదు.', qty: 'తదుపరి చర్య: ఫోర్‌మన్‌తో కలిసి సరుకును భౌతికంగా లెక్కించండి.', damage: 'తదుపరి చర్య: దెబ్బతిన్న సరుకును పరిశీలించి ఫోటో తీయండి.', other: 'తదుపరి చర్య: ఆధారాలను సూపర్వైజర్‌తో ధృవీకరించండి.' },
    'ml-IN': { title: 'സാക്ഷി അവലോകനം.', hold: 'പണം നൽകുന്നത് തടഞ്ഞുവയ്ക്കുക.', proceed: 'തെളിവുകൾ യോജിക്കുന്നു, എന്നാൽ അന്തിമ പണമടയ്ക്കൽ അനുമതി സൂപ്പർവൈസറുടേതാണ്.', pending: 'വിശകലനം പൂർത്തിയാക്കാനായില്ല. പണമടയ്ക്കൽ പെൻഡിങ്ങിൽ വയ്ക്കുക.', quality: 'തെളിവിന്റെ നിലവാരം', issues: 'പ്രശ്നങ്ങൾ കണ്ടെത്തി.', none: 'നേരിട്ടുള്ള വൈരുദ്ധ്യം കണ്ടെത്തിയില്ല.', qty: 'അടുത്ത നടപടി: ഫോർമാനൊപ്പം സാധനങ്ങൾ നേരിട്ട് എണ്ണുക.', damage: 'അടുത്ത നടപടി: കേടായ സാധനങ്ങൾ പരിശോധിച്ച് ഫോട്ടോ എടുക്കുക.', other: 'അടുത്ത നടപടി: തെളിവുകൾ സൂപ്പർവൈസറുമായി പരിശോധിക്കുക.' },
    'kn-IN': { title: 'ಸಾಕ್ಷಿ ಪರಿಶೀಲನೆ.', hold: 'ಪಾವತಿಯನ್ನು ತಡೆಹಿಡಿಯಿರಿ.', proceed: 'ಸಾಕ್ಷ್ಯಗಳು ಹೊಂದಿಕೆಯಾಗಿವೆ, ಆದರೆ ಅಂತಿಮ ಪಾವತಿ ಅನುಮತಿ ಮೇಲ್ವಿಚಾರಕರದ್ದಾಗಿದೆ.', pending: 'ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣವಾಗಲಿಲ್ಲ. ಪಾವತಿಯನ್ನು ಬಾಕಿ ಇರಿಸಿ.', quality: 'ಸಾಕ್ಷ್ಯದ ಗುಣಮಟ್ಟ', issues: 'ಸಮಸ್ಯೆಗಳು ಕಂಡುಬಂದಿವೆ.', none: 'ನೇರವಾದ ವ್ಯತ್ಯಾಸ ಕಂಡುಬಂದಿಲ್ಲ.', qty: 'ಮುಂದಿನ ಕ್ರಮ: ಫೋರ್‌ಮನ್ ಜೊತೆ ಸರಕುಗಳನ್ನು ಭೌತಿಕವಾಗಿ ಎಣಿಸಿ.', damage: 'ಮುಂದಿನ ಕ್ರಮ: ಹಾನಿಯಾದ ಸರಕನ್ನು ಪರಿಶೀಲಿಸಿ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.', other: 'ಮುಂದಿನ ಕ್ರಮ: ಮೇಲ್ವಿಚಾರಕರೊಂದಿಗೆ ಸಾಕ್ಷ್ಯಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.' },
    'en-IN': { title: 'Sakshi review.', hold: 'Keep payment on hold.', proceed: 'Evidence is consistent, but final payment approval remains with the supervisor.', pending: 'Analysis could not be completed. Keep payment pending.', quality: 'Evidence quality', issues: 'issues were found.', none: 'No direct conflict was identified.', qty: 'Next action: physically count the delivered material with the foreman.', damage: 'Next action: inspect and photograph the damaged material.', other: 'Next action: verify the source evidence with the supervisor.' },
  }[language] || {};
  const decision = result.decision === 'PENDING_REVIEW' ? copy.pending : blocked ? copy.hold : copy.proceed;
  const conflictLine = issueCount ? `${issueCount} ${copy.issues}` : copy.none;
  const next = hasQuantity ? copy.qty : hasDamage ? copy.damage : copy.other;
  return `${copy.title} ${decision} ${copy.quality}: ${result.evidence_quality?.level || 'LOW'}. ${conflictLine} ${next}`;
}
