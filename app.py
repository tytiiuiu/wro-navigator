import streamlit as str
import os
import base64

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Живой Навигатор WRO 2026")
str.write("Свободно перетаскивай оба квадрата. Наведи мышь на СТАРТ и покрути колёсико (или используй ползунок ниже), чтобы задать начальный угол робота!")

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

# Начальные дефолтные позиции (в мм)
START_X = 200
START_Y = 950
END_X = 800
END_Y = 500

# 2. Монолитный HTML/JS интерфейс
html_code = f"""
<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    
    <!-- Квадрат 1: СТАРТ со стрелкой направления внутри -->
    <div id="start_box" style="position: absolute; background: rgba(255, 75, 75, 0.4); border: 2px solid #ff4b4b; cursor: move; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 11px;">
        <div style="position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
            <span style="z-index: 2; margin-top: -15px;">СТАРТ</span>
            <!-- Стрелка направления -->
            <div id="arrow" style="position: absolute; width: 0; height: 0; border-left: 8px solid transparent; border-right: 8px solid transparent; border-bottom: 25px solid #ffeb3b; transform: rotate(0deg); transform-origin: center 12.5px; z-index: 1;"></div>
        </div>
    </div>
    
    <!-- Квадрат 2: РОБОТ (ФИНИШ) -->
    <div id="end_box" style="position: absolute; background: rgba(0, 0, 255, 0.4); border: 2px solid #00f; cursor: move; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">РОБОТ</div>
</div>

<!-- Блок живых метрик -->
<div style="display: flex; gap: 20px; margin-top: 15px; font-family: sans-serif; background: #1e1e1e; padding: 15px; border-radius: 8px; color: white;">
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">📏 Дистанция пути:</span>
        <div id="live_dist" style="font-size: 24px; font-weight: bold; color: #ffeb3b;">0.0 мм</div>
    </div>
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">🧭 Итоговый угол разворота:</span>
        <div id="live_angle" style="font-size: 24px; font-weight: bold; color: #00e676;">0.0°</div>
        <div id="snap_info" style="font-size: 11px; color: #ffeb3b; height: 14px; margin-top: 2px;"></div>
    </div>
    <div style="flex: 1;">
        <span style="color: #aaa; font-size: 14px;">📍 Ориентация старта:</span>
        <div id="live_start_angle" style="font-size: 24px; font-weight: bold; color: #29b6f6;">0°</div>
    </div>
</div>

<!-- Живой генератор кода для Pybricks -->
<div style="margin-top: 15px; font-family: sans-serif;">
    <h3 style="color: white; margin-bottom: 5px; font-size: 18px;">💻 Мгновенный код для Pybricks:</h3>
    <pre id="live_code" style="background: #0e1117; padding: 15px; border-radius: 5px; border: 1px solid #30363d; color: #e6edf3; font-family: monospace; font-size: 14px; margin: 0; line-height: 1.5;"></pre>
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
const arrow = document.getElementById('arrow');

const txtDist = document.getElementById('live_dist');
const txtAngle = document.getElementById('live_angle');
const txtStartAngle = document.getElementById('live_start_angle');
const snapInfo = document.getElementById('snap_info');
const blockCode = document.getElementById('live_code');

let p1 = {{ x: {START_X}, y: {START_Y} }};
let p2 = {{ x: {END_X}, y: {END_Y} }};
let startAngleDeg = 0; // Направление старта в тригонометрических градусах (0 - вправо/восток)

function drawScene() {{
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    const sizeW = ROB_MM * kW;
    const sizeH = ROB_MM * kH;
    
    bStart.style.width = sizeW + 'px'; bStart.style.height = sizeH + 'px';
    bEnd.style.width = sizeW + 'px'; bEnd.style.height = sizeH + 'px';
    
    bStart.style.left = (p1.x * kW - sizeW/2) + 'px'; bStart.style.top = (p1.y * kH - sizeH/2) + 'px';
    bEnd.style.left = (p2.x * kW - sizeW/2) + 'px'; bEnd.style.top = (p2.y * kH - sizeH/2) + 'px';
    
    // Поворот стрелки в CSS (в CSS 0 градусов — это ВВЕРХ, поэтому корректируем на +90 относительно тригонометрии)
    arrow.style.transform = `rotate(${{-startAngleDeg + 90}}deg)`;
    txtStartAngle.innerText = Math.round(startAngleDeg) + '°';
    
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

    // ЖИВАЯ ТРИГОНОМЕТРИЯ
    const dx = p2.x - p1.x;
    const dy = -(p2.y - p1.y); 
    
    const distance = Math.sqrt(dx*dx + dy*dy);
    // Абсолютный угол вектора движения
    let moveAngle = Math.atan2(dy, dx) * (180 / Math.PI);
    
    // ТРЕБУЕМЫЙ ПОВОРОТ = Угол движения минус начальный угол робота
    let turnAngle = moveAngle - startAngleDeg;
    
    // Нормализуем в диапазон от -180 до 180 градусов
    while (turnAngle > 180) turnAngle -= 360;
    while (turnAngle <= -180) turnAngle += 360;
    
    // АВТОВЫРАВНИВАНИЕ НА 90 ГРАДУСОВ (макс погрешность 2 градуса)
    let finalAngle = turnAngle;
    let snaped = false;
    
    const targets = [-180, -135, -90, -45, 0, 45, 90, 135, 180];
    for (let t of targets) {{
        if (Math.abs(turnAngle - t) <= 2) {{
            finalAngle = t;
            snaped = true;
            break;
        }}
    }}
    
    if (snaped) {{
        snapInfo.innerText = `🧲 Сработало автовыравнивание на ${{finalAngle}}° (погрешность < 2°)`;
    }} else {{
        snapInfo.innerText = "";
    }}
    
    txtDist.innerText = distance.toFixed(1) + ' мм';
    txtAngle.innerText = finalAngle.toFixed(1) + '°';

    blockCode.innerText = `robot.turn(${{Math.round(finalAngle)}})\\nrobot.straight(${{Math.round(distance)}})`;
    
    // Сохраняем в глобальное окно, чтобы синхронизировать с внешним ползунком Streamlit
    window.currentStartAngle = startAngleDeg;
}}

// Изменение угла СТАРТа колесиком мыши
bStart.addEventListener('wheel', (e) => {{
    e.preventDefault();
    if (e.deltaY < 0) {{
        startAngleDeg = (startAngleDeg + 5) % 360;
    }} else {{
        startAngleDeg = (startAngleDeg - 5 + 360) % 360;
    }}
    drawScene();
}});

function setupDrag(el, pObject) {{
    let isDragging = false;
    el.addEventListener('mousedown', (e) => {{ 
        if(e.target === arrow || e.target.parentNode === arrow) return; // Не мешаем колесику
        isDragging = true; 
        e.preventDefault(); 
    }});
    
    window.addEventListener('mousemove', (e) => {{
        if (!isDragging) return;
        const rect = img.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const kW = img.clientWidth / W_MM;
        const kH = img.clientHeight / H_MM;
        
        pObject.x = Math.max(0, Math.min(W_MM, mouseX / kW));
        pObject.y = Math.max(0, Math.min(H_MM, mouseY / kH));
        
        drawScene();
    }});
    
    window.addEventListener('mouseup', () => {{ isDragging = false; }});
}}

setupDrag(bStart, p1);
setupDrag(bEnd, p2);

img.onload = drawScene;
window.addEventListener('resize', drawScene);
if (img.complete) drawScene();

// Слушаем изменения угла от ползунка Streamlit
window.addEventListener('message', (e) => {{
    if(e.data && e.data.type === 'set_angle') {{
        startAngleDeg = e.data.angle;
        drawScene();
    }}
}});
</script>
"""

# Отрисовка интерактивного HTML поля
import streamlit.components.v1 as components
components.html(html_code, height=760, scrolling=False)

# Слайдер для дублирования управления углом (если у кого-то нет мышки с колесиком)
str.markdown("### 🧭 Точная настройка начального направления робота:")
angle_slider = str.slider("Направление робота на старте (в градусах):", -180, 180, 0, step=5)

# Передаем значение из слайдера обратно в JS-компонент на лету
js_bridge = f"""
<script>
window.parent.postMessage({{type: 'set_angle', angle: {angle_slider}}}, '*');
</script>
"""
components.html(js_bridge, height=0)
