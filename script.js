function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const override = params.get("api");
  if (override) {
    return override.replace(/\/$/, "");
  }

  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000/api";
  }

  return `${window.location.origin}/api`;
}

const API = resolveApiBase();
const DOCS_URL = API.replace(/\/api$/, "/docs");
const out = document.getElementById("output");
const btn = document.getElementById("generateBtn");
const btnText = document.getElementById("btnText");
document.getElementById("docsLink").href = DOCS_URL;

let selectedLang = "en";
let selectedQuizCount = 5;
let currentResult = null;
let quizState = {};

async function apiFetch(path, options) {
  try {
    return await fetch(`${API}${path}`, options);
  } catch (error) {
    throw new Error(`Cannot reach the backend at ${API}. Start the FastAPI server, or pass a different base URL with ?api=https://host/api.`);
  }
}

// ---------- Chip handlers ----------
function bindChipGroup(selector, onSelect) {
  document.querySelectorAll(selector).forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(selector).forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      onSelect(chip);
    });
  });
}
bindChipGroup("#langChips .chip-toggle", c => {
  selectedLang = c.dataset.lang;
  if (currentResult) renderResults();
});
bindChipGroup("#quizChips .chip-toggle", c => {
  selectedQuizCount = parseInt(c.dataset.q);
});

// ---------- Step Indicator ----------
function setStep(stage) {
  // stage: 1 (idle), 2 (generating), 3 (done)
  const s1 = document.getElementById("step-1");
  const s2 = document.getElementById("step-2");
  const s3 = document.getElementById("step-3");
  const c1 = document.getElementById("conn-1");
  const c2 = document.getElementById("conn-2");

  [s1,s2,s3].forEach(el => {
    el.classList.remove("bg-gradient-to-br","from-pink-500","via-purple-500","to-blue-500","text-white","shadow-lg","shadow-purple-300","ring-4","ring-white");
    el.classList.add("bg-white","text-slate-400","ring-2","ring-slate-200","shadow-md");
  });
  [c1,c2].forEach(el => el.classList.remove("active"));

  const activate = (el) => {
    el.classList.remove("bg-white","text-slate-400","ring-2","ring-slate-200","shadow-md");
    el.classList.add("bg-gradient-to-br","from-pink-500","via-purple-500","to-blue-500","text-white","shadow-lg","shadow-purple-300","ring-4","ring-white");
  };

  if (stage >= 1) activate(s1);
  if (stage >= 2) { c1.classList.add("active"); activate(s2); }
  if (stage >= 3) { c2.classList.add("active"); activate(s3); }
}

// ---------- Generate Flow ----------
async function generate() {
  btn.disabled = true;
  btnText.innerHTML = `<div class="dot-loader"><span></span><span></span><span></span></div> <span>Generating...</span>`;
  out.innerHTML = "";
  quizState = {};
  setStep(2);
  renderSkeletonLoader();

  try {
    updateLoadingMsg("📤 Uploading your notes...");
    const upload = await apiFetch(`/upload-notes`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        title: document.getElementById("title").value || "Untitled",
        raw_text: document.getElementById("notes").value
      })
    });
    if (!upload.ok) throw new Error("Upload failed");
    const uploadJson = await upload.json();

    updateLoadingMsg("🧠 AI is analyzing your notes...");
    const gen = await apiFetch(`/generate-content`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        note_id: uploadJson.note_id,
        num_quizzes: selectedQuizCount,
        languages: ["en", "hi", "hinglish"]
      })
    });
    if (!gen.ok) throw new Error("Generation failed");
    const genJson = await gen.json();

    let result;
    const stages = [
      "📚 Extracting key concepts...",
      "🎬 Designing animated scenes...",
      "❓ Crafting interactive quizzes...",
      "🌐 Translating to multiple languages...",
      "✅ Validating lesson quality..."
    ];
    for (let i = 0; i < 40; i++) {
      await new Promise(r => setTimeout(r, 1500));
      const r2 = await apiFetch(`/results/${genJson.generated_content_id}`);
      if (!r2.ok) throw new Error(`Results request failed (${r2.status})`);
      result = await r2.json();
      updateLoadingMsg(stages[Math.min(i, stages.length - 1)]);
      if (result.status === "completed" || result.status === "failed") break;
    }

    if (result.status === "completed") {
      currentResult = result;
      setStep(3);
      renderResults();
    } else {
      setStep(1);
      renderError(result.error_message || "Unknown error");
    }
  } catch (e) {
    setStep(1);
    renderError(e.message);
  } finally {
    btn.disabled = false;
    btnText.innerHTML = `<span>✨</span><span>Generate AI Lesson</span><span>→</span>`;
  }
}

// ---------- Skeleton loader ----------
function renderSkeletonLoader() {
  out.innerHTML = `
    <div class="glass rounded-3xl p-8 shadow-2xl shadow-purple-200/50 animate-scale-in">
      <div class="flex items-center gap-4 mb-6">
        <div class="w-12 h-12 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 animate-pulse-slow flex items-center justify-center text-white">
          <div class="dot-loader"><span></span><span></span><span></span></div>
        </div>
        <div class="flex-1">
          <div id="loadingMsg" class="font-bold text-slate-700">Starting up the AI...</div>
          <div class="text-xs text-slate-500 font-semibold mt-1">This usually takes 10–20 seconds</div>
        </div>
      </div>
      <div class="space-y-3">
        <div class="skeleton h-4 rounded-lg w-3/4"></div>
        <div class="skeleton h-4 rounded-lg w-full"></div>
        <div class="skeleton h-4 rounded-lg w-5/6"></div>
        <div class="grid grid-cols-3 gap-3 mt-6">
          <div class="skeleton h-24 rounded-2xl"></div>
          <div class="skeleton h-24 rounded-2xl"></div>
          <div class="skeleton h-24 rounded-2xl"></div>
        </div>
      </div>
    </div>
  `;
}
function updateLoadingMsg(msg) {
  const el = document.getElementById("loadingMsg");
  if (el) el.textContent = msg;
}

function renderError(msg) {
  out.innerHTML = `
    <div class="bg-white rounded-3xl p-8 shadow-xl border border-red-200 animate-scale-in">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-2xl">😅</div>
        <div>
          <div class="font-bold text-red-600 text-lg">Oops! Something went wrong</div>
          <div class="text-sm text-slate-600 mt-1">${msg}</div>
          <button onclick="generate()" class="mt-3 px-4 py-2 bg-red-500 text-white rounded-xl text-sm font-bold hover:scale-105 transition">
            Retry
          </button>
        </div>
      </div>
    </div>
  `;
}

// ---------- Main Render ----------
function renderResults() {
  const r = currentResult;
  const bundle = (r.translations || []).find(t => t.language === selectedLang);
  const concepts = bundle?.concepts || r.concepts || [];
  const quizzes  = bundle?.quizzes  || r.quizzes  || [];
  const scenes   = r.scene_plan || [];

  const langLabel = {en: "English", hi: "हिंदी", hinglish: "Hinglish"}[selectedLang];
  const qualityScore = Math.round((r.validation_report?.score || 0) * 100);

  out.innerHTML = `
    <!-- Success Banner -->
    <div class="glass rounded-3xl p-6 shadow-xl mb-6 animate-fade-up border border-green-200/50">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-white text-2xl shadow-lg shadow-green-200">✓</div>
          <div>
            <div class="font-display font-bold text-lg text-slate-800">Lesson Ready!</div>
            <div class="text-sm text-slate-600 font-semibold">Viewing in <b class="text-purple-600">${langLabel}</b> · Switch language anytime above ↑</div>
          </div>
        </div>
        <div class="px-4 py-2 rounded-full bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 font-bold text-sm">
          🎯 Quality: ${qualityScore}%
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 animate-fade-up" style="animation-delay: 0.1s">
      ${statCard("stat-pink",   "stat-icon-pink",   "📚", concepts.length, "Concepts")}
      ${statCard("stat-purple", "stat-icon-purple", "🎬", scenes.length,   "Scenes")}
      ${statCard("stat-blue",   "stat-icon-blue",   "❓", quizzes.length,  "Quizzes")}
      ${statCard("stat-cyan",   "stat-icon-cyan",   "⚡", qualityScore+"%", "Quality")}
    </div>

    <!-- Tab Navigation -->
    <div class="glass rounded-full p-1.5 shadow-lg mb-6 flex gap-1 animate-fade-up" style="animation-delay: 0.15s">
      ${tabBtn("concepts", "📚 Concepts", true)}
      ${tabBtn("scenes",   "🎬 Scenes",   false)}
      ${tabBtn("quizzes",  "🎯 Quiz Time", false)}
    </div>

    <!-- Tab Panels -->
    <div id="tab-concepts" class="tab-panel animate-fade-up">${renderConcepts(concepts)}</div>
    <div id="tab-scenes"   class="tab-panel hidden">${renderScenes(scenes)}</div>
    <div id="tab-quizzes"  class="tab-panel hidden">${renderQuizzes(quizzes)}</div>
  `;

  // Tabs
  document.querySelectorAll("[data-tab]").forEach(t => {
    t.addEventListener("click", () => {
      document.querySelectorAll("[data-tab]").forEach(x => {
        x.classList.remove("bg-gradient-to-r","from-pink-500","via-purple-500","to-blue-500","text-white","shadow-lg");
        x.classList.add("text-slate-600");
      });
      t.classList.add("bg-gradient-to-r","from-pink-500","via-purple-500","to-blue-500","text-white","shadow-lg");
      t.classList.remove("text-slate-600");
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
      const panel = document.getElementById("tab-" + t.dataset.tab);
      panel.classList.remove("hidden");
      panel.classList.remove("animate-fade-up");
      void panel.offsetWidth;
      panel.classList.add("animate-fade-up");
    });
  });

  // Init scenes
  scenes.forEach((s, i) => initScenePlayer(i, s));
  // Init quizzes
  quizzes.forEach((q, i) => { quizState[i] = { answered: false, correct: q.correct_index, explanation: q.explanation }; });
}

// ---------- Components ----------
function statCard(bg, icon, emoji, value, label) {
  return `
    <div class="rounded-2xl ${bg} p-5 shadow-md hover:shadow-xl transition-all hover:-translate-y-1 cursor-default group">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 rounded-2xl ${icon} flex items-center justify-center text-2xl shadow-md group-hover:scale-110 transition-transform">${emoji}</div>
        <div>
          <div class="text-3xl font-display font-black text-slate-800">${value}</div>
          <div class="text-xs font-bold text-slate-600 uppercase tracking-wider">${label}</div>
        </div>
      </div>
    </div>
  `;
}

function tabBtn(key, label, active) {
  const activeCls = active
    ? "bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 text-white shadow-lg"
    : "text-slate-600";
  return `<button data-tab="${key}" class="flex-1 py-2.5 px-4 rounded-full font-bold text-sm transition-all ${activeCls}">${label}</button>`;
}

function renderConcepts(concepts) {
  if (!concepts.length) return emptyState("No concepts found", "🔍");
  return `<div class="grid grid-cols-1 md:grid-cols-2 gap-4">` + concepts.map((c, i) => `
    <div class="bg-white rounded-3xl p-6 shadow-md card-hover border border-white animate-fade-up" style="animation-delay: ${i*0.05}s">
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex items-center gap-2">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white font-bold text-sm shadow-md">C${i+1}</div>
          <h3 class="font-display font-bold text-lg text-slate-800">${c.title || ''}</h3>
        </div>
        <span class="diff-${c.difficulty || 'medium'} px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">${c.difficulty || 'medium'}</span>
      </div>
      <p class="text-slate-600 leading-relaxed mb-4">${c.summary || ''}</p>
      <div class="flex flex-wrap gap-2">
        ${(c.keywords || []).map(k => `<span class="px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-100">#${k}</span>`).join("")}
      </div>
    </div>
  `).join("") + `</div>`;
}

function normalizeImageQuery(text) {
  return (text || "learning topic")
    .replace(/[^a-zA-Z0-9\s-]/g, " ")
    .trim()
    .split(/\s+/)
    .slice(0, 10)
    .join(" ");
}

function hashCode(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = ((hash << 5) - hash) + text.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function sceneImageUrl(scene, step) {
  const base = normalizeImageQuery(`${scene?.title || "education"} ${step?.narration || ""}`);
  const sig = hashCode(`${scene?.scene_id || scene?.title || "scene"}-${step?.step_id || 0}`) % 1000;
  return `https://image.pollinations.ai/prompt/${encodeURIComponent(base)}?width=1600&height=900&nologo=true`;
}

function updateSceneImage(idx, scene, step) {
  const img = document.getElementById(`scene-img-${idx}`);
  if (!img) return;
  const next = sceneImageUrl(scene, step);
  if (img.dataset.src === next) return;
  img.classList.remove("loaded");
  img.dataset.src = next;
  img.classList.remove("hidden-image");
  img.onload = () => {
    img.classList.add("loaded");
  };
  img.src = next;
}

function handleSceneImageError(idx) {
  const img = document.getElementById(`scene-img-${idx}`);
  if (!img) return;
  img.classList.add("hidden-image");
}

function renderScenes(scenes) {
  if (!scenes.length) return emptyState("No scenes generated", "🎬");
  return `<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">` + scenes.map((s, i) => `
    <div id="scene-${i}" class="scene-video card-hover animate-fade-up" style="animation-delay: ${i*0.08}s">
      <img id="scene-img-${i}" class="scene-topic-image" src="${sceneImageUrl(s)}" alt="Scene topic image" loading="lazy" referrerpolicy="no-referrer" onerror="handleSceneImageError(${i})" />
      <div class="scene-image-overlay"></div>

      <div class="play-overlay absolute inset-0 flex items-center justify-center z-20">
        <button 
          onclick="playScene(${i})"
          class="w-16 h-16 rounded-full bg-white/30 backdrop-blur-md flex items-center justify-center text-white text-2xl shadow-xl hover:scale-110 transition-all">
          ▶
        </button>
      </div>

      <!-- Top bar -->
      <div class="flex items-center justify-between px-5 pt-4 text-white/90">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-red-400 animate-pulse"></div>
          <span class="text-xs font-bold uppercase tracking-widest">AI Generated · Scene ${i+1}</span>
        </div>
        <span class="text-xs font-bold bg-white/10 backdrop-blur-sm px-2 py-1 rounded-lg">${s.steps.length} steps</span>
      </div>

      <!-- Stage -->
      <div class="px-6 py-10 min-h-[260px] flex flex-col items-center justify-center text-center text-white relative">
        <div id="visual-${i}" class="text-7xl mb-4 transition-all duration-500 animate-bounce-slow drop-shadow-2xl">🎞️</div>
        <div id="narration-${i}" class="text-lg font-semibold leading-relaxed max-w-md px-4 text-white/95">
          ${s.title}
        </div>
        <div id="start-hint-${i}" class="text-xs mt-3 px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm text-white/80 font-bold transition-all duration-300">
          ✨ Tap play to explore scene
        </div>
        <div id="hint-${i}" class="text-xs mt-3 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm text-white/80 font-bold uppercase tracking-wider hidden"></div>
      </div>

      <!-- Controls -->
      <div class="flex items-center gap-3 px-5 py-4 bg-black/20 backdrop-blur-sm">
        <button onclick="prevStep(${i})" class="text-white hover:text-pink-300 transition-transform hover:scale-110 text-xl font-bold">⏮</button>
        <button id="play-${i}" onclick="toggleScene(${i})"
          class="w-12 h-12 rounded-full bg-white text-purple-600 flex items-center justify-center shadow-lg hover:scale-110 transition-transform text-lg font-bold">▶</button>
        <button onclick="nextStep(${i}, true)" class="text-white hover:text-pink-300 transition-transform hover:scale-110 text-xl font-bold">⏭</button>
        <div class="flex-1 ml-2">
          <div class="text-xs font-bold text-white/80 mb-1" id="step-title-${i}">${s.title}</div>
          <div class="h-2 bg-white/20 rounded-full overflow-hidden">
            <div id="progress-${i}" class="h-full bg-gradient-to-r from-pink-300 via-purple-300 to-blue-300 rounded-full transition-all duration-300" style="width: 0%"></div>
          </div>
        </div>
        <div id="step-info-${i}" class="text-xs font-bold text-white/90 min-w-[40px] text-right">0/${s.steps.length}</div>
      </div>
    </div>
  `).join("") + `</div>`;
}

// ---------- Scene Player ----------
const scenePlayers = {};
function initScenePlayer(idx, scene) {
  scenePlayers[idx] = { scene, current: -1, playing: false, timer: null };
  updateSceneImage(idx, scene, scene.steps?.[0]);
}

function getSmartEmoji(text) {
  if (!text) return "🎬";
  const lower = text.toLowerCase();
  if (lower.includes('water') || lower.includes('liquid') || lower.includes('cycle')) return "💧";
  if (lower.includes('sun') || lower.includes('heat') || lower.includes('energy')) return "☀️";
  if (lower.includes('plant') || lower.includes('tree') || lower.includes('leaf')) return "🌱";
  if (lower.includes('animal') || lower.includes('dog') || lower.includes('cat')) return "🐾";
  if (lower.includes('space') || lower.includes('star') || lower.includes('planet')) return "🌌";
  if (lower.includes('brain') || lower.includes('think') || lower.includes('mind')) return "🧠";
  if (lower.includes('history') || lower.includes('time') || lower.includes('past')) return "⏳";
  if (lower.includes('math') || lower.includes('number') || lower.includes('calculate')) return "🔢";
  if (lower.includes('science') || lower.includes('experiment') || lower.includes('lab')) return "🔬";
  if (lower.includes('cloud') || lower.includes('vapor')) return "☁️";
  if (lower.includes('rain') || lower.includes('drop')) return "🌧️";
  if (lower.includes('river') || lower.includes('ocean')) return "🌊";
  if (lower.includes('ice') || lower.includes('snow') || lower.includes('freeze')) return "❄️";
  
  // Default fallback by extracting any emoji in the text
  const found = text.match(/\p{Emoji}/gu);
  return found ? found.join("") : "🎬";
}

function toggleScene(idx) {
  const p = scenePlayers[idx];
  if (p.playing) pauseScene(idx);
  else playScene(idx);
}
function playScene(idx) {
  const p = scenePlayers[idx];
  document.querySelector(`#scene-${idx} .play-overlay`)?.classList.add("hidden");
  document.getElementById(`start-hint-${idx}`)?.classList.add("hidden");
  p.playing = true;
  document.getElementById(`play-${idx}`).innerHTML = "⏸";
  if (p.current >= p.scene.steps.length - 1) p.current = -1;
  nextStep(idx);
}
function pauseScene(idx) {
  const p = scenePlayers[idx];
  p.playing = false;
  document.getElementById(`play-${idx}`).innerHTML = "▶";
  clearTimeout(p.timer);
}
function prevStep(idx) {
  const p = scenePlayers[idx];
  pauseScene(idx);
  if (p.current > 0) {
    p.current--;
    updateStepUI(idx);
  }
}
function nextStep(idx, manual = false) {
  const p = scenePlayers[idx];
  if (manual) pauseScene(idx);
  p.current++;
  if (p.current >= p.scene.steps.length) { pauseScene(idx); return; }
  updateStepUI(idx);
  
  if (!manual && p.playing) {
    const step = p.scene.steps[p.current];
    p.timer = setTimeout(() => { if (p.playing) nextStep(idx); }, (step.duration_sec || 4) * 1000);
  }
}
function updateStepUI(idx) {
  const p = scenePlayers[idx];
  const step = p.scene.steps[p.current];
  const visual = document.getElementById(`visual-${idx}`);
  const narration = document.getElementById(`narration-${idx}`);
  const progress = document.getElementById(`progress-${idx}`);
  const stepInfo = document.getElementById(`step-info-${idx}`);
  const hint = document.getElementById(`hint-${idx}`);

  const emojis = getSmartEmoji(step.narration + " " + (step.visual || ""));
  
  // Custom Animations based on the AI's hint!
  const animHint = (step.animation_hint || "fade-in").toLowerCase();
  
  // Pre-animation state
  visual.style.transition = "none";
  if (animHint.includes("zoom") || animHint.includes("grow")) {
    visual.style.transform = "scale(0.1)";
    visual.style.opacity = "0";
  } else if (animHint.includes("slide") || animHint.includes("move")) {
    visual.style.transform = "translateX(-100px)";
    visual.style.opacity = "0";
  } else if (animHint.includes("draw")) {
    visual.style.transform = "scale(0.8) rotate(-15deg)";
    visual.style.opacity = "0";
  } else if (animHint.includes("drop") || animHint.includes("fall")) {
    visual.style.transform = "translateY(-100px)";
    visual.style.opacity = "0";
  } else {
    // Default fade
    visual.style.transform = "scale(0.9)";
    visual.style.opacity = "0";
  }

  // Force reflow
  void visual.offsetWidth;

  // Post-animation state
  visual.style.transition = "all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)";
  setTimeout(() => {
    visual.textContent = emojis;
    visual.style.transform = "translate(0, 0) scale(1) rotate(0deg)";
    visual.style.opacity = "1";
    
    // Add continuous bounce if it's supposed to hover/float
    if (animHint.includes("float") || animHint.includes("hover")) {
      visual.classList.add("animate-bounce-slow");
    } else {
      visual.classList.remove("animate-bounce-slow");
    }
  }, 50);

  narration.style.opacity = "0";
  setTimeout(() => {
    narration.textContent = step.narration;
    narration.style.opacity = "1";
  }, 250);

  // Animation hint tags are hidden/removed completely per user feedback
  hint.classList.add("hidden");

  updateSceneImage(idx, p.scene, step);

  progress.style.width = ((p.current + 1) / p.scene.steps.length * 100) + "%";
  stepInfo.textContent = `${p.current + 1}/${p.scene.steps.length}`;
}

// ---------- Quiz ----------
function renderQuizzes(quizzes) {
  if (!quizzes.length) return emptyState("No quizzes generated", "❓");
  return `
    <div class="mb-4 text-center">
      <p class="text-slate-600 font-semibold">Click an answer to see if you're right! 🎯</p>
    </div>
    <div class="grid grid-cols-1 gap-5">
    ${quizzes.map((q, i) => `
      <div id="quiz-${i}" class="bg-white rounded-3xl p-6 shadow-md border border-white card-hover animate-fade-up" style="animation-delay: ${i*0.05}s">
        <div class="flex items-start justify-between gap-3 mb-5">
          <div class="flex items-start gap-3 flex-1">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 via-purple-500 to-blue-500 text-white flex items-center justify-center font-display font-bold text-sm shadow-md flex-shrink-0">Q${i+1}</div>
            <h3 class="font-display font-bold text-lg text-slate-800 mt-1">${q.question}</h3>
          </div>
          <span class="diff-${q.difficulty || 'medium'} px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide flex-shrink-0">${q.difficulty || 'medium'}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          ${(q.options || []).map((opt, j) => `
            <div class="quiz-opt cursor-pointer flex items-center gap-3 p-4 rounded-2xl bg-slate-50 border-2 border-slate-100" data-q="${i}" data-opt="${j}" onclick="answerQuiz(${i}, ${j})">
              <div class="w-9 h-9 rounded-xl bg-white border-2 border-slate-200 flex items-center justify-center font-display font-bold text-sm text-slate-600 flex-shrink-0">${String.fromCharCode(65+j)}</div>
              <div class="font-semibold text-slate-700 text-sm">${opt}</div>
            </div>
          `).join("")}
        </div>
        <div id="explanation-${i}"></div>
      </div>
    `).join("")}
    </div>
  `;
}

function answerQuiz(qIdx, optIdx) {
  const s = quizState[qIdx];
  if (!s || s.answered) return;
  s.answered = true;

  const opts = document.querySelectorAll(`#quiz-${qIdx} .quiz-opt`);
  opts.forEach(o => {
    o.classList.add("disabled");
    o.onclick = null;
    o.classList.remove("cursor-pointer");
  });

  const correctIdx = s.correct;
  const chosen = opts[optIdx];
  const correct = opts[correctIdx];

  if (optIdx === correctIdx) {
    chosen.classList.remove("bg-slate-50","border-slate-100");
    chosen.classList.add("bg-gradient-to-r","from-green-100","to-emerald-100","border-green-400");
    chosen.querySelector(".w-9").classList.remove("bg-white","border-slate-200","text-slate-600");
    chosen.querySelector(".w-9").classList.add("bg-green-500","border-green-500","text-white");
    chosen.insertAdjacentHTML("beforeend", `<span class="ml-auto text-green-600 text-xl font-bold">✓</span>`);
  } else {
    chosen.classList.remove("bg-slate-50","border-slate-100");
    chosen.classList.add("bg-gradient-to-r","from-red-100","to-pink-100","border-red-400");
    chosen.querySelector(".w-9").classList.remove("bg-white","border-slate-200","text-slate-600");
    chosen.querySelector(".w-9").classList.add("bg-red-500","border-red-500","text-white");
    chosen.insertAdjacentHTML("beforeend", `<span class="ml-auto text-red-600 text-xl font-bold">✗</span>`);
    correct.classList.remove("bg-slate-50","border-slate-100");
    correct.classList.add("bg-gradient-to-r","from-green-100","to-emerald-100","border-green-400");
    correct.querySelector(".w-9").classList.remove("bg-white","border-slate-200","text-slate-600");
    correct.querySelector(".w-9").classList.add("bg-green-500","border-green-500","text-white");
    correct.insertAdjacentHTML("beforeend", `<span class="ml-auto text-green-600 text-xl font-bold">✓</span>`);
  }

  const isCorrect = optIdx === correctIdx;
  document.getElementById(`explanation-${qIdx}`).innerHTML = `
    <div class="mt-4 p-4 rounded-2xl ${isCorrect ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-400' : 'bg-gradient-to-r from-amber-50 to-orange-50 border-l-4 border-amber-400'} animate-scale-in">
      <div class="flex items-start gap-3">
        <div class="text-2xl">${isCorrect ? '🎉' : '💡'}</div>
        <div>
          <div class="font-display font-bold ${isCorrect ? 'text-green-700' : 'text-amber-700'} mb-1">${isCorrect ? 'Correct! Great job!' : "Not quite - here's the explanation:"}</div>
          <div class="text-sm text-slate-700 leading-relaxed">${s.explanation || ''}</div>
        </div>
      </div>
    </div>
  `;
}

function emptyState(msg, icon) {
  return `
    <div class="glass rounded-3xl p-12 text-center">
      <div class="text-6xl mb-4 opacity-40">${icon}</div>
      <div class="text-slate-500 font-bold">${msg}</div>
    </div>
  `;
}

// ---------- Keyboard Controls ----------
document.addEventListener('keydown', (e) => {
  if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

  const tabScenes = document.getElementById('tab-scenes');
  if (!tabScenes || tabScenes.classList.contains('hidden')) return;

  const activeSceneIds = Object.keys(scenePlayers).filter(id => {
      const el = document.getElementById(`scene-${id}`);
      return el;
  });

  if (activeSceneIds.length > 0) {
      let idx = activeSceneIds[0];
      const hovered = document.querySelector('.scene-video:hover');
      if (hovered) {
          idx = hovered.id.replace('scene-', '');
      }
      
      if (e.code === 'Space') {
          e.preventDefault();
          toggleScene(idx);
      } else if (e.code === 'ArrowRight') {
          e.preventDefault();
          nextStep(idx, true);
      } else if (e.code === 'ArrowLeft') {
          e.preventDefault();
          prevStep(idx);
      }
  }
});
