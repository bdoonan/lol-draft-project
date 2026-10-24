//page behaviour for the home page (countdown) and the play pages
//on a play page the server sends the game state, this file draws it and sends guesses back without reloading
(function () {
  'use strict';

  const STATS_KEY = 'lolStats';
  //keys from the old single game stats formats, moved aside so they don't mix with per game stats
  const OLD_KEYS = ['streak', 'numGames', 'wins', 'failures', 'attempts1', 'attempts2', 'attempts3',
                    'attempts4', 'attempts5', 'done', 'completed'];
  const $ = id => document.getElementById(id);

  let state, yearPicker, eventPicker, teamPicker, chart, countdownTimer;

  //localStorage can throw in private windows or with blocked site data
  function storage() {
    try { return window.localStorage; } catch (e) { return null; }
  }

  function pretty(name) {
    return name.replace(/_/g, ' ');
  }

  //---------- searchable dropdowns (falls back to the plain select if Tom Select didn't load) ----------
  function picker(id) {
    const el = $(id);
    const ts = window.TomSelect ? new TomSelect(el, { maxOptions: null, create: false }) : null;
    return {
      setPlaceholder: text => {
        el.setAttribute('placeholder', text);
        if (ts) {
          ts.settings.placeholder = text;
          ts.control_input.placeholder = text;
        }
      },
      value: () => (ts ? ts.getValue() : el.value),
      clear: () => (ts ? ts.clear(true) : (el.value = '')),
      remove: value => {
        if (ts) ts.removeOption(value);
        else Array.from(el.options).filter(o => o.value === value).forEach(o => o.remove());
      },
      //takes plain strings or {value, text}, and keeps the current choice if it is still an option
      setOptions: items => {
        const current = ts ? ts.getValue() : el.value;
        const options = items.map(o => (typeof o === 'string' ? { value: o, text: o } : o));
        const keep = options.some(o => o.value === current) ? current : '';
        if (ts) {
          ts.clearOptions();
          ts.addOptions(options);
          ts.setValue(keep, true);
        } else {
          el.replaceChildren(new Option('', ''), ...options.map(o => new Option(o.text, o.value)));
          el.value = keep;
        }
      },
    };
  }

  //---------- server calls ----------
  async function post(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      //day the page was loaded for, so a guess made after the reset isn't applied to the new match
      body: JSON.stringify(Object.assign({ day: state.day }, body)),
    });
    const data = await res.json().catch(() => ({}));
    //the page is from before the daily reset, show the new matches instead
    if (data.newDay) {
      window.location.reload();
      throw new Error('New matches are out, loading them…');
    }
    if (!res.ok) throw new Error(data.error || 'Something went wrong, try again.');
    return data;
  }

  async function submitGuess(event) {
    event.preventDefault();
    let body;
    if (state.stage === 'year') {
      const year = yearPicker.value();
      if (!year) return setStatus('Pick a year first.');
      body = { year: Number(year) };
    } else if (state.stage === 'event') {
      const event = eventPicker.value();
      if (!event) return setStatus('Pick the event first.');
      body = { event: event };
    } else if (state.stage === 'blue' || state.stage === 'red') {
      const team = teamPicker.value();
      if (!team) return setStatus('Pick the ' + state.stage + ' side team first.');
      body = { team: team };
    } else {
      return;
    }
    const button = $('submit-btn');
    button.disabled = true;
    try {
      state = await post('/api/' + state.slug + '/guess', body);
      //the server only accepts each guess once, so these fire once per game
      if (state.guesses.length === 1) track('start-' + state.slug, 'Started ' + state.name);
      if (state.stage === 'won') {
        track('finish-' + state.slug + '-won-' + state.result.attempts,
              state.name + ' won in ' + state.result.attempts);
      } else if (state.stage === 'lost') {
        track('finish-' + state.slug + '-lost', state.name + ' lost');
      }
      setStatus('');
      yearPicker.clear();
      eventPicker.clear();
      teamPicker.clear();
      render();
    } catch (e) {
      setStatus(e.message);
    } finally {
      button.disabled = false;
    }
  }

  async function useHint(side) {
    try {
      state = await post('/api/' + state.slug + '/hint', { side: side });
      track('hint-' + state.slug + '-' + side, state.name + ' ' + side + ' hint');
      render();
    } catch (e) {
      setStatus(e.message);
    }
  }

  function setStatus(text) {
    $('status').textContent = text;
  }

  //---------- analytics ----------
  //sends a goatcounter event (shown in its dashboard as a path marked "event").
  //does nothing when analytics are off (no GOATCOUNTER_CODE) or the script is blocked
  function track(name, title) {
    try {
      if (window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({ path: name, title: title || name, event: true });
      }
    } catch (e) { /* never let analytics break the game */ }
  }

  //---------- drawing ----------
  function render() {
    const finished = state.stage === 'won' || state.stage === 'lost';
    const teamStage = state.stage === 'blue' || state.stage === 'red';
    let header = state.name + ' · ' + (state.year || '?');
    if (state.event) header += ' · ' + state.event;
    if (state.blueTeam) header += ' · ' + state.blueTeam + ' vs ?';
    $('tourney-name').textContent = finished ? pretty(state.result.tournament) : header;
    if (state.blueTeam) showTeam('blue', state.blueTeam, state.blueLogo);
    $('attempts').textContent = 'Attempts remaining: ' + state.attemptsLeft;
    $('year-picker').hidden = state.stage !== 'year';
    $('event-picker').hidden = state.stage !== 'event';
    $('team-picker').hidden = !teamStage;
    $('play-panel').hidden = finished;

    state.guesses.filter(g => g.kind === 'year').forEach(g => yearPicker.remove(g.cells[0].text));
    if (state.stage === 'event') {
      const triedEvents = new Set(state.guesses.filter(g => g.kind === 'event').map(g => g.cells[0].text));
      eventPicker.setOptions(state.events.filter(e => !triedEvents.has(e.text)));
    }
    if (teamStage) {
      //options are that tournament's teams, minus the confirmed blue team and anything already guessed for this side
      const tried = new Set(state.guesses.filter(g => g.kind === state.stage).map(g => g.cells[0].text));
      teamPicker.setOptions(state.teams.filter(t => t !== state.blueTeam && !tried.has(t)));
      teamPicker.setPlaceholder(state.stage === 'blue' ? 'Blue side team' : 'Red side team');
      $('team-picker').className = 'picker side-' + state.stage;
    }

    //hint buttons stay greyed out until a hint is earned (see HINT_AFTER in game.py)
    ['blue', 'red'].forEach(side => {
      const hint = state.hints[side];
      const button = $(side + 'hint');
      if (hint) showPlayer(side, hint.index, hint.name);
      button.hidden = Boolean(hint) || finished;
      button.disabled = state.hintsAvailable === 0;
      button.title = button.disabled
        ? 'Unlocks after ' + state.hintAfter + ' wrong guesses, then one more per wrong guess'
        : '';
    });

    renderHistory();
    if (finished) renderResult();
  }

  //fills the coloured team box above a side's picks, with the logo if one was downloaded
  function showTeam(side, name, logo) {
    const box = $(side + '-team-name');
    const label = document.createElement('span');
    label.textContent = name;
    if (logo) {
      const img = document.createElement('img');
      img.className = 'team-logo';
      img.src = logo;
      img.alt = '';
      img.onerror = () => img.remove();
      box.replaceChildren(img, label);
    } else {
      box.replaceChildren(label);
    }
  }

  function showPlayer(side, index, name) {
    const el = $(side + '-player-' + index);
    el.textContent = name;
    el.hidden = false;
  }

  function renderHistory() {
    $('guess-history').replaceChildren(...state.guesses.map(guess => {
      const row = document.createElement('div');
      row.className = 'guess-row';
      const label = document.createElement('span');
      label.className = 'side-label ' + guess.kind;
      label.textContent = { year: 'Year', event: 'Event', blue: 'Blue', red: 'Red' }[guess.kind];
      row.append(label);
      guess.cells.forEach(cell => {
        const span = document.createElement('span');
        span.className = cell.result;
        span.textContent = cell.text;
        if (cell.result === 'higher' || cell.result === 'lower') span.title = 'The answer is ' + cell.result;
        row.append(span);
      });
      return row;
    }));
  }

  function renderResult() {
    const result = state.result;
    const won = state.stage === 'won';
    $('result').hidden = false;
    showTeam('blue', result.blueTeam, result.blueLogo);
    showTeam('red', result.redTeam, result.redLogo);
    ['blue', 'red'].forEach(side => result.players[side].forEach((name, i) => showPlayer(side, i, name)));

    const banner = $('result-banner');
    banner.className = 'result-banner ' + (won ? 'won' : 'lost');
    banner.textContent = won
      ? 'Congratulations you got the correct answer in ' + result.attempts + ' attempt(s)'
      : 'Sorry you did not get the correct answer';

    const stats = recordResult();
    const rate = stats.numGames ? (stats.wins / stats.numGames * 100).toFixed(2) : '0.00';
    $('winratio').textContent = state.name + ' win rate: ' + stats.wins + '/' + stats.numGames + ' (' + rate + '%)';
    $('streak').textContent = 'Current streak: ' + stats.streak;
    drawChart(stats);
    renderVod(result);
    startCountdown(state.nextReset, state.serverNow);
  }

  //shows a thumbnail first and only loads youtube's player when clicked,
  //with a direct youtube link underneath in case the embedded player refuses to play
  function renderVod(result) {
    const box = $('vod-embed');
    if (box.childElementCount) return;
    $('vod').hidden = false;
    const vod = result.vod;
    if (!vod) {
      box.classList.add('vod-none');
      box.textContent = 'No VOD available for this match';
      return;
    }
    const play = document.createElement('button');
    play.type = 'button';
    play.className = 'vod-thumb';
    play.style.backgroundImage = 'url("' + vod.thumb + '")';
    play.setAttribute('aria-label', 'Play the VOD');
    play.addEventListener('click', () => {
      track('vod-play-' + state.slug, state.name + ' VOD played');
      const iframe = document.createElement('iframe');
      iframe.src = vod.embed;
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      iframe.allowFullscreen = true;
      box.replaceChildren(iframe);
    });
    box.append(play);

    const link = $('vod-watch');
    link.href = vod.watch;
    link.addEventListener('click', () => track('vod-youtube-' + state.slug, state.name + ' VOD on YouTube'));
    const s = vod.start;
    const at = s ? ' (starts at ' + Math.floor(s / 3600) + ':' + String(Math.floor(s / 60) % 60).padStart(2, '0') +
      ':' + String(s % 60).padStart(2, '0') + ')' : '';
    link.textContent = 'Watch on YouTube ↗' + at;
    link.hidden = false;
  }

  function drawChart(stats) {
    if (!window.Chart) return;
    if (chart) chart.destroy();
    Chart.defaults.color = '#fff';
    chart = new Chart($('myChart'), {
      type: 'bar',
      data: {
        labels: ['1', '2', '3', '4', '5', 'X'],
        datasets: [{
          data: stats.dist.concat(stats.failures),
          backgroundColor: ['green', 'green', 'green', 'green', 'green', 'red'],
        }],
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, title: { display: true, text: state.name + ' attempt history' } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  //counts down on the server's clock: offset corrects for a visitor's clock being minutes off
  function startCountdown(nextReset, serverNow) {
    if (countdownTimer) return;
    const target = Date.parse(nextReset);
    const offset = serverNow ? Date.parse(serverNow) - Date.now() : 0;
    const tick = () => {
      const left = target - (Date.now() + offset);
      if (left <= 0) {
        clearInterval(countdownTimer);
        window.location.reload();
        return;
      }
      const s = Math.floor(left / 1000);
      const pad = n => String(n).padStart(2, '0');
      $('countdown').textContent = 'Next matches in ' + pad(Math.floor(s / 3600)) + ':' +
        pad(Math.floor(s / 60) % 60) + ':' + pad(s % 60);
    };
    tick();
    countdownTimer = setInterval(tick, 1000);
  }

  //a tab left open in the background past the daily reset shows yesterday's matches,
  //so reload when it comes back into view after the reset
  function reloadWhenStale(nextReset, serverNow) {
    const target = Date.parse(nextReset);
    const offset = serverNow ? Date.parse(serverNow) - Date.now() : 0;
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && Date.now() + offset >= target) window.location.reload();
    });
  }

  //---------- stats per game (kept in this browser only) ----------
  //lolStats = {<slug>: {numGames, wins, streak, dist, failures, lastRecordedDay}}
  function loadAllStats() {
    const ls = storage();
    if (!ls) return {};
    try {
      const saved = JSON.parse(ls.getItem(STATS_KEY)) || {};
      //the single game version stored one stats object here, keep it aside instead of mixing it in
      if ('numGames' in saved) {
        ls.setItem(STATS_KEY + 'Legacy', JSON.stringify(saved));
        return {};
      }
      return saved;
    } catch (e) {
      return {};
    }
  }

  function saveAllStats(all) {
    const ls = storage();
    if (!ls) return;
    try {
      ls.setItem(STATS_KEY, JSON.stringify(all));
      OLD_KEYS.forEach(key => ls.removeItem(key));
    } catch (e) { /* storage full or blocked */ }
  }

  //counts each game once per day, so refreshing the finished page never adds another game
  function recordResult() {
    const all = loadAllStats();
    const stats = Object.assign(
      { numGames: 0, wins: 0, streak: 0, dist: [0, 0, 0, 0, 0], failures: 0, lastRecordedDay: null },
      all[state.slug]);
    if (stats.lastRecordedDay !== state.day) {
      stats.numGames++;
      if (state.stage === 'won') {
        stats.wins++;
        stats.streak++;
        stats.dist[Math.min(state.result.attempts, 5) - 1]++;
      } else {
        stats.failures++;
        stats.streak = 0;
      }
      stats.lastRecordedDay = state.day;
      all[state.slug] = stats;
      saveAllStats(all);
    }
    return stats;
  }

  //---------- board layout: draft order or roles ----------
  //only offered when the game has pick order data (2017 onward), the choice is remembered in this browser
  function setupBoardView() {
    const toggle = $('view-toggle');
    if (toggle.hidden) return;
    const ls = storage();
    const apply = view => {
      document.querySelectorAll('.pick').forEach(card => {
        card.style.order = view === 'draft' ? card.dataset.pick : Number(card.dataset.role) + 1;
      });
      toggle.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.view === view));
    };
    let view = 'draft';
    try { view = (ls && ls.getItem('boardView')) || 'draft'; } catch (e) { /* ignore */ }
    apply(view);
    toggle.addEventListener('click', event => {
      const button = event.target.closest('button[data-view]');
      if (!button) return;
      apply(button.dataset.view);
      try { if (ls) ls.setItem('boardView', button.dataset.view); } catch (e) { /* ignore */ }
    });
  }

  //---------- instructions modal ----------
  function setupModal() {
    const modal = $('instructionsModal');
    const close = () => {
      modal.style.display = 'none';
      const ls = storage();
      try { if (ls) ls.setItem('hasSeenInstructions', 'true'); } catch (e) { /* ignore */ }
    };
    const ls = storage();
    let seen = false;
    try { seen = Boolean(ls && ls.getItem('hasSeenInstructions')); } catch (e) { /* ignore */ }
    if (!seen) modal.style.display = 'block';
    document.querySelector('.close-modal').addEventListener('click', close);
    $('closeModalBtn').addEventListener('click', close);
    modal.addEventListener('click', event => { if (event.target === modal) close(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
    $('instructionsBtn').addEventListener('click', () => { modal.style.display = 'block'; });
  }

  //---------- start ----------
  setupModal();
  const stateEl = $('state');
  if (!stateEl) {
    //home page
    startCountdown($('countdown').dataset.nextReset, $('countdown').dataset.serverNow);
    reloadWhenStale($('countdown').dataset.nextReset, $('countdown').dataset.serverNow);
    return;
  }
  state = JSON.parse(stateEl.textContent);
  reloadWhenStale(state.nextReset, state.serverNow);
  //the first version kept guess history in sessionStorage, it is all on the server now
  try { window.sessionStorage.clear(); } catch (e) { /* ignore */ }
  yearPicker = picker('year-select');
  eventPicker = picker('event-select');
  teamPicker = picker('team-select');
  setupBoardView();
  $('guess-form').addEventListener('submit', submitGuess);
  $('bluehint').addEventListener('click', () => useHint('blue'));
  $('redhint').addEventListener('click', () => useHint('red'));
  render();
})();
