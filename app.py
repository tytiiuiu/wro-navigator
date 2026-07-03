import streamlit as str
import os
import base64
import json

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Навигатор WRO 2026: Построение траектории")
str.write("Перетаскивай робота мышкой — значения дистанции и угла внизу меняются прямо на лету!")

# 1. Поиск картинки поля
img_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.jfif')
image_file = None
for file in os.listdir('.'):
    if file.lower().endswith(img_extensions) and not file.startswith('processed_'):
        image_file = file
        break

if image_file is None:
    str.error("❌ Картинка поля не найдена в репозитории!")
    str.stop()

# Кодируем картинку в Base64
with open(image_file, "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

# Инициализация координат в памяти Python
if "start_x" not in str.session_state:
    str.session_state.start_x = 200
    str.session_state.start_y = 950  
if "end_x" not in str.session_state:
    str.session_state.end_x = 800
    str.session_state.end_y = 500

# Если нажали фиксацию, обновляем конечную точку в Python
query_params = str.query_params
if "set_coords" in query_params:
    try:
        coords = json.loads(query_params["set_coords"])
        str.session_state.end_x = coords["x2"]
        str.session_state.end_y = coords["y2"]
    except:
        pass

x1, y1 = str.session_state.start_x, str.session_state.start_y
x2, y2 = str.session_state.end_x, str.session_state.end_y

# 2. HTML/JS Движок с мгновенным пересчетом метрик
html_code = f"""
<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    
    <!-- Квадрат 1: СТАРТ -->
    <div id="start_box" style="position: absolute; background: rgba(128,128,128,0.3); border: 2px dashed #ff4b4b; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; pointer-events: none;">СТАРТ</div>
    
    <!-- Квадрат 2: РОБОТ (ФИНИШ) -->
    <div id="end_box" style="position: absolute; background: rgba(128,128,128,0.6); border: 2px solid #00f; cursor: move; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">РОБОТ</div>
</div>

<!-- Блок живых метрик прямо под картой -->
<div style="display: flex; gap: 20px; margin-top: 15px; font-family: sans-serif; background: #1e1e1e; padding: 15px; border-radius: 8px; color: white;">
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">📏 Дистанция до цели (живой расчет):</span>
        <div id="live_dist" style="font-size: 24px; font-weight: bold; color: #ffeb3b;">0.0 мм</div>
    </div>
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">🧭 Градус разворота (живой расчет):</span>
        <div id="live_angle" style="font-size: 24px; font-weight: bold; color: #00e676;">0.0°</div>
    </div>
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">📍 Координаты Робота:</span>
        <div id="live_coords" style="font-size: 18px; margin-top: 5px; font-family: monospace;">X: 0, Y: 0</div>
    </div>
</div>

<script>
const W_MM = {FIELD_WIDTH_MM};
const H_MM = {FIELD_HEIGHT_MM};
const ROB_MM = {ZONE_SIZE_MM};

const img = document.getElementById('field');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');

const bStart = document.getElementById('start_box');
const bEnd = document.getElementById('end_box');

const txtDist = document.getElementById('live_dist');
const txtAngle = document.getElementById('live_angle');
const txtCoords = document.getElementById('live_coords');

let p1 = {{ x: {x1}, y: {y1} }};
let p2 = {{ x: {x2}, y: {y2} }};

function drawScene() {{
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    
    const sizeW = ROB_MM * kW;
    const sizeH = ROB_MM * kH;
    
    bStart.style.width = sizeW + 'px'; bStart.style.height = sizeH + 'px';
    bEnd.style.width = sizeW + 'px'; bEnd.style.height = sizeH + 'px';
    
    bStart.style.left = (p1.x * kW - sizeW/2) + 'px'; bStart.style.top = (p1.y * kH - sizeH/2) + 'px';
    bEnd.style.left = (p2.x * kW - sizeW/2) + 'px'; bEnd.style.top = (p2.y * kH - sizeH/2) + 'px';
    
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.moveTo(p1.x * kW, p1.y * kH);
    ctx.lineTo(p2.x * kW, p2.y * kH);
    ctx.strokeStyle = '#ffeb3b';
    ctx.lineWidth = 3;
    ctx.setLineDash([6, 4]);
    ctx.stroke();

    // МГНОВЕННАЯ МАТЕМАТИКА НА ЛЕТУ
    const dx = p2.x - p1.x;
    const dy = -(p2.y - p1.y); // Инверсия Y для робототехники
    
    const distance = Math.sqrt(dx*dx + dy*dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI);
    
    // Пишем результаты прямо на экран
    txtDist.innerText = distance.toFixed(1) + ' мм';
    txtAngle.innerText = angle.toFixed(1) + '°';
    txtCoords.innerText = 'X: ' + Math.round(p2.x) + ', Y: ' + Math.round(p2.y);

    // Сохраняем в буфер для кнопки фиксации
    localStorage.setItem("wro_pending_x2", Math.round(p2.x));
    localStorage.setItem("wro_pending_y2", Math.round(p2.y));
}}

let isDragging = false;
bEnd.addEventListener('mousedown', (e) => {{ isDragging = true; e.preventDefault(); }});

window.addEventListener('mousemove', (e) => {{
    if (!isDragging) return;
    const rect = img.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    
    p2.x = Math.max(0, Math.min(W_MM, mouseX / kW));
    p2.y = Math.max(0, Math.min(H_MM, mouseY / kH));
    
    drawScene();
}});

window.addEventListener('mouseup', () => {{ isDragging = false; }});

img.onload = drawScene;
window.addEventListener('resize', drawScene);
if (img.complete) drawScene();
</script>
"""

# Выводим интерактивное поле с живыми метриками
import streamlit.components.v1 as components
components.html(html_code, height=640, scrolling=False)

# 3. Фиксация для получения кода Pybricks
str.markdown("---")
if str.button("📍 СГЕНЕРИРОВАТЬ КОД ДЛЯ ЭТОЙ ТОЧКИ (ENTER)", type="primary"):
    js_submit = f"""
    <script>
    const x = localStorage.getItem("wro_pending_x2") || {x2};
    const y = localStorage.getItem("wro_pending_y2") || {y2};
    const res = JSON.stringify({{x2: parseInt(x), y2: parseInt(y)}});
    window.parent.location.search = '?set_coords=' + encodeURIComponent(res);
    </script>
    """
    components.html(js_submit, height=0)

# Математика в Python (для генерации кода блока Pybricks)
dx = x2 - x1
dy = -(y2 - y1)
distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

str.subheader("💻 Зафиксированный код для Pybricks:")
str.code(f"robot.turn({round(angle_deg)})\nrobot.straight({round(distance)})", language="python")
