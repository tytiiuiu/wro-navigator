import streamlit as str
import os
import math
import base64
import json

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Навигатор WRO 2026: Построение траектории робота")
str.write("Первый квадрат — это Старт. Перетащи второй квадрат в точку Финиша и нажми кнопку фиксации под полем.")

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

# Инициализация координат в памяти (Старт зафиксирован, Финиш двигаем)
if "start_x" not in str.session_state:
    str.session_state.start_x = 200
    str.session_state.start_y = 950  # Например, левый нижний угол поля
if "end_x" not in str.session_state:
    str.session_state.end_x = 800
    str.session_state.end_y = 500

# Перехватываем координаты из JavaScript, если пользователь применил перемещение
query_params = str.query_params
if "set_coords" in query_params:
    try:
        coords = json.loads(query_params["set_coords"])
        str.session_state.end_x = coords["x2"]
        str.session_state.end_y = coords["y2"]
    except:
        pass

# 2. HTML/JS Движок: Старт на месте, Финиш тащится курсором
html_code = f"""
<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    
    <!-- Квадрат 1: СТАРТ (Остается на месте) -->
    <div id="start_box" style="position: absolute; background: rgba(128,128,128,0.3); border: 2px dashed #ff4b4b; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; pointer-events: none;">СТАРТ</div>
    
    <!-- Квадрат 2: ФИНИШ / РОБОТ (Тянется мышкой) -->
    <div id="end_box" style="position: absolute; background: rgba(128,128,128,0.6); border: 2px solid #00f; cursor: move; box-sizing: border-box; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">РОБОТ</div>
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

// Координаты
let p1 = {{ x: {str.session_state.start_x}, y: {str.session_state.start_y} }};
let p2 = {{ x: {str.session_state.end_x}, y: {str.session_state.end_y} }};

function drawScene() {{
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    
    const sizeW = ROB_MM * kW;
    const sizeH = ROB_MM * kH;
    
    // Размеры квадратов 250х250 мм в масштабе экрана
    bStart.style.width = sizeW + 'px'; bStart.style.height = sizeH + 'px';
    bEnd.style.width = sizeW + 'px'; bEnd.style.height = sizeH + 'px';
    
    // Позиционируем по центру координат
    bStart.style.left = (p1.x * kW - sizeW/2) + 'px'; bStart.style.top = (p1.y * kH - sizeH/2) + 'px';
    bEnd.style.left = (p2.x * kW - sizeW/2) + 'px'; bEnd.style.top = (p2.y * kH - sizeH/2) + 'px';
    
    // Рисуем линию пути
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.moveTo(p1.x * kW, p1.y * kH);
    ctx.lineTo(p2.x * kW, p2.y * kH);
    ctx.strokeStyle = '#fff500';
    ctx.lineWidth = 3;
    ctx.setLineDash([6, 4]); // Пунктирная линия пути
    ctx.stroke();
}}

// Логика перетаскивания робота мышкой к курсору
let isDragging = false;
bEnd.addEventListener('mousedown', (e) => {{ isDragging = true; e.preventDefault(); }});

window.addEventListener('mousemove', (e) => {{
    if (!isDragging) return;
    const rect = img.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    
    // Ограничиваем рамками поля
    p2.x = Math.max(0, Math.min(W_MM, mouseX / kW));
    p2.y = Math.max(0, Math.min(H_MM, mouseY / kH));
    
    drawScene();
    
    // Отправляем промежуточные координаты в скрытый инпут для отображения в Python на лету
    window.parent.document.dispatchEvent(new CustomEvent("robot_moving", {{detail: p2}}));
}});

window.addEventListener('mouseup', () => {{
    if (isDragging) {{
        isDragging = false;
        // Сохраняем во временный буфер сессии браузера
        localStorage.setItem("wro_pending_x2", Math.round(p2.x));
        localStorage.setItem("wro_pending_y2", Math.round(p2.y));
    }}
}});

img.onload = drawScene;
window.addEventListener('resize', drawScene);
if (img.complete) drawScene();
</script>
"""

# Выводим интерактивное поле
import streamlit.components.v1 as components
components.html(html_code, height=530, scrolling=False)

# 3. Кнопка "Enter" / Фиксации для точной остановки
x1, y1 = str.session_state.start_x, str.session_state.start_y
x2, y2 = str.session_state.end_x, str.session_state.end_y

str.markdown("### 🕹️ Панель управления точкой:")
col_btn, col_manual_x, col_manual_y = str.columns([2, 2, 2])

with col_btn:
    str.write("") # Отступ
    if str.button("📍 ЗАФИКСИРОВАТЬ ТОЧКУ (ENTER)", type="primary", use_container_width=True):
        # Код для считывания данных из localStorage через JavaScript и перезагрузки страницы с новыми параметрами
        js_submit = """
        <script>
        const x = localStorage.getItem("wro_pending_x2") || Math.round({x2});
        const y = localStorage.getItem("wro_pending_y2") || Math.round({y2});
        const res = JSON.stringify({x2: parseInt(x), y2: parseInt(y)});
        window.parent.location.search = '?set_coords=' + encodeURIComponent(res);
        </script>
        """
        components.html(js_submit, height=0)

with col_manual_x:
    x2 = str.number_input("Финиш X (мм) - точная доводка:", 0, FIELD_WIDTH_MM, int(x2))
with col_manual_y:
    y2 = str.number_input("Финиш Y (мм) - точная доводка:", 0, FIELD_HEIGHT_MM, int(y2))

# Обновляем состояние, если крутили цифры руками
if x2 != str.session_state.end_x or y2 != str.session_state.end_y:
    str.session_state.end_x = x2
    str.session_state.end_y = y2

# 4. Математические вычисления
dx = x2 - x1
dy = -(y2 - y1)  # Делаем Y классическим (вверх - плюс, вниз - минус)

distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

# Результаты на экран
str.markdown("---")
st_col1, st_col2, st_col3 = str.columns(3)
with st_col1:
    str.metric("📏 Дистанция до цели", f"{round(distance, 1)} мм")
with st_col2:
    str.metric("🧭 Градус разворота", f"{round(angle_deg, 1)}°")
with st_col3:
    str.info(f"Старт: [{x1}, {y1}] мм | Конец: [{x2}, {y2}] мм")

str.subheader("💻 Сгенерированный код для Pybricks:")
str.code(f"robot.turn({round(angle_deg)})\nrobot.straight({round(distance)})", language="python")
