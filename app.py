import streamlit as str
import os
import base64
import json

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🚀 Про-Навигатор WRO 2026: Мульти-маршрут")
str.write("Кликни на поле, чтобы построить цепочку шагов. Выбирай тип движения для каждой точки, вращай робота.")

# Скрытый буфер синхронизации координат
incoming_data = str.sidebar.text_area("Системный буфер точек", value="", key="js_pts_buffer", label_visibility="collapsed")

# Инициализация точек в сессии Streamlit
if "waypoints" not in str.session_state:
    str.session_state.waypoints = [
        {"x": 200, "y": 950, "type": "straight", "comment": "Старт"},
        {"x": 800, "y": 500, "type": "straight", "comment": "Первая миссия"}
    ]

# Перехват координат из буфера
if incoming_data:
    try:
        parsed = json.loads(incoming_data)
        if "points" in parsed:
            str.session_state.waypoints = parsed["points"]
    except:
        pass

if "start_angle" not in str.session_state:
    str.session_state.start_angle = 0

# Базовый шаблон инициализации по умолчанию
default_init = """from pybricks.robotics import DriveBase
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port

# Твоя конфигурация робота
left_motor = Motor(Port.A)
right_motor = Motor(Port.B)
robot = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=114)
line_sensor = ColorSensor(Port.C)"""

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

with open(image_file, "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

# 2. Настройки в Sidebar
str.sidebar.header("⚙️ Глобальные настройки")

custom_init_code = str.sidebar.text_area(
    "🤖 Блок инициализации (Pybricks):",
    value=default_init,
    height=200,
    help="При изменении этого текста цепочка шагов больше не сбросится!"
)

# Безопасное экранирование строк
safe_init_code = custom_init_code.replace("\n", "\\n").replace("'", "\\'")

# Функционал Экспорта / Импорта маршрута в Sidebar
str.sidebar.markdown("### 💾 Сохранение траектории")
col_exp, col_imp = str.sidebar.columns(2)

with col_exp:
    route_json_string = json.dumps(str.session_state.waypoints, indent=2, ensure_ascii=False)
    str.download_button(
        label="📥 Скачать JSON",
        data=route_json_string,
        file_name="wro_route.json",
        mime="application/json",
        use_container_width=True
    )

with col_imp:
    uploaded_file = str.file_uploader("Загрузить JSON", type=["json"], label_visibility="collapsed")
    if uploaded_file is not None:
        try:
            str.session_state.waypoints = json.load(uploaded_file)
            str.rerun()
        except:
            str.sidebar.error("Ошибка чтения JSON файла")

str.sidebar.markdown("---")
str.sidebar.header("📝 Настройка шагов маршрута")
updated_points = list(str.session_state.waypoints)

# Переменная для отслеживания активной (раскрытой) точки в UI
active_index = len(updated_points) - 1 

for i, pt in enumerate(updated_points):
    expander_label = f"📍 Точка {i+1}: {pt.get('comment', '') or 'Без имени'}"
    is_expanded = (i == len(updated_points)-1)
    
    with str.sidebar.expander(expander_label, expanded=is_expanded):
        if is_expanded:
            active_index = i
            
        if i == 0:
            pt["comment"] = str.text_input(f"Заметка {i+1}", value=pt.get("comment", "Старт"), key=f"c_{i}")
        else:
            pt["comment"] = str.text_input(f"Заметка {i+1}", value=pt.get("comment", f"Шаг {i}"), key=f"c_{i}")
            move_mode = str.radio(
                f"Тип движения {i+1}:",
                ["1. Простой код (Дистанция)", "2. Калибровка (До линии)"],
                index=0 if pt.get("type", "straight") == "straight" else 1,
                key=f"t_{i}"
            )
            pt["type"] = "straight" if "1." in move_mode else "color_sensor"

str.session_state.waypoints = updated_points

# Слайдер начального направления
str.markdown("### 🧭 Начальное направление робота:")
angle_slider = str.slider("Задать угол стрелки старта (градусы):", -180, 180, int(str.session_state.start_angle), step=5)
str.session_state.start_angle = angle_slider

points_json = json.dumps(str.session_state.waypoints)

# 3. HTML / JS Интерфейс
html_code = f"""
<style>
.modal-overlay {{
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.75);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999;
    font-family: sans-serif;
    opacity: 0;
    display: none;
    transition: opacity 0.3s ease;
}}
.modal-window {{
    background: #1e1e24;
    color: #e6edf3;
    padding: 30px;
    border-radius: 12px;
    max-width: 550px;
    width: 90%;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    border: 1px solid #464855;
    text-align: center;
}}
.modal-window h2 {{
    color: #00e676;
    margin-top: 0;
}}
.modal-window ul {{
    text-align: left;
    line-height: 1.6;
    font-size: 14px;
    margin-bottom: 25px;
}}
.modal-btn {{
    background: #00e676;
    color: #0e1117;
    border: none;
    padding: 12px 40px;
    font-size: 16px;
    font-weight: bold;
    border-radius: 6px;
    cursor: pointer;
}}
.modal-btn:hover {{ background: #00b357; }}

@keyframes pulse-glow {{
    0% {{ box-shadow: 0 0 5px #00e676, inset 0 0 5px #00e676; }}
    50% {{ box-shadow: 0 0 20px #00e676, inset 0 0 15px #00e676; border-color: #00e676 !important; }}
    100% {{ box-shadow: 0 0 5px #00e676, inset 0 0 5px #00e676; }}
}}
.active-robot {{
    animation: pulse-glow 2s infinite ease-in-out;
    background: rgba(0, 230, 118, 0.35) !important;
}}
</style>

<div id="instruction_modal" class="modal-overlay">
    <div class="modal-window">
        <h2>🤖 Инструкция к Про-Навигатору</h2>
        <p>Добро пожаловать в генератор траекторий WRO 2026! Вот как с ним работать:</p>
        <ul>
            <li>📍 <b>Перетаскивание:</b> Двигай кубики робота по полю мышкой или пальцем на планшете.</li>
            <li>➕ <b>Управление шагами:</b> Используй кнопки под картой для гибкого изменения маршрута.</li>
            <li>⚙️ <b>Подсветка шага:</b> Активная точка, открытая в левой панели, будет мягко пульсировать зелёным неоном на поле!</li>
            <li>💾 <b>Сохранение:</b> Ты можешь скачать траекторию в файл JSON и загрузить её обратно в любой день.</li>
        </ul>
        <button class="modal-btn" id="btn_modal_ok">OK</button>
    </div>
</div>

<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5;"></canvas>
    <div id="boxes_container"></div>
</div>

<div style="display: flex; gap: 15px; margin-top: 15px; font-family: sans-serif; flex-wrap: wrap;">
    <button id="btn_add" style="background: #28a745; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">➕ Добавить точку</button>
    <button id="btn_pop" style="background: #dc3545; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">❌ Удалить последнюю</button>
    <button id="btn_clear" style="background: #6c757d; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">🧹 Очистить всё</button>
</div>

<!-- Окно с кодом -->
<div style="margin-top: 25px; font-family: sans-serif; position: relative; max-width: 1100px;">
    <div style="display: flex; justify-content: space-between; align-items: center; background: #262730; padding: 10px 15px; border-radius: 6px 6px 0 0; border: 1px solid #464855; border-bottom: none;">
        <span style="color: white; font-weight: bold; font-size: 14px;">💻 Нативный код Pybricks (Обновляется в реальном времени):</span>
        <button id="btn_copy" style="background: #1e1e1e; color: #00e676; border: 1px solid #00e676; padding: 5px 12px; font-size: 12px; font-weight: bold; border-radius: 4px; cursor: pointer;">📋 Скопировать код</button>
    </div>
    <pre id="live_code" style="background: #0e1117; padding: 15px; border-radius: 0 0 6px 6px; border: 1px solid #464855; color: #e6edf3; font-family: monospace; font-size: 14px; margin: 0; line-height: 1.5; white-space: pre-wrap; overflow-x: auto; max-height: 400px;"></pre>
</div>

<script>
const W_MM = {FIELD_WIDTH_MM};
const H_MM = {FIELD_HEIGHT_MM};
const ROB_MM = {ZONE_SIZE_MM};
const SNAP_THRESHOLD = 3.5;
const activeIndexFromPython = {active_index};

const img = document.getElementById('field');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');
const boxesContainer = document.getElementById('boxes_container');
const blockCode = document.getElementById('live_code');
const btnCopy = document.getElementById('btn_copy');
const modal = document.getElementById('instruction_modal');
const btnModalOk = document.getElementById('btn_modal_ok');

let pts = {points_json};
let startAngleDeg = {angle_slider};
let customInit = '{safe_init_code}';

if (!localStorage.getItem('wro_navigator_visited')) {{
    modal.style.display = 'flex';
    setTimeout(() => {{ modal.style.opacity = '1'; }}, 50);
}}

btnModalOk.addEventListener('click', () => {{
    modal.style.opacity = '0';
    localStorage.setItem('wro_navigator_visited', 'true');
    setTimeout(() => {{ modal.style.display = 'none'; }}, 300);
}});

function syncPointsToPython() {{
    const parentData = {{ points: pts }};
    const buffer = window.parent.document.querySelector('textarea[aria-label="Системный буфер точек"]');
    if(buffer) {{
        buffer.value = JSON.stringify(parentData);
        buffer.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
}}

function drawScene() {{
    const kW = img.clientWidth / W_MM;
    const kH = img.clientHeight / H_MM;
    const sizeW = ROB_MM * kW;
    const sizeH = ROB_MM * kH;

    boxesContainer.innerHTML = '';
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let currentAngle = startAngleDeg;
    let pybricksCode = "# Робот собран с помощью Живого Навигатора WRO 2026\\n" + customInit + "\\n\\n# --- ПОСТРОЕННЫЙ МАРШРУТ ---\\n";

    for(let i=0; i < pts.length; i++) {{
        let p = pts[i];
        
        if (i > 0) {{
            let prev = pts[i-1];
            let dx = p.x - prev.x;
            let dy = -(p.y - prev.y);
            let distance = Math.sqrt(dx*dx + dy*dy);
            
            if (distance > 5) {{
                let moveAngle = Math.atan2(dy, dx) * (180 / Math.PI);
                let turnAngle = moveAngle - currentAngle;
                
                turnAngle = (turnAngle + 180) % 360;
                if (turnAngle < 0) turnAngle += 360;
                turnAngle -= 180;

                const targets = [-180, -135, -90, -45, 0, 45, 90, 135, 180];
                for (let t of targets) {{
                    if (Math.abs(turnAngle - t) <= SNAP_THRESHOLD) {{
                        turnAngle = t;
                        let absoluteTargetAngle = turnAngle + currentAngle;
                        let rad = absoluteTargetAngle * (Math.PI / 180);
                        p.x = prev.x + distance * Math.cos(rad);
                        p.y = prev.y - distance * Math.sin(rad);
                        dx = p.x - prev.x;
                        dy = -(p.y - prev.y);
                        break;
                    }}
                }}

                currentAngle = currentAngle + turnAngle;
                
                let comm = p.comment ? "# " + p.comment + "\\n" : "";
                pybricksCode += comm + "robot.turn(" + Math.round(turnAngle) + ")\\n";
                
                if(p.type === "color_sensor") {{
                    pybricksCode += "# Калибровка: едем до черной линии\\nrobot.drive(200, 0)\\nwhile line_sensor.reflection() > 15:\\n    pass\\nrobot.stop()\\n\\n";
                }} else {{
                    pybricksCode += "robot.straight(" + Math.round(distance) + ")\\n\\n";
                }}

                ctx.beginPath();
                ctx.moveTo(prev.x * kW, prev.y * kH);
                ctx.lineTo(p.x * kW, p.y * kH);
                ctx.strokeStyle = '#ffeb3b';
                ctx.lineWidth = 3;
                ctx.setLineDash([6, 4]);
                ctx.stroke();
            }}
        }}

        const box = document.createElement('div');
        box.style.position = 'absolute';
        box.style.width = sizeW + 'px';
        box.style.height = sizeH + 'px';
        box.style.left = (p.x * kW - sizeW/2) + 'px';
        box.style.top = (p.y * kH - sizeH/2) + 'px';
        box.style.boxSizing = 'border-box';
        box.style.display = 'flex';
        box.style.alignItems = 'center';
        box.style.justifyContent = 'center';
        box.style.color = 'white';
        box.style.fontWeight = 'bold';
        box.style.fontSize = '12px';
        box.style.transform = "rotate(" + (-currentAngle + 90) + "deg)";

        if (i === activeIndexFromPython) {{
            box.classList.add('active-robot');
        }}

        if (i === 0) {{
            if (!box.classList.contains('active-robot')) {{
                box.style.background = 'rgba(255, 75, 75, 0.4)';
                box.style.border = '2px solid #ff4b4b';
            }}
            box.innerHTML = '<div style="position:relative; width:100%; height:100%; display:flex; align-items:center; justify-content:center;"><span style="z-index:2; margin-top:-10px;">СТАРТ</span><div style="position:absolute; width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-bottom:20px solid #ffeb3b; transform:translateY(-5px); z-index:1;"></div></div>';
        }} else if (i === pts.length - 1) {{
            if (!box.classList.contains('active-robot')) {{
                box.style.background = 'rgba(0, 0, 255, 0.4)';
                box.style.border = '2px solid #00f';
            }}
            box.innerText = p.type === "color_sensor" ? "👁️ ЛИНИЯ" : "🤖 РОБОТ";
        }} else {{
            if (!box.classList.contains('active-robot')) {{
                box.style.background = 'rgba(255, 235, 59, 0.25)';
                box.style.border = '2px dashed #ffeb3b';
            }}
            box.innerText = i + 1;
            box.style.color = '#ffeb3b';
        }}

        boxesContainer.appendChild(box);
        setupDragAndTouch(box, p);
    }}
    
    blockCode.innerText = pybricksCode;
}}

function setupDragAndTouch(el, pObject) {{
    let isDragging = false;

    const moveHandler = (clientX, clientY) => {{
        const rect = img.getBoundingClientRect();
        const mouseX = clientX - rect.left;
        const mouseY = clientY - rect.top;
        const kW = img.clientWidth / W_MM;
        const kH = img.clientHeight / H_MM;
        
        pObject.x = Math.max(0, Math.min(W_MM, mouseX / kW));
        pObject.y = Math.max(0, Math.min(H_MM, mouseY / kH));
        drawScene();
    }};

    el.addEventListener('mousedown', (e) => {{ isDragging = true; e.preventDefault(); }});
    window.addEventListener('mousemove', (e) => {{ if (isDragging) moveHandler(e.clientX, e.clientY); }});
    window.addEventListener('mouseup', () => {{ if(isDragging) {{ isDragging = false; syncPointsToPython(); }} }});

    el.addEventListener('touchstart', (e) => {{ isDragging = true; }}, {{ passive: true }});
    window.addEventListener('touchmove', (e) => {{ 
        if (isDragging && e.touches.length > 0) {{
            moveHandler(e.touches[0].clientX, e.touches[0].clientY);
        }}
    }}, {{ passive: true }});
    window.addEventListener('touchend', () => {{ if(isDragging) {{ isDragging = false; syncPointsToPython(); }} }});
}}

btnCopy.addEventListener('click', () => {{
    navigator.clipboard.writeText(blockCode.innerText).then(() => {{
        btnCopy.innerText = "✅ Скопировано!";
        btnCopy.style.color = "#fff";
        btnCopy.style.background = "#00e676";
        setTimeout(() => {{
            btnCopy.innerText = "📋 Скопировать код";
            btnCopy.style.color = "#00e676";
            btnCopy.style.background = "#1e1e1e";
        }}, 1500);
    }});
}});

document.getElementById('btn_add').addEventListener('click', () => {{
    let last = pts[pts.length - 1];
    pts.push({{ x: Math.min(W_MM, last.x + 200), y: Math.max(0, last.y - 200), type: "straight", comment: "Шаг " + (pts.length) }});
    drawScene();
    syncPointsToPython();
}});

document.getElementById('btn_pop').addEventListener('click', () => {{
    if(pts.length > 2) {{
        pts.pop();
        drawScene();
        syncPointsToPython();
    }}
}});

document.getElementById('btn_clear').addEventListener('click', () => {{
    pts = [
        {{ "x": 200, "y": 950, "type": "straight", "comment": "Старт" }},
        {{ "x": 500, "y": 500, "type": "straight", "comment": "Точка 2" }}
    ];
    drawScene();
    syncPointsToPython();
}});

img.onload = drawScene;
window.addEventListener('resize', drawScene);
if (img.complete) drawScene();
</script>
"""

import streamlit.components.v1 as components
components.html(html_code, height=1200, scrolling=False)
