document.addEventListener('DOMContentLoaded', () => {
  // Image switching buttons
  const img = document.getElementById('trackImage');
  const buttons = document.querySelectorAll('.image-mode-btn');

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;

      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Change the image
      if (img.dataset[mode]) {
        img.src = img.dataset[mode];
      }
    });
  });
});
