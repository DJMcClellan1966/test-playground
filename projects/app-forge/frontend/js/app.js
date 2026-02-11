/**App Forge Frontend Logic*/

// Human-readable labels for inferred answers
const ANSWER_LABELS = {
  has_data: ["Stores data in a database", "No database needed"],
  needs_auth: ["User login required", "No login needed"],
  multi_user: ["Multiple users", "Single user"],
  realtime: ["Real-time updates", "Standard loading"],
  search: ["Search capability", "No search needed"],
  export: ["Data export", "No export needed"],
  mobile: ["Mobile support", "Desktop only"],
  complex_queries: ["Complex queries", "Simple queries"],
  performance_critical: ["Performance critical", "Standard performance"],
};

// Human-readable template names
const TEMPLATE_NAMES = {
  sliding_puzzle: "Sliding Tile Puzzle",
  tictactoe: "Tic Tac Toe",
  memory_game: "Memory Match",
  guess_game: "Guess the Number",
  quiz: "Quiz / Trivia",
  hangman: "Hangman",
  wordle: "Wordle",
  calculator: "Calculator",
  converter: "Unit Converter",
  timer: "Timer / Pomodoro",
  reaction_game: "Reaction Time Game",
  generic_game: "Game",
  generic: "Custom App",
  crud: "Data App (CRUD)",
  // Component assembler types
  password_gen: "Password Generator",
  color_gen: "Color Palette Generator",
  name_gen: "Name Generator",
  quote_gen: "Quote Generator",
  dice_roller: "Dice Roller",
  coin_flip: "Coin Flipper",
  lorem_gen: "Lorem Ipsum Generator",
  generic_gen: "Random Generator",
  typing_test: "Typing Speed Test",
  flashcard: "Flashcard Study Tool",
  kanban: "Kanban Board",
  chat: "Chat Interface",
  canvas: "Drawing / Whiteboard",
  editor: "Text Editor",
};

const API = {
  async start(description) {
    const res = await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description })
    });
    return res.json();
  },

  async answer(question_id, answer) {
    const res = await fetch('/api/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id, answer })
    });
    return res.json();
  },

  async generate(app_name) {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_name })
    });
    return res.json();
  },

  async save(app_name, description, answered, files) {
    const res = await fetch('/api/save-and-preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_name, description, answered, files })
    });
    return res.json();
  },

  async exportGithub(project_path, github_url) {
    const res = await fetch('/api/export-github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_path, github_url })
    });
    return res.json();
  },

  async stopPreview() {
    const res = await fetch('/api/preview/stop', { method: 'POST' });
    return res.json();
  },

  async regenerate(resetFrom) {
    const res = await fetch('/api/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset_from: resetFrom || null })
    });
    return res.json();
  }
};

const UI = {
  showStep(name) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step-${name}`).classList.add('active');
  },

  showQuestion(question) {
    const container = document.getElementById('questions-container');
    container.innerHTML = `
      <div class="question-card">
        <h2>${question.text}</h2>
        <div class="question-buttons">
          <button class="btn btn-yes" id="btn-yes">&#10003; Yes</button>
          <button class="btn btn-no" id="btn-no">&#10007; No</button>
        </div>
      </div>
    `;
    document.getElementById('btn-yes').addEventListener('click', () => {
      State.answer(question.id, true);
    });
    document.getElementById('btn-no').addEventListener('click', () => {
      State.answer(question.id, false);
    });
  },

  updateQuestionCount(current, total) {
    const el = document.getElementById('question-count');
    if (total <= 1) {
      el.textContent = 'One more thing:';
    } else {
      el.textContent = `Question ${current} of ${total}`;
    }
  },

  showDetection(inferred, detected) {
    const panel = document.getElementById('detection-panel');
    const items = document.getElementById('detection-items');
    const badges = [];

    // Show matched template
    if (detected && detected.template) {
      const name = TEMPLATE_NAMES[detected.template] || detected.template;
      badges.push(`<span class="detection-item template-badge">Building: ${name}</span>`);
    }

    // Show extracted features
    if (detected && detected.features) {
      for (const [key, val] of Object.entries(detected.features)) {
        if (key !== 'data_app') {
          const label = key.replace(/_/g, ' ');
          badges.push(`<span class="detection-item feature-badge">${label}: ${val}</span>`);
        }
      }
    }

    // Show inferred answers
    for (const [key, val] of Object.entries(inferred)) {
      const labels = ANSWER_LABELS[key];
      if (labels) {
        const label = val ? labels[0] : labels[1];
        badges.push(`<span class="detection-item">${label}</span>`);
      }
    }

    if (badges.length > 0) {
      items.innerHTML = badges.join('');
      panel.style.display = 'block';
    }
  },

  showGenerating() {
    const container = document.getElementById('questions-container');
    container.innerHTML = `
      <div class="generating-message">
        <h2>Building your app</h2>
        <div class="dots">&#9679; &#9679; &#9679;</div>
      </div>
    `;
    document.getElementById('question-count').textContent = '';
  },

  showResults(tech_stack, files, preview_url, preview_error) {
    document.getElementById('stack-backend').textContent = tech_stack.backend;
    document.getElementById('stack-db').textContent = tech_stack.database;
    document.getElementById('stack-frontend').textContent = tech_stack.frontend;
    document.getElementById('stack-auth').textContent = tech_stack.auth;

    if (tech_stack.notes && tech_stack.notes.length > 0) {
      const notesHtml = tech_stack.notes.map(n => `<div class="stack-note">&#128161; ${n}</div>`).join('');
      document.getElementById('stack-notes').innerHTML = notesHtml;
    }

    const frame = document.getElementById('preview-frame');
    const statusEl = document.getElementById('preview-status');

    if (preview_url) {
      statusEl.innerHTML = '<span class="status-running">&#9679; Live</span> Your app is running at ' + preview_url;
      statusEl.style.display = 'block';
      frame.removeAttribute('srcdoc');
      frame.removeAttribute('sandbox');
      frame.src = preview_url;
    } else if (preview_error) {
      statusEl.innerHTML = '<span class="status-error">&#9679; Error</span> ' + preview_error;
      statusEl.style.display = 'block';
      const html = files['templates/index.html'];
      if (html) frame.srcdoc = html;
    } else {
      const html = files['templates/index.html'];
      if (html) frame.srcdoc = html;
      statusEl.style.display = 'none';
    }

    // File switching in code tab
    State.currentFile = 'app.py';
    switchFile('app.py');
  },

  showSuccess(path) {
    document.getElementById('success-message').style.display = 'block';
    document.getElementById('success-path').textContent = `Saved to: ${path}`;
    const cdEl = document.getElementById('success-cd');
    if (cdEl) cdEl.textContent = path;
  }
};

const State = {
  step: 'describe',
  description: '',
  profile: null,
  answered: {},
  currentQuestion: null,
  techStack: null,
  files: null,
  totalQuestions: 0,
  questionIndex: 0,
  projectPath: null,
  currentFile: 'app.py',

  async startWizard() {
    const description = document.getElementById('description').value.trim();
    if (description.length < 10) {
      alert('Please describe your app with at least 10 characters');
      return;
    }

    this.description = description;
    const result = await API.start(description);
    if (result.error) { alert(result.error); return; }

    this.profile = result.profile;
    this.answered = result.inferred || {};
    this.totalQuestions = result.total_questions;
    this.questionIndex = 1;

    // Show what was detected (template + features + inferred answers)
    const panel = document.getElementById('detection-panel');
    panel.style.display = 'none';
    if ((result.inferred && Object.keys(result.inferred).length > 0) || result.detected) {
      UI.showDetection(result.inferred || {}, result.detected || {});
    }

    if (result.next_question) {
      // Still have questions to ask
      this.step = 'questions';
      this.currentQuestion = result.next_question;
      UI.showStep('questions');
      document.getElementById('questions-title').textContent =
        this.totalQuestions <= 2 ? 'Just a couple more details' : 'A few more details';
      UI.showQuestion(this.currentQuestion);
      UI.updateQuestionCount(this.questionIndex, this.totalQuestions);
    } else {
      // All answered by inference — auto-generate
      this.step = 'questions';
      UI.showStep('questions');
      document.getElementById('questions-title').textContent = 'Building your app';
      UI.showGenerating();

      const generated = await API.generate(this.description);
      this.techStack = generated.tech_stack;
      this.files = generated.files;
      this.step = 'review';
      UI.showStep('review');
      UI.showResults(this.techStack, this.files, generated.preview_url, generated.preview_error);
    }
  },

  async answer(question_id, answer) {
    const result = await API.answer(question_id, answer);
    this.answered = result.answered;
    if (result.total_questions !== undefined) this.totalQuestions = result.total_questions;

    if (result.complete) {
      UI.showGenerating();
      const generated = await API.generate(this.description);
      this.techStack = generated.tech_stack;
      this.files = generated.files;
      this.step = 'review';
      UI.showStep('review');
      UI.showResults(this.techStack, this.files, generated.preview_url, generated.preview_error);
    } else {
      this.questionIndex++;
      this.currentQuestion = result.next_question;
      if (this.currentQuestion) {
        UI.showQuestion(this.currentQuestion);
        UI.updateQuestionCount(this.questionIndex, this.totalQuestions);
      }
    }
  },

  async save() {
    const app_name = document.getElementById('app-name').value || 'My App';
    const result = await API.save(app_name, this.description, this.answered, this.files);
    if (result.success) {
      this.projectPath = result.project_path;
      UI.showSuccess(result.project_path);
    } else {
      alert('Error saving: ' + (result.error || 'Unknown error'));
    }
  },

  goBack() {
    API.stopPreview();
    this.step = 'describe';
    this.projectPath = null;
    document.getElementById('success-message').style.display = 'none';
    document.getElementById('preview-frame').removeAttribute('src');
    document.getElementById('preview-frame').srcdoc = '';
    document.getElementById('detection-panel').style.display = 'none';
    UI.showStep('describe');
  },

  async changeAnswers() {
    API.stopPreview();
    const result = await API.regenerate();
    this.answered = result.answered;
    this.totalQuestions = result.total_questions || this.totalQuestions;
    this.questionIndex = Object.keys(this.answered).length + 1;

    if (result.complete) {
      const generated = await API.generate(this.description);
      this.techStack = generated.tech_stack;
      this.files = generated.files;
      this.step = 'review';
      UI.showStep('review');
      UI.showResults(this.techStack, this.files, generated.preview_url, generated.preview_error);
    } else {
      this.step = 'questions';
      this.currentQuestion = result.next_question;
      UI.showStep('questions');
      if (this.currentQuestion) {
        UI.showQuestion(this.currentQuestion);
        UI.updateQuestionCount(this.questionIndex, this.totalQuestions);
      }
    }
  }
};

// Tab switching for preview/code
function switchTab(tab) {
  document.querySelectorAll('.preview-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => {
    t.classList.remove('active');
    t.style.display = 'none';
  });
  const targetTab = document.querySelector(`.preview-tab[data-tab="${tab}"]`);
  const targetContent = document.getElementById(`tab-${tab}`);
  if (targetTab) targetTab.classList.add('active');
  if (targetContent) {
    targetContent.classList.add('active');
    targetContent.style.display = 'block';
  }
}

// File switching in code tab
function switchFile(filename) {
  document.querySelectorAll('.file-tab').forEach(t => t.classList.remove('active'));
  const tab = document.querySelector(`.file-tab[data-file="${filename}"]`);
  if (tab) tab.classList.add('active');
  const codeEl = document.getElementById('code-preview');
  if (State.files && State.files[filename]) {
    codeEl.textContent = State.files[filename];
  } else {
    codeEl.textContent = '(no content)';
  }
  State.currentFile = filename;
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-next').addEventListener('click', () => State.startWizard());
  document.getElementById('btn-back').addEventListener('click', () => State.goBack());
  document.getElementById('btn-back-review').addEventListener('click', () => State.goBack());
  document.getElementById('btn-change-answers').addEventListener('click', () => State.changeAnswers());
  document.getElementById('btn-save').addEventListener('click', () => State.save());

  document.getElementById('btn-export-github').addEventListener('click', async () => {
    if (!State.projectPath) {
      alert('Please save to desktop first, then export to GitHub.');
      return;
    }
    const github_url = prompt('GitHub repo URL (e.g., https://github.com/user/my-app.git):');
    if (github_url) {
      const result = await API.exportGithub(State.projectPath, github_url);
      if (result.success) {
        alert('Successfully pushed to GitHub!');
      } else {
        alert('GitHub export error: ' + (result.error || 'Unknown error'));
      }
    }
  });
});
