import json

with open('qa_data.json', 'r', encoding='utf-8') as f:
    qa = json.load(f)

categorized = []
for i, (q, a) in enumerate(qa, 1):
    ql = (q + ' ' + a).lower()
    cat = 'Architecture & Fundamentals'
    if 'lock' in ql or 'redis' in ql or 'lua' in ql or 'ttl' in ql:
        cat = 'Redis & Distributed Locking'
    elif 'idempotenc' in ql or 'tamper' in ql or 'sha-256' in ql or 'hash' in ql:
        cat = 'Idempotency & Deduplication'
    elif 'celery' in ql or 'worker' in ql or 'retry' in ql or 'jitter' in ql or 'prefetch' in ql or 'ack' in ql or 'dlq' in ql:
        cat = 'Celery Workers & Failure Semantics'
    elif 'postgres' in ql or 'index' in ql or 'transaction' in ql or 'outbox' in ql or 'model' in ql or 'fsm' in ql or 'uuid' in ql:
        cat = 'PostgreSQL & Database Design'
    elif 'jwt' in ql or 'token' in ql or 'auth' in ql or 'permission' in ql or 'rate limit' in ql or 'throttle' in ql:
        cat = 'Auth, Security & Rate Limiting'
    elif 'prometheus' in ql or 'grafana' in ql or 'metric' in ql or 'health' in ql or 'latency' in ql or 'correlation' in ql:
        cat = 'Observability & Monitoring'
    elif 'docker' in ql or 'aws' in ql or 'fargate' in ql or 'ecs' in ql or 'deploy' in ql:
        cat = 'Docker & Cloud Deployment'
    elif 'test' in ql or 'locust' in ql or 'pytest' in ql:
        cat = 'Testing & Load Simulation'
        
    categorized.append({
        'id': i,
        'category': cat,
        'question': q,
        'answer': a
    })

data_json = json.dumps(categorized)

template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SDE Interview Master Dashboard | Distributed Job Queue</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        code, pre { font-family: 'JetBrains Mono', monospace; }
        .perspective-1000 { perspective: 1000px; }
        .transform-style-3d { transform-style: preserve-3d; }
        .backface-hidden { backface-visibility: hidden; }
        .rotate-y-180 { transform: rotateY(180deg); }
        .card-flip { transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
        .flipped { transform: rotateY(180deg); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 9999px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

    <!-- Top Navigation Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold text-xl">
                    ⚡
                </div>
                <div>
                    <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                        Distributed Job Queue <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold">SDE Interview Mastery</span>
                    </h1>
                    <p class="text-xs text-slate-400">Interactive Anki-Style Learning Dashboard & Viva Simulator (200 Questions)</p>
                </div>
            </div>

            <!-- Global Action Bar -->
            <div class="flex items-center gap-2 flex-wrap">
                <a href="anki_deck_distributed_job_queue.csv" download class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm">
                    <span>📥 Download Anki CSV</span>
                </a>
                <a href="Distributed_Job_Queue_Viva_and_Project_Guide.pdf" download class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 transition shadow-sm">
                    <span>📄 Download Full PDF</span>
                </a>
                <button onclick="resetProgress()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
                    🔄 Reset Stats
                </button>
            </div>
        </div>
    </header>

    <!-- Main Content Container -->
    <main class="max-w-7xl mx-auto px-6 py-6 flex-1 w-full flex flex-col gap-6">

        <!-- Metric Cards Bar -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <span class="text-xs font-medium text-slate-400">Total Question Bank</span>
                <div class="text-2xl font-bold text-white mt-1">200</div>
                <div class="text-[11px] text-cyan-400 mt-1">100% Comprehensive</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <span class="text-xs font-medium text-slate-400">Mastered / Easy</span>
                <div id="count-mastered" class="text-2xl font-bold text-emerald-400 mt-1">0</div>
                <div class="text-[11px] text-slate-400 mt-1">Confidence Level: High</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <span class="text-xs font-medium text-slate-400">Review Later / Hard</span>
                <div id="count-flagged" class="text-2xl font-bold text-amber-400 mt-1">0</div>
                <div class="text-[11px] text-slate-400 mt-1">Requires revision</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <span class="text-xs font-medium text-slate-400">Cards Reviewed</span>
                <div id="count-viewed" class="text-2xl font-bold text-indigo-400 mt-1">0</div>
                <div id="progress-percent" class="text-[11px] text-slate-400 mt-1">0% Completed</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between col-span-2 md:col-span-1">
                <span class="text-xs font-medium text-slate-400">Overall Mastery</span>
                <div class="w-full bg-slate-800 rounded-full h-3 mt-2 overflow-hidden">
                    <div id="mastery-bar" class="bg-gradient-to-r from-cyan-500 to-emerald-400 h-3 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
                <div id="mastery-label" class="text-[11px] text-slate-400 mt-2 font-mono">0 / 200 Ready</div>
            </div>
        </div>

        <!-- Mode Switcher Tabs -->
        <div class="flex items-center justify-between border-b border-slate-800 pb-2 flex-wrap gap-3">
            <div class="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
                <button id="tab-flashcard" onclick="switchMode('flashcard')" class="px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow">
                    🎴 Flashcard Simulator
                </button>
                <button id="tab-table" onclick="switchMode('table')" class="px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white">
                    📑 Question Explorer (All 200)
                </button>
                <button id="tab-guide" onclick="switchMode('guide')" class="px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white">
                    🧠 How Anki Works for Interviews
                </button>
            </div>

            <!-- Filters -->
            <div class="flex items-center gap-3 flex-wrap text-xs">
                <select id="filter-category" onchange="filterCards()" class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500">
                    <option value="ALL">All 8 Topics (200 Questions)</option>
                    <option value="Architecture & Fundamentals">Architecture & Fundamentals</option>
                    <option value="PostgreSQL & Database Design">PostgreSQL & Database Design</option>
                    <option value="Redis & Distributed Locking">Redis & Distributed Locking</option>
                    <option value="Celery Workers & Failure Semantics">Celery Workers & Failure Semantics</option>
                    <option value="Idempotency & Deduplication">Idempotency & Deduplication</option>
                    <option value="Auth, Security & Rate Limiting">Auth, Security & Rate Limiting</option>
                    <option value="Observability & Monitoring">Observability & Monitoring</option>
                    <option value="Docker & Cloud Deployment">Docker & Cloud Deployment</option>
                    <option value="Testing & Load Simulation">Testing & Load Simulation</option>
                </select>

                <select id="filter-status" onchange="filterCards()" class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500">
                    <option value="ALL">All Statuses</option>
                    <option value="FLAGGED">Hard / Flagged Only</option>
                    <option value="UNVIEWED">Unreviewed Only</option>
                    <option value="MASTERED">Mastered Only</option>
                </select>

                <input type="text" id="search-input" oninput="filterCards()" placeholder="Search keywords, Q#, Lua, FSM..." class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500 w-52">
            </div>
        </div>

        <!-- MODE 1: FLASHCARD ANKI SIMULATOR -->
        <section id="section-flashcard" class="flex flex-col items-center justify-center py-4 gap-6">
            <div class="w-full max-w-3xl flex items-center justify-between text-xs text-slate-400 font-mono">
                <div>Card <span id="current-index-label" class="text-cyan-400 font-bold text-sm">1</span> of <span id="total-filtered-label" class="text-white font-bold text-sm">200</span></div>
                <div id="current-category-pill" class="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-sans">Architecture</div>
                <div class="flex items-center gap-2">
                    <span>Shortcut: <b>Space</b> (Flip), <b>1/2/3</b> (Rate)</span>
                </div>
            </div>

            <!-- Flashcard Frame (Perspective Container) -->
            <div class="w-full max-w-3xl h-[400px] perspective-1000 cursor-pointer" onclick="toggleCardFlip()">
                <div id="card-inner" class="card-flip relative w-full h-full transform-style-3d">
                    
                    <!-- FRONT SIDE -->
                    <div class="absolute inset-0 w-full h-full bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-slate-800 hover:border-cyan-500/50 rounded-2xl p-8 flex flex-col justify-between backface-hidden shadow-2xl transition">
                        <div class="flex items-center justify-between">
                            <span id="card-q-number" class="px-3 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono font-bold text-xs">Question #1</span>
                            <span class="text-xs text-slate-500 flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span> Click or Press Spacebar to Reveal Answer
                            </span>
                        </div>

                        <div class="my-auto">
                            <h2 id="card-question-text" class="text-xl md:text-2xl font-bold text-white tracking-tight leading-snug">
                                Loading question...
                            </h2>
                        </div>

                        <div class="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-4">
                            <span>Topic: <span id="card-topic-text" class="text-slate-300 font-medium">General</span></span>
                            <span>Prompt: Try answering aloud before flipping</span>
                        </div>
                    </div>

                    <!-- BACK SIDE (ANSWER) -->
                    <div class="absolute inset-0 w-full h-full bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-indigo-500/40 rounded-2xl p-8 flex flex-col justify-between backface-hidden rotate-y-180 shadow-2xl overflow-y-auto">
                        <div class="flex items-center justify-between">
                            <span id="card-ans-number" class="px-3 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono font-bold text-xs">Examiner Answer</span>
                            <span class="text-xs text-slate-400">Click or Space to flip back</span>
                        </div>

                        <div class="my-auto py-2">
                            <div id="card-answer-text" class="text-sm md:text-base text-slate-200 leading-relaxed font-normal">
                                Loading answer...
                            </div>
                        </div>

                        <div class="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-4">
                            <span class="text-emerald-400 font-mono">✓ Verified Production Answer</span>
                            <span>Rate your recall below to advance</span>
                        </div>
                    </div>

                </div>
            </div>

            <!-- Anki-Style Confidence Buttons -->
            <div class="flex items-center gap-3 w-full max-w-3xl justify-center flex-wrap">
                <button onclick="prevCard(event)" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-bold transition flex items-center gap-1.5">
                    ⬅ Previous
                </button>
                <button onclick="rateCard('again', event)" class="px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🔴 Again / Hard (Key: 1)
                </button>
                <button onclick="rateCard('good', event)" class="px-5 py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🟡 Good / Review (Key: 2)
                </button>
                <button onclick="rateCard('easy', event)" class="px-5 py-2.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🟢 Mastered / Easy (Key: 3)
                </button>
                <button onclick="nextCard(event)" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-bold transition flex items-center gap-1.5">
                    Next ➡
                </button>
            </div>
        </section>

        <!-- MODE 2: TABLE / QUESTION EXPLORER -->
        <section id="section-table" class="hidden flex-col gap-4">
            <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
                <div class="max-h-[600px] overflow-y-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-950 text-slate-400 sticky top-0 uppercase tracking-wider font-mono border-b border-slate-800 z-10">
                            <tr>
                                <th class="p-3.5 w-16 text-center">Q#</th>
                                <th class="p-3.5 w-44">Category</th>
                                <th class="p-3.5">Interview Question</th>
                                <th class="p-3.5 w-24 text-center">Status</th>
                                <th class="p-3.5 w-20 text-center">Practice</th>
                            </tr>
                        </thead>
                        <tbody id="table-body" class="divide-y divide-slate-800/60 font-sans">
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- MODE 3: HOW ANKI HELPS LEARN FOR INTERVIEWS -->
        <section id="section-guide" class="hidden flex-col gap-6 max-w-4xl mx-auto text-slate-300 leading-relaxed text-sm">
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col gap-6 shadow-xl">
                <div class="flex items-center gap-3 text-cyan-400 border-b border-slate-800 pb-4">
                    <span class="text-3xl">🧠</span>
                    <div>
                        <h2 class="text-xl font-bold text-white">Can Anki Help You Ace Your SDE Interviews?</h2>
                        <p class="text-xs text-slate-400">The science of Active Recall & Spaced Repetition for Backend Engineering</p>
                    </div>
                </div>

                <div class="space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-cyan-400"></span> 1. The Core Problem with SDE Technical Interviews
                    </h3>
                    <p>
                        In backend developer interviews, examiners do not just ask you to recite basic definitions. They probe your understanding of <b>distributed systems trade-offs and edge cases</b>:
                        <i>"Why did you release the lock with Lua instead of DEL?", "What happens if the worker dies after database commit?", "How does worker_prefetch_multiplier prevent queue starvation?"</i>
                    </p>
                    <p>
                        Passive reading (re-reading code or notes) creates an <b>illusion of competence</b>. When an interviewer challenges you with realistic follow-ups, passive recognition breaks down.
                    </p>
                </div>

                <div class="space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-emerald-400"></span> 2. Why Anki & Flashcards Work Wonders
                    </h3>
                    <p>
                        Anki uses two cognitive principles proven by neuroscience:
                    </p>
                    <ul class="list-disc list-inside space-y-2 pl-2 text-slate-300">
                        <li><b>Active Recall (Testing Effect):</b> Seeing the prompt (e.g. <i>"Why use transaction.on_commit?"</i>) forces your brain to reconstruct the technical solution from scratch. This strengthens retrieval pathways by over 300%.</li>
                        <li><b>Spaced Repetition System (SRS):</b> Hard questions (e.g. atomic Lua scripts, Optimistic Concurrency Control, Transactional Outbox) are reviewed more frequently, while easy concepts are spaced out over days and weeks.</li>
                    </ul>
                </div>

                <div class="space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full bg-amber-400"></span> 3. How to Use this Dashboard & Your Anki Deck
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800">
                            <h4 class="font-bold text-white mb-2 text-xs uppercase tracking-wider text-cyan-400">Method 1: Interactive Web Simulator</h4>
                            <p class="text-xs text-slate-400 mb-2">Use the <b>🎴 Flashcard Simulator</b> above right inside your browser:</p>
                            <ul class="text-xs space-y-1.5 list-disc list-inside text-slate-300">
                                <li>Press <b>Spacebar</b> to flip cards.</li>
                                <li>Press <b>1</b> for Again, <b>2</b> for Review, <b>3</b> for Mastered.</li>
                                <li>Filter by specific topic (e.g., Redis Locking or PostgreSQL).</li>
                            </ul>
                        </div>
                        <div class="p-4 rounded-xl bg-slate-950 border border-slate-800">
                            <h4 class="font-bold text-white mb-2 text-xs uppercase tracking-wider text-emerald-400">Method 2: Official Anki Desktop App</h4>
                            <p class="text-xs text-slate-400 mb-2">Study on mobile or desktop with the exported deck:</p>
                            <ol class="text-xs space-y-1.5 list-decimal list-inside text-slate-300">
                                <li>Download the <code>anki_deck_distributed_job_queue.csv</code> button on top.</li>
                                <li>Open Anki Desktop & click <b>Import File</b>.</li>
                                <li>Select comma separated, map Front/Back/Tags.</li>
                                <li>Practice 20 cards every morning before your interviews!</li>
                            </ol>
                        </div>
                    </div>
                </div>

                <div class="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-xs text-cyan-300 flex items-start gap-3">
                    <span class="text-lg">💡</span>
                    <div>
                        <b>Pro Tip for Interviews:</b> When you flip a card, don't just read the answer in your head. <b>Speak the explanation aloud</b> in 2-3 concise sentences. This trains your verbal fluency, speech pacing, and engineering vocabulary.
                    </div>
                </div>
            </div>
        </section>

    </main>

    <!-- Embedded Data & Engine -->
    <script>
        const QUESTIONS_DATA = ''' + data_json + ''';

        let state = {
            currentIndex: 0,
            filteredCards: [...QUESTIONS_DATA],
            cardStatuses: JSON.parse(localStorage.getItem('djq_card_statuses') || '{}'),
            currentMode: 'flashcard',
            isFlipped: false
        };

        function init() {
            updateStats();
            filterCards();
            renderTable();
            setupKeyboardShortcuts();
        }

        function switchMode(mode) {
            state.currentMode = mode;
            document.getElementById('section-flashcard').classList.toggle('hidden', mode !== 'flashcard');
            document.getElementById('section-table').classList.toggle('hidden', mode !== 'table');
            document.getElementById('section-guide').classList.toggle('hidden', mode !== 'guide');

            document.getElementById('tab-flashcard').className = mode === 'flashcard' ? 'px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow' : 'px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white';
            document.getElementById('tab-table').className = mode === 'table' ? 'px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow' : 'px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white';
            document.getElementById('tab-guide').className = mode === 'guide' ? 'px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow' : 'px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white';

            if (mode === 'table') renderTable();
        }

        function filterCards() {
            const cat = document.getElementById('filter-category').value;
            const status = document.getElementById('filter-status').value;
            const search = document.getElementById('search-input').value.toLowerCase().trim();

            state.filteredCards = QUESTIONS_DATA.filter(item => {
                if (cat !== 'ALL' && item.category !== cat) return false;
                
                const itemStatus = state.cardStatuses[item.id] || 'UNVIEWED';
                if (status === 'FLAGGED' && itemStatus !== 'FLAGGED') return false;
                if (status === 'MASTERED' && itemStatus !== 'MASTERED') return false;
                if (status === 'UNVIEWED' && itemStatus !== 'UNVIEWED') return false;

                if (search) {
                    const matchQ = item.question.toLowerCase().includes(search);
                    const matchA = item.answer.toLowerCase().includes(search);
                    const matchId = `q${item.id}` === search || `${item.id}` === search;
                    if (!matchQ && !matchA && !matchId) return false;
                }

                return true;
            });

            state.currentIndex = 0;
            updateCardDisplay();
            if (state.currentMode === 'table') renderTable();
        }

        function updateCardDisplay() {
            const inner = document.getElementById('card-inner');
            inner.classList.remove('flipped');
            state.isFlipped = false;

            const total = state.filteredCards.length;
            document.getElementById('total-filtered-label').innerText = total;

            if (total === 0) {
                document.getElementById('current-index-label').innerText = '0';
                document.getElementById('card-q-number').innerText = 'No Cards Found';
                document.getElementById('card-question-text').innerText = 'No questions match your current filter criteria.';
                document.getElementById('card-answer-text').innerText = 'Try changing category or clearing your search term.';
                document.getElementById('current-category-pill').innerText = 'Empty';
                return;
            }

            const card = state.filteredCards[state.currentIndex];
            document.getElementById('current-index-label').innerText = (state.currentIndex + 1);
            document.getElementById('card-q-number').innerText = `Question #${card.id}`;
            document.getElementById('card-ans-number').innerText = `Answer #${card.id}`;
            document.getElementById('card-question-text').innerText = card.question;
            document.getElementById('card-answer-text').innerHTML = card.answer.replace(/\\n/g, '<br>');
            document.getElementById('card-topic-text').innerText = card.category;
            document.getElementById('current-category-pill').innerText = card.category;
        }

        function toggleCardFlip() {
            const inner = document.getElementById('card-inner');
            state.isFlipped = !state.isFlipped;
            inner.classList.toggle('flipped', state.isFlipped);
        }

        function rateCard(rating, e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;

            const card = state.filteredCards[state.currentIndex];
            if (rating === 'easy') {
                state.cardStatuses[card.id] = 'MASTERED';
            } else if (rating === 'again') {
                state.cardStatuses[card.id] = 'FLAGGED';
            } else {
                state.cardStatuses[card.id] = 'REVIEW';
            }

            saveStatuses();
            nextCard();
        }

        function nextCard(e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;
            state.currentIndex = (state.currentIndex + 1) % state.filteredCards.length;
            updateCardDisplay();
        }

        function prevCard(e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;
            state.currentIndex = (state.currentIndex - 1 + state.filteredCards.length) % state.filteredCards.length;
            updateCardDisplay();
        }

        function jumpToCard(id) {
            const idx = state.filteredCards.findIndex(c => c.id === id);
            if (idx !== -1) {
                state.currentIndex = idx;
                switchMode('flashcard');
                updateCardDisplay();
            }
        }

        function renderTable() {
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            state.filteredCards.forEach(item => {
                const status = state.cardStatuses[item.id] || 'UNVIEWED';
                let badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">Unviewed</span>';
                if (status === 'MASTERED') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">Mastered</span>';
                if (status === 'FLAGGED') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold">Hard</span>';
                if (status === 'REVIEW') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-bold">Review</span>';

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.innerHTML = `
                    <td class="p-3.5 text-center font-mono font-bold text-slate-400">Q${item.id}</td>
                    <td class="p-3.5 text-slate-300 font-medium"><span class="text-[11px] px-2 py-1 bg-slate-800/80 rounded-md border border-slate-700/60">${item.category}</span></td>
                    <td class="p-3.5 text-slate-200 font-medium">${item.question}</td>
                    <td class="p-3.5 text-center">${badge}</td>
                    <td class="p-3.5 text-center">
                        <button onclick="jumpToCard(${item.id})" class="px-2.5 py-1 text-[11px] rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-semibold">
                            Practice
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function updateStats() {
            let mastered = 0;
            let flagged = 0;
            let viewed = 0;

            QUESTIONS_DATA.forEach(item => {
                const s = state.cardStatuses[item.id];
                if (s) viewed++;
                if (s === 'MASTERED') mastered++;
                if (s === 'FLAGGED') flagged++;
            });

            document.getElementById('count-mastered').innerText = mastered;
            document.getElementById('count-flagged').innerText = flagged;
            document.getElementById('count-viewed').innerText = viewed;

            const percent = Math.round((viewed / 200) * 100);
            document.getElementById('progress-percent').innerText = `${percent}% Completed`;

            const masteryPercent = Math.round((mastered / 200) * 100);
            document.getElementById('mastery-bar').style.width = `${masteryPercent}%`;
            document.getElementById('mastery-label').innerText = `${mastered} / 200 Ready (${masteryPercent}%)`;
        }

        function saveStatuses() {
            localStorage.setItem('djq_card_statuses', JSON.stringify(state.cardStatuses));
            updateStats();
        }

        function resetProgress() {
            if (confirm('Are you sure you want to reset all card mastery stats and progress?')) {
                state.cardStatuses = {};
                saveStatuses();
                filterCards();
            }
        }

        function setupKeyboardShortcuts() {
            window.addEventListener('keydown', (e) => {
                if (document.activeElement === document.getElementById('search-input')) return;

                if (state.currentMode === 'flashcard') {
                    if (e.code === 'Space') {
                        e.preventDefault();
                        toggleCardFlip();
                    } else if (e.key === '1') {
                        rateCard('again');
                    } else if (e.key === '2') {
                        rateCard('good');
                    } else if (e.key === '3') {
                        rateCard('easy');
                    } else if (e.code === 'ArrowRight') {
                        nextCard();
                    } else if (e.code === 'ArrowLeft') {
                        prevCard();
                    }
                }
            });
        }

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
'''

with open('interview_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(template)

print('Generated interview_dashboard.html successfully!')
