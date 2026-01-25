// Generate random gradient for hero title
function setRandomGradient() {
  const heroTitle = document.querySelector('.hero-text h1');
  if (!heroTitle) return;

  // Generate random hue values for vibrant colors
  const hue1 = Math.floor(Math.random() * 360);
  const hue2 = (hue1 + 60 + Math.floor(Math.random() * 120)) % 360; // Offset by 60-180 degrees

  // Use HSL for vibrant, saturated colors
  const color1 = `hsl(${hue1}, 85%, 60%)`;
  const color2 = `hsl(${hue2}, 85%, 60%)`;

  // Apply gradient
  const gradient = `linear-gradient(135deg, ${color1} 0%, ${color2} 100%)`;
  heroTitle.style.background = gradient;
  heroTitle.style.webkitBackgroundClip = 'text';
  heroTitle.style.backgroundClip = 'text';
  heroTitle.style.webkitTextFillColor = 'transparent';
}

// Run on page load
document.addEventListener('DOMContentLoaded', setRandomGradient);

