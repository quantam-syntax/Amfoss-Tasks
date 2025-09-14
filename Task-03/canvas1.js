const canvas = document.getElementById("canvas1");
const ctx = canvas.getContext("2d");
const drawaudio = document.getElementById("drawaudio");
drawaudio.loop = true;

const bg = new Image();
bg.src = "background.jpg";

// === SETTINGS ===
const drawColor = "yellow";
const centerDotRadius = 8;
let drawing = false;
let points = [];
let highestScore = 0;

// Resize + redraw background
function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  drawBackground();
  drawCenter();
}
function drawBackground() {
  ctx.drawImage(bg, 0, 0, canvas.width, canvas.height);
}
function drawCenter() {
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  ctx.fillStyle = "red";
  ctx.beginPath();
  ctx.arc(centerX, centerY, centerDotRadius, 0, Math.PI * 2);
  ctx.fill();
}
function clearCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawBackground();
  drawCenter();
}

// Drawing events
canvas.addEventListener("mousedown", (e) => {
  drawing = true;
  points = [];
  clearCanvas();
  const { x, y } = getMousePos(e);
  points.push({ x, y });
  ctx.beginPath();
  ctx.moveTo(x, y);

  drawaudio.currentTime = 0;
  drawaudio.play();
});
canvas.addEventListener("mouseup", () => {
  drawing = false;
  ctx.closePath();
  checkCircle();
  drawaudio.pause();
});
canvas.addEventListener("mousemove", (e) => {
  if (!drawing) return;
  const { x, y } = getMousePos(e);
  points.push({ x, y });
  ctx.lineTo(x, y);
  ctx.strokeStyle = drawColor;
  ctx.lineWidth = 2;
  ctx.stroke();
});

// Helpers
function getMousePos(e) {
  const rect = canvas.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

// Scoring
function checkCircle() {
  if (points.length < 20) return;

  let sumX = 0, sumY = 0;
  points.forEach(p => { sumX += p.x; sumY += p.y; });
  const centerX = sumX / points.length;
  const centerY = sumY / points.length;

  let sumR = 0;
  points.forEach(p => {
    const dx = p.x - centerX;
    const dy = p.y - centerY;
    sumR += Math.sqrt(dx*dx + dy*dy);
  });
  const avgR = sumR / points.length;

  let variance = 0;
  points.forEach(p => {
    const dx = p.x - centerX;
    const dy = p.y - centerY;
    const r = Math.sqrt(dx*dx + dy*dy);
    variance += Math.abs(r - avgR);
  });
  variance /= points.length;

  const fixedX = canvas.width / 2;
  const fixedY = canvas.height / 2;
  const dist = Math.sqrt((fixedX - centerX)**2 + (fixedY - centerY)**2);

  let roundnessScore = Math.max(0, 100 - variance);
  let centerScore = Math.max(0, 100 - dist * 0.5);
  const finalScore = Math.min(100, (roundnessScore * 0.6 + centerScore * 0.4));

  if (finalScore > highestScore) highestScore = finalScore;

  document.getElementById("result").innerText =
    `Score: ${finalScore.toFixed(2)} / 100 | Best: ${highestScore.toFixed(2)} / 100`;

  ctx.strokeStyle = "red";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(centerX, centerY, avgR, 0, Math.PI * 2);
  ctx.stroke();
}

// Init
bg.onload = () => resizeCanvas();
window.addEventListener("resize", resizeCanvas);
