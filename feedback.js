/* Feedback modal logic — shared by index.html and the test suite */

var feedbackRating = 0;
var ratingLabels = ['', 'Slecht', 'Matig', 'Goed', 'Erg goed', 'Uitstekend!'];

function setRating(n) {
  feedbackRating = n;
  document.querySelectorAll('#rating-stars span').forEach(function(s, i) {
    s.style.opacity = i < n ? '1' : '0.3';
  });
  document.getElementById('rating-label').textContent = ratingLabels[n];
}

function toggleFeedbackCat(btn) {
  var active = btn.style.background === 'rgb(30, 58, 95)';
  btn.style.background = active ? '#fff' : '#1e3a5f';
  btn.style.color = active ? '#475569' : '#fff';
  btn.style.borderColor = active ? '#e2e8f0' : '#1e3a5f';
}

function submitFeedback() {
  document.getElementById('modal-feedback').style.display = 'none';
  document.getElementById('feedback-text').value = '';
  feedbackRating = 0;
  document.querySelectorAll('#rating-stars span').forEach(function(s) { s.style.opacity = '1'; });
  document.querySelectorAll('#feedback-cats button').forEach(function(b) {
    b.style.background = '#fff';
    b.style.color = '#475569';
    b.style.borderColor = '#e2e8f0';
  });
  toast('Bedankt voor je feedback!');
}

/* Export for Node.js (test environment) */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { setRating, toggleFeedbackCat, submitFeedback, get feedbackRating() { return feedbackRating; } };
}
