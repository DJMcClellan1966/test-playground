/**App Forge Frontend Logic*/

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

  async save(app_name) {
    const res = await fetch('/api/save-and-preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_name })
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
          <button class="btn btn-yes" id="btn-yes">✓ Yes</button>
          <button class="btn btn-no" id="btn-no">✗ No</button>
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
    document.getElementById('question-count').textContent = `Question ${current} of ${total}`;
  },

  showResults(tech_stack, files) {
    document.getElementById('stack-backend').textContent = tech_stack.backend;
    document.getElementById('stack-db').textContent = tech_stack.database;
    document.getElementById('stack-frontend').textContent = tech_stack.frontend;
    document.getElementById('stack-auth').textContent = tech_stack.auth;
    
    if (tech_stack.notes && tech_stack.notes.length > 0) {
      const notesHtml = tech_stack.notes.map(n => `<div class="stack-note">💡 ${n}</div>`).join('');
      document.getElementById('stack-notes').innerHTML = notesHtml;
    }

    // Show code preview (just first 30 lines)
    const app_py = files['app.py'];
    const preview = app_py.split('\n').slice(0, 30).join('\n') + '\n\n...';
    document.getElementById('code-preview').textContent = preview;
  },

  showSuccess(path) {
    document.getElementById('success-message').style.display = 'block';
    document.getElementById('success-path').textContent = `📂 Saved to: ${path}`;
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

  async startWizard() {
    const description = document.getElementById('description').value.trim();
    
    if (description.length < 10) {
      alert('Please describe your app with at least 10 characters');
      return;
    }

    this.description = description;
    const result = await API.start(description);
    
    if (result.error) {
      alert(result.error);
      return;
    }

    this.profile = result.profile;
    this.step = 'questions';
    this.questionIndex = 1;
    this.totalQuestions = 9; // Estimate
    
    UI.showStep('questions');
    
    if (result.next_question) {
      this.currentQuestion = result.next_question;
      UI.showQuestion(this.currentQuestion);
      UI.updateQuestionCount(this.questionIndex, this.totalQuestions);
    }
  },

  async answer(question_id, answer) {
    const result = await API.answer(question_id, answer);
    
    this.answered = result.answered;
    
    if (result.complete) {
      // Generate code
      const generated = await API.generate(this.description);
      this.techStack = generated.tech_stack;
      this.files = generated.files;
      
      this.step = 'review';
      UI.showStep('review');
      UI.showResults(this.techStack, this.files);
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
    const result = await API.save(app_name);
    
    if (result.success) {
      UI.showSuccess(result.project_path);
    } else {
      alert('Error saving: ' + result.error);
    }
  },

  goBack() {
    this.step = 'describe';
    UI.showStep('describe');
  }
};

// Init
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-next').addEventListener('click', () => State.startWizard());
  document.getElementById('btn-back').addEventListener('click', () => State.goBack());
  document.getElementById('btn-save').addEventListener('click', () => State.save());
  
  document.getElementById('btn-export-github').addEventListener('click', () => {
    const github_url = prompt('GitHub repo URL (e.g., https://github.com/user/my-app.git):');
    if (github_url) {
      const app_name = document.getElementById('app-name').value || 'My App';
      API.exportGithub(State.techStack.project_path, github_url);
    }
  });
});
