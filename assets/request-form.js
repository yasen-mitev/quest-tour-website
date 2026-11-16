/* Game play request form. The one place the site talks to the app: three calls to
   <form data-api>/api/public/* (games, challenge, requests), JSON in and out, no cookies.
   Plain script, no dependencies. The form stays hidden, and the no-JS line stays visible,
   until the games have loaded, so every failure ends up on that line.

   Protection, client side:
   - A self-hosted proof-of-work challenge (ALTCHA-compatible: sha256(salt + number) == challenge).
     It is solved in the background while the visitor types.
   - The server drops a submission that arrives sooner than min_fill_seconds after it issued the
     challenge. The wait is therefore counted on this page from the moment the challenge was
     RECEIVED (performance.now()), which is never earlier than the issue time, and the page's wall
     clock is never compared with the server's.
   - A challenge is accepted once, so a fresh one is fetched after every 4xx and every success. */
(function () {
  'use strict';

  const FRESH_MARGIN_MS = 30 * 1000;   // fetch a new challenge when less than this is left on it
  // Server field names that have exactly one control in the form; everything else is shown in the status line.
  const SINGLE_FIELDS = ['game_key', 'play_date', 'contact_name', 'contact_email', 'contact_phone', 'message', 'terms_accepted'];

  /* Finds the number N in 0..maxnumber with sha256(salt + N) == challenge (hex), or null. */
  async function solve(challenge, salt, maxnumber) {
    const subtle = typeof globalThis !== 'undefined' && globalThis.crypto && globalThis.crypto.subtle;
    if (!subtle || !/^([0-9a-f]{2})+$/i.test(challenge)) return null;
    const target = new Uint8Array(challenge.match(/../g).map(function (byte) { return parseInt(byte, 16); }));
    const encoder = new TextEncoder();
    for (let n = 0; n <= maxnumber; n++) {
      const digest = new Uint8Array(await subtle.digest('SHA-256', encoder.encode(salt + n)));
      if (digest.length === target.length && digest.every(function (byte, i) { return byte === target[i]; })) return n;
    }
    return null;
  }

  if (typeof module !== 'undefined' && module.exports) module.exports = { solve: solve };
  if (typeof document === 'undefined') return;

  const form = document.getElementById('request-form');
  const fallback = document.getElementById('request-fallback');
  const statusEl = document.getElementById('request-status');
  if (!form || !fallback || !statusEl) return;
  if (!(window.crypto && window.crypto.subtle)) return;      // no Web Crypto: the no-JS line stays

  const api = (form.getAttribute('data-api') || '').replace(/\/+$/, '');
  const termsVersion = form.getAttribute('data-terms-version') || '';
  const maxTeams = parseInt(form.getAttribute('data-max-teams'), 10) || 1;
  const gameSelect = form.elements.game_key;
  const introEl = document.getElementById('game-intro');
  const teamsEl = document.getElementById('request-teams');
  const addTeam = document.getElementById('add-team');
  const submit = form.querySelector('button[type="submit"]');
  const submitLabel = submit.textContent;
  const teamTemplate = teamsEl.querySelector('.team-row').cloneNode(true);

  let current = null;     // { data, receivedAt, solution } of the challenge in use
  let busy = false;

  function setStatus(text, kind) {
    statusEl.textContent = text;
    statusEl.className = 'req-status' + (kind ? ' is-' + kind : '');
  }

  function sleep(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms); }); }

  async function getJson(path) {
    const response = await fetch(api + path, { credentials: 'omit', cache: 'no-store' });
    if (!response.ok) throw new Error('GET ' + path + ' ' + response.status);
    return response.json();
  }

  /* ---- challenge ---- */

  async function fetchChallenge() {
    const data = await getJson('/api/public/requests/challenge');
    const receivedAt = performance.now();
    const next = { data: data, receivedAt: receivedAt, solution: solve(data.challenge, data.salt, data.maxnumber) };
    next.solution.catch(function () {});      // a failure is reported when the submit awaits it
    current = next;
    return next;
  }

  function freshEnough(challenge) {
    const left = challenge.data.expires_in_seconds * 1000 - (performance.now() - challenge.receivedAt);
    return left >= FRESH_MARGIN_MS;
  }

  function refreshChallenge() {
    current = null;
    return fetchChallenge().catch(function () {});     // the next submit fetches again if this failed
  }

  /* ---- games ---- */

  function showGames(games) {
    const placeholder = gameSelect.querySelector('option[value=""]');
    gameSelect.textContent = '';
    gameSelect.appendChild(placeholder);
    games.forEach(function (game) {
      const option = document.createElement('option');
      option.value = game.key;
      option.textContent = game.name;
      option.setAttribute('data-intro', game.intro || '');
      gameSelect.appendChild(option);
    });
  }

  function showIntro() {
    const option = gameSelect.selectedOptions[0];
    const intro = option ? option.getAttribute('data-intro') || '' : '';
    introEl.textContent = intro;
    introEl.hidden = !intro;
  }

  /* ---- teams ---- */

  function teamRows() { return teamsEl.querySelectorAll('.team-row'); }

  function renumberTeams() {
    const rows = teamRows();
    rows.forEach(function (row, i) {
      row.querySelector('.team-row__title').textContent = 'Team ' + (i + 1);
      row.querySelector('.team-row__remove').hidden = rows.length === 1;
    });
    addTeam.hidden = rows.length >= maxTeams;
  }

  function appendTeam() {
    if (teamRows().length >= maxTeams) return null;
    const row = teamTemplate.cloneNode(true);
    teamsEl.appendChild(row);
    renumberTeams();
    return row;
  }

  function resetTeams() {
    const rows = teamRows();
    for (let i = rows.length - 1; i > 0; i--) rows[i].remove();
    renumberTeams();
  }

  /* ---- errors ---- */

  function clearErrors() {
    form.querySelectorAll('.field-error').forEach(function (el) { el.remove(); });
    form.querySelectorAll('[aria-invalid]').forEach(function (el) {
      el.removeAttribute('aria-invalid');
      el.removeAttribute('aria-describedby');
    });
  }

  /* Maps a server field ("contact_email", "teams.1.key") onto its control, or null. */
  function controlFor(field) {
    const team = /^teams\.(\d+)\.(name|key|participants)$/.exec(field);
    if (team) {
      const row = teamRows()[parseInt(team[1], 10)];
      return row ? row.querySelector('[name="team_' + team[2] + '"]') : null;
    }
    return SINGLE_FIELDS.indexOf(field) === -1 ? null : form.elements[field];
  }

  let errorSeq = 0;

  function showFieldError(control, message) {
    const note = document.createElement('span');
    note.className = 'field-error';
    note.id = 'request-error-' + (++errorSeq);
    note.textContent = message;
    control.closest('label').appendChild(note);
    control.setAttribute('aria-invalid', 'true');
    control.setAttribute('aria-describedby', note.id);
  }

  function showErrors(errors, summary) {
    const general = [];
    let first = null;
    errors.forEach(function (error) {
      const control = controlFor(error.field);
      if (control) {
        showFieldError(control, error.message);
        first = first || control;
      } else {
        general.push(error.message);
      }
    });
    setStatus(general.concat(first ? [summary] : []).join(' ') || summary, 'error');
    if (first) first.focus();
  }

  /* ---- submit ---- */

  function value(name) {
    const text = form.elements[name].value.trim();
    return text === '' ? null : text;
  }

  function collectTeams() {
    return Array.prototype.map.call(teamRows(), function (row) {
      const participants = row.querySelector('[name="team_participants"]').value.trim();
      return {
        name: row.querySelector('[name="team_name"]').value.trim(),
        key: row.querySelector('[name="team_key"]').value.trim(),
        participants: participants === '' ? null : Number(participants),
      };
    });
  }

  function payload(challenge, number) {
    return {
      game_key: gameSelect.value,
      play_date: form.elements.play_date.value,
      teams: collectTeams(),
      contact_name: form.elements.contact_name.value.trim(),
      contact_email: value('contact_email'),
      contact_phone: value('contact_phone'),
      message: value('message'),
      terms_accepted: true,
      terms_version: termsVersion,
      website: form.elements.website.value,
      altcha: {
        algorithm: challenge.algorithm,
        challenge: challenge.challenge,
        maxnumber: challenge.maxnumber,
        salt: challenge.salt,
        signature: challenge.signature,
        number: number,
      },
    };
  }

  async function readJson(response) {
    try { return await response.json(); } catch (e) { return null; }
  }

  async function post(body) {
    return fetch(api + '/api/public/requests', {
      method: 'POST',
      credentials: 'omit',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  async function send() {
    let challenge = current;
    if (!challenge || !freshEnough(challenge)) challenge = await fetchChallenge();
    const number = await challenge.solution;
    if (number === null) {
      await refreshChallenge();
      return setStatus('We could not complete the automatic check. Please try again.', 'error');
    }
    const wait = challenge.data.min_fill_seconds * 1000 - (performance.now() - challenge.receivedAt);
    if (wait > 0) await sleep(wait);

    const response = await post(payload(challenge.data, number));
    if (response.status === 201) {
      form.reset();
      resetTeams();
      showIntro();
      clearErrors();
      await refreshChallenge();
      return setStatus("Thank you. We'll be in touch.", 'ok');
    }
    const body = await readJson(response);
    if (response.status === 503 && body && body.detail === 'not_accepting') {
      return setStatus("We're not taking requests right now. Please try again later.", 'error');
    }
    if (response.status >= 400 && response.status < 500) await refreshChallenge();
    if (response.status === 413) {
      return setStatus('Your request is too long. Please shorten the message and try again.', 'error');
    }
    if ((response.status === 422 || response.status === 409) && body && Array.isArray(body.errors)) {
      return showErrors(body.errors, response.status === 409
        ? 'Please check the highlighted field.'
        : 'Please check the highlighted fields and send the request again.');
    }
    return setStatus('Something went wrong. Please try again in a moment.', 'error');
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    if (busy) return;
    busy = true;
    submit.disabled = true;
    submit.textContent = 'Checking…';
    clearErrors();
    setStatus('', '');
    try {
      await send();
    } catch (e) {
      setStatus('Something went wrong. Please try again in a moment.', 'error');
    } finally {
      busy = false;
      submit.disabled = false;
      submit.textContent = submitLabel;
    }
  });

  gameSelect.addEventListener('change', showIntro);
  addTeam.addEventListener('click', function () {
    const row = appendTeam();
    if (row) row.querySelector('[name="team_name"]').focus();
  });
  teamsEl.addEventListener('click', function (event) {
    const remove = event.target.closest('.team-row__remove');
    if (!remove) return;
    remove.closest('.team-row').remove();
    renumberTeams();
  });

  /* ---- start: games first; with none, or on any failure, the no-JS line stays ---- */

  getJson('/api/public/games').then(function (games) {
    if (!Array.isArray(games) || games.length === 0) return;
    showGames(games);
    renumberTeams();
    form.hidden = false;
    fallback.hidden = true;
    return fetchChallenge().catch(function () {});     // submit fetches again if this failed
  }).catch(function () {});
})();
