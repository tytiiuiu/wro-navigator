import streamlit as str
import os
import math
import base64
import json
from PIL import Image

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Интерактивный Навигатор WRO 2026")
str.write("Зажми мышкой любой из серых квадратов (роботов) и перетаскивай их по полю!")

# 1. Поиск картинки
img_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.jfif')
image_file = None
for file in os.listdir('.'):
    if file.lower().endswith(img_extensions) and not file.startswith('processed_'):
        image_file = file
        break

if image_file is None:
    str.error("❌ Картинка поля не найдена в репозитории!")
    str.stop()

# 2. Кодируем картинку в Base64 для передачи прямо в браузер (без путей и ошибок)
with open(image_file, "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

# Инициализация координат по умолчанию (в мм)
if "x1" not in str.session_state:
    str.session_state.x1 = 300
    str.session_state.y1 = 300
    str.session_state.x2 = 1500
    str.session_state.y2 = 700

# Получаем данные из JS обратно в Python, если они изменились
query_params = str.query_params
if "data" in query_params:
    try:
        coords = json.loads(query_params["data"])
        str.session_state.x1 = coords["x1"]
        str.session_state.y1 = coords["y1"]
        str.session_state.x2 = coords["x2"]
        str.session_state.y2 = coords["y2"]
    except:
        pass

# 3. Интерактивный HTML/JS движок для плавного перетаскивания (Drag & Drop)
html_code = f"""
<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    
    <!-- Робот 1 (Красный контур) -->
    <div id="rob1" style="position: absolute; background: rgba(128,128,128,0.5); border: 2px solid red; cursor: move; box-sizing: border-box;"></div>
    <!-- Робот 2 (Синий контур) -->
    <div id="rob2" style="position: absolute; background: rgba(128,128,128,0.5); border: 2px solid blue; cursor: move; box-sizing: border-box;"></div>
</div>

<script>
const W_MM = {FIELD_WIDTH_MM};
const H_MM = {FIELD_HEIGHT_MM};
const ROB_MM = {ZONE_SIZE_MM};

const container = document.getElementById('container');
const img = document.getElementById('field');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');

const r1 = document.getElementById('rob1');
const r2 = document.getElementById('rob2');

// Текущие координаты в мм
let p1 = {{ x: {str.session_state.x1}, y: {str.session_state.y1} }};
let p2 = {{ x: {str.session_state.x2}, y: {str.session_state.y2} }};

function updatePositions() {{
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    
    const sizeW = ROB_MM * kW;
    const sizeH = ROB_MM * kH;
    
    // Настраиваем размеры роботов
    r1.style.width = sizeW + 'px'; r1.style.height = sizeH + 'px';
    r2.style.width = sizeW + 'px'; r2.style.height = sizeH + 'px';
    
    // Центрируем коробки по координатам
    r1.style.left = (p1.x * kW - sizeW/2) + 'px'; r1.style.top = (p1.y * kH - sizeH/2) + 'px';
    r2.style.left = (p2.x * kW - sizeW/2) + 'px'; r2.style.top = (p2.y * kH - sizeH/2) + 'px';
    
    // Перерисовываем линию
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.moveTo(p1.x * kW, p1.y * kH);
    ctx.lineTo(p2.x * kW, p2.y * kH);
    ctx.strokeStyle = 'yellow';
    ctx.lineWidth = 4;
    ctx.stroke();
}}

function makeDraggable(el, pObject) {{
    let isDragging = false;
    el.addEventListener('mousedown', (e) => {{ isDragging = true; e.preventDefault(); }});
    
    window.addEventListener('mousemove', (e) => {{
        if (!isDragging) return;
        const rect = img.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        const kW = img.clientWidth / W_MM;
        const kH = img.clientHeight / H_MM;
        
        pObject.x = Math.max(0, Math.min(W_MM, mouseX / kW));
        pObject.y = Math.max(0, Math.min(H_MM, mouseY / kH));
        
        updatePositions();
    }});
    
    window.addEventListener('mouseup', () => {{
        if (isDragging) {{
            isDragging = false;
            // Отправляем новые координаты обратно в Python через URL параметры
            const data = JSON.stringify({{ x1: Math.round(p1.x), y1: Math.round(p1.y), x2: Math.round(p2.x), y2: Math.round(p2.y) }});
            window.parent.location.search = '?data=' + encodeURIComponent(data);
        }}
    }});
}}

img.onload = updatePositions;
window.addEventListener('resize', updatePositions);
if (img.complete) updatePositions();

makeDraggable(r1, p1);
makeDraggable(r2, p2);
</script>
"""

# Отображаем нашу интерактивную карту
import streamlit.components.v1 as components
components.html(html_code, height=550, scrolling=False)

# 4. Математика расчетов движения (на стороне Python)
x1, y1 = str.session_state.x1, str.session_state.y1
x2, y2 = str.session_state.x2, str.session_state.y2

dx = x2 - x1
dy = -(y2 - y1)  # Инвертируем Y для привычной тригонометрии WRO (вверх - плюс)

distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

# Красивый вывод метрик и кода для робота
str.markdown("---")
col1, col2, col3 = str.columns(3)
with col1:
    str.metric("📏 Дистанция пути", f"{round(distance, 1)} мм")
with col2:
    str.metric("🧭 Точный угол поворота", f"{round(angle_deg, 1)}°")
with col3:
    str.info(f"Координаты: Робот 1 [{x1}, {y1}] ➡️ Робот 2 [{x2}, {y2}]")

str.subheader("💻 Готовый код для копирования в Pybricks:")
str.code(f"robot.turn({round(angle_deg)})\nrobot.straight({round(distance)})", language="python")
