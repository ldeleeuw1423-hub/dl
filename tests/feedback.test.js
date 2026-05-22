/**
 * Tests for the feedback button and modal in docs/index.html.
 * Logic lives in docs/feedback.js which is loaded by index.html at runtime
 * and required here directly for unit testing.
 */

const fs = require('fs');
const path = require('path');

// ─── DOM setup ───────────────────────────────────────────────────────────────

function loadDOM() {
  const html = fs.readFileSync(path.join(__dirname, '..', 'docs', 'index.html'), 'utf8');
  document.documentElement.innerHTML = html;
}

// ─── Module under test ───────────────────────────────────────────────────────

// feedback.js uses `document` and a global `toast()`.  We load the DOM first,
// then stub toast, then require the module so it inherits the jsdom globals.
let fb;

beforeEach(() => {
  loadDOM();
  global.toast = jest.fn();
  jest.resetModules();
  fb = require('../docs/feedback.js');
});

// Convenience: expose module functions as plain references inside tests
const fn = {
  setRating: (...a) => fb.setRating(...a),
  toggleFeedbackCat: (...a) => fb.toggleFeedbackCat(...a),
  submitFeedback: (...a) => fb.submitFeedback(...a),
};

// ─── Floating feedback button ────────────────────────────────────────────────

describe('Floating feedback button', () => {
  test('exists in the document', () => {
    const feedbackBtn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent.includes('Feedback'));
    expect(feedbackBtn).not.toBeNull();
  });

  test('modal is hidden on page load', () => {
    const modal = document.getElementById('modal-feedback');
    expect(modal).not.toBeNull();
    expect(modal.style.display).toBe('none');
  });

  test('clicking button shows modal', () => {
    const modal = document.getElementById('modal-feedback');
    const feedbackBtn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent.trim().includes('Feedback'));
    feedbackBtn.click();
    expect(modal.style.display).toBe('flex');
  });
});

// ─── setRating() ─────────────────────────────────────────────────────────────

describe('setRating()', () => {
  test('updates feedbackRating', () => {
    fn.setRating(4);
    expect(fb.feedbackRating).toBe(4);
  });

  test('highlights stars up to chosen rating, dims the rest', () => {
    fn.setRating(3);
    const stars = document.querySelectorAll('#rating-stars span');
    stars.forEach((s, i) => {
      expect(s.style.opacity).toBe(i < 3 ? '1' : '0.3');
    });
  });

  test('sets label text for each value 1-5', () => {
    const expected = ['', 'Slecht', 'Matig', 'Goed', 'Erg goed', 'Uitstekend!'];
    for (let n = 1; n <= 5; n++) {
      fn.setRating(n);
      expect(document.getElementById('rating-label').textContent).toBe(expected[n]);
    }
  });

  test('5-star rating lights up all stars', () => {
    fn.setRating(5);
    document.querySelectorAll('#rating-stars span').forEach(s => {
      expect(s.style.opacity).toBe('1');
    });
  });
});

// ─── toggleFeedbackCat() ─────────────────────────────────────────────────────

describe('toggleFeedbackCat()', () => {
  function catButtons() {
    return Array.from(document.querySelectorAll('#feedback-cats button'));
  }

  test('activates a chip on first click', () => {
    const btn = catButtons()[0];
    fn.toggleFeedbackCat(btn);
    expect(btn.style.background).toBe('rgb(30, 58, 95)');
    expect(btn.style.color).toBe('rgb(255, 255, 255)');
  });

  test('deactivates an active chip on second click', () => {
    const btn = catButtons()[0];
    fn.toggleFeedbackCat(btn);
    fn.toggleFeedbackCat(btn);
    expect(btn.style.background).toBe('rgb(255, 255, 255)');
    expect(btn.style.color).toBe('rgb(71, 85, 105)');
  });

  test('multiple chips can be active at the same time', () => {
    const btns = catButtons();
    fn.toggleFeedbackCat(btns[0]);
    fn.toggleFeedbackCat(btns[2]);
    expect(btns[0].style.background).toBe('rgb(30, 58, 95)');
    expect(btns[2].style.background).toBe('rgb(30, 58, 95)');
    // chips ship with inline background:#fff — untouched chip stays white
    expect(btns[1].style.background).not.toBe('rgb(30, 58, 95)');
  });
});

// ─── submitFeedback() ────────────────────────────────────────────────────────

describe('submitFeedback()', () => {
  test('hides the modal', () => {
    const modal = document.getElementById('modal-feedback');
    modal.style.display = 'flex';
    fn.submitFeedback();
    expect(modal.style.display).toBe('none');
  });

  test('clears the textarea', () => {
    const textarea = document.getElementById('feedback-text');
    textarea.value = 'Some feedback text';
    fn.submitFeedback();
    expect(textarea.value).toBe('');
  });

  test('resets feedbackRating to 0', () => {
    fn.setRating(4);
    fn.submitFeedback();
    expect(fb.feedbackRating).toBe(0);
  });

  test('resets all star opacities to 1', () => {
    fn.setRating(2);
    fn.submitFeedback();
    document.querySelectorAll('#rating-stars span').forEach(s => {
      expect(s.style.opacity).toBe('1');
    });
  });

  test('deactivates all category chips', () => {
    const btns = Array.from(document.querySelectorAll('#feedback-cats button'));
    btns.forEach(b => fn.toggleFeedbackCat(b));
    fn.submitFeedback();
    btns.forEach(b => {
      expect(b.style.background).toBe('rgb(255, 255, 255)');
      expect(b.style.color).toBe('rgb(71, 85, 105)');
    });
  });

  test('calls toast with Dutch thank-you message', () => {
    fn.submitFeedback();
    expect(global.toast).toHaveBeenCalledWith('Bedankt voor je feedback!');
  });

  test('toast is called exactly once per submit', () => {
    fn.submitFeedback();
    expect(global.toast).toHaveBeenCalledTimes(1);
  });
});

// ─── Modal close controls ─────────────────────────────────────────────────────

describe('Modal close controls', () => {
  test('✕ button closes the modal', () => {
    const modal = document.getElementById('modal-feedback');
    modal.style.display = 'flex';
    const closeBtn = modal.querySelector('button[onclick*="none"]');
    expect(closeBtn).not.toBeNull();
    closeBtn.click();
    expect(modal.style.display).toBe('none');
  });

  test('Annuleren button closes the modal', () => {
    const modal = document.getElementById('modal-feedback');
    modal.style.display = 'flex';
    const cancelBtn = Array.from(modal.querySelectorAll('button'))
      .find(b => b.textContent.trim() === 'Annuleren');
    expect(cancelBtn).not.toBeNull();
    cancelBtn.click();
    expect(modal.style.display).toBe('none');
  });
});
