/**
 * Enneagram Quiz JavaScript
 * Handles the progressive quiz interface and submission
 */

class EnneagramQuiz {
    constructor() {
        this.questions = [];
        this.currentPage = 0;
        this.questionsPerPage = 3;
        this.responses = {};
        this.userName = '';
        this.questionsLoaded = false;
        this.isSubmitting = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadQuestions();
    }

    initializeElements() {
        this.landingSection = document.getElementById('landingSection');
        this.quizSection = document.getElementById('quizSection');
        this.nameInput = document.getElementById('nameInput');
        this.startBtn = document.getElementById('startBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.userNameSpan = document.getElementById('userName');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.questionsContainer = document.getElementById('questionsContainer');
        this.navigation = document.getElementById('navigation');
    }

    async loadQuestions() {
        try {
            this.startBtn.textContent = 'Loading...';
            const response = await fetch('/api/questions');
            this.questions = await response.json();
            this.questionsLoaded = true;
            this.startBtn.textContent = 'Begin';
            this.updateStartButton();
        } catch (error) {
            console.error('Failed to load questions:', error);
            this.startBtn.textContent = 'Error - Reload';
            // Fallback: reload page to get questions from server-side
            window.location.href = '/quiz';
        }
    }

    bindEvents() {
        this.nameInput.addEventListener('input', () => {
            this.updateStartButton();
        });

        this.nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.startBtn.disabled) {
                this.startQuiz();
            }
        });

        this.startBtn.addEventListener('click', () => this.startQuiz());
        this.nextBtn.addEventListener('click', () => this.nextPage());
    }

    updateStartButton() {
        const name = this.nameInput.value.trim();
        const nameValid = name.length >= 2;
        this.startBtn.disabled = !nameValid || !this.questionsLoaded;
    }

    startQuiz() {
        this.userName = this.nameInput.value.trim();
        if (!this.userName || !this.questionsLoaded || this.questions.length === 0) return;

        this.userNameSpan.textContent = this.userName;
        
        // Smooth transition
        this.landingSection.classList.add('slide-up');
        
        setTimeout(() => {
            this.quizSection.classList.add('active');
            this.showCurrentPage();
        }, 600);
    }

    showCurrentPage() {
        const startIdx = this.currentPage * this.questionsPerPage;
        const endIdx = Math.min(startIdx + this.questionsPerPage, this.questions.length);
        const pageQuestions = this.questions.slice(startIdx, endIdx);

        // Update progress
        const totalAnswered = Object.keys(this.responses).length;
        const progressPercent = (totalAnswered / this.questions.length) * 100;
        this.progressFill.style.width = progressPercent + '%';
        this.progressText.textContent = `Question ${startIdx + 1}-${endIdx} of ${this.questions.length}`;

        // Render questions
        this.questionsContainer.innerHTML = pageQuestions.map(q => this.renderQuestion(q)).join('');

        // Add event listeners
        this.questionsContainer.addEventListener('change', () => this.checkPageComplete());
        
        // Check if page is already complete
        this.checkPageComplete();
    }

    renderQuestion(question) {
        const isAnswered = this.responses[`q_${question.id}`] !== undefined;
        const currentValue = this.responses[`q_${question.id}`] || '';

        return `
            <div class="question-card" data-question-id="${question.id}">
                <div class="question-text">
                    <span class="question-number">${question.id}.</span>
                    ${question.text}
                </div>
                
                <div class="answer-options">
                    ${[1,2,3,4,5].map(value => `
                        <label class="answer-option">
                            <div class="option-label">
                                ${value === 1 ? 'Strongly<br>Disagree' : 
                                  value === 3 ? 'Neutral' : 
                                  value === 5 ? 'Strongly<br>Agree' : ''}
                            </div>
                            <input type="radio" name="q_${question.id}" value="${value}" ${currentValue == value ? 'checked' : ''}>
                            <div class="option-circle">${value}</div>
                            <div class="option-number">${value}</div>
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
    }

    checkPageComplete() {
        const startIdx = this.currentPage * this.questionsPerPage;
        const endIdx = Math.min(startIdx + this.questionsPerPage, this.questions.length);
        const pageQuestions = this.questions.slice(startIdx, endIdx);

        // Check if all questions on current page are answered
        const allAnswered = pageQuestions.every(q => {
            const input = document.querySelector(`input[name="q_${q.id}"]:checked`);
            if (input) {
                this.responses[`q_${q.id}`] = parseInt(input.value);
                return true;
            }
            return false;
        });

        // Update navigation
        this.navigation.classList.toggle('enabled', allAnswered);
        this.nextBtn.disabled = !allAnswered;

        // Update button text for last page
        const isLastPage = endIdx >= this.questions.length;
        this.nextBtn.textContent = isLastPage ? 'Complete Assessment' : 'Continue';

        // Auto-submit if last page and all answered
        if (isLastPage && allAnswered) {
            setTimeout(() => this.submitQuiz(), 1000);
        }
    }

    nextPage() {
        const isLastPage = (this.currentPage + 1) * this.questionsPerPage >= this.questions.length;
        
        if (isLastPage) {
            this.submitQuiz();
        } else {
            this.currentPage++;
            this.showCurrentPage();
        }
    }

    async submitQuiz() {
        // Prevent double submission
        if (this.isSubmitting) return;
        this.isSubmitting = true;
        
        try {
            // Show loading state
            this.nextBtn.textContent = 'Completing...';
            this.nextBtn.disabled = true;

            const formData = new FormData();
            formData.append('name', this.userName);
            formData.append('consent', 'yes');

            // Add all responses
            Object.entries(this.responses).forEach(([key, value]) => {
                formData.append(key, value);
            });

            const response = await fetch('/submit', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Check if the server redirected us (for successful submission)
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    // Fallback in case no redirect happened
                    window.location.href = '/results';
                }
            } else {
                throw new Error('Submission failed');
            }
        } catch (error) {
            console.error('Submit error:', error);
            alert('There was an error submitting your assessment. Please try again.');
            this.nextBtn.textContent = 'Complete Assessment';
            this.nextBtn.disabled = false;
            this.isSubmitting = false; // Reset so user can try again
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EnneagramQuiz();
});
