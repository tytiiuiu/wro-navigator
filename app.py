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
str.write("Кликни на поле, чтобы построить цепочку шагов. Выбирай тип движения для каждой точки, вращай робота. Код генерируется ниже!")

# Инициализация углов и точек в сессии Streamlit
if "start_angle" not in str.session_state:
    str.session_state.start_angle = 0
if "waypoints" not in str.session_state:
    str.session_state.waypoints = [
        {"x": 200, "y": 950, "type": "straight", "comment": "Старт"},
        {"x": 800, "y": 500, "type": "straight", "comment": "Первая миссия"}
    ]
if "generated_py_code" not in str.session_state:
    str.session_state.generated_py_code = "# Здесь появится твой код"

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

# 2. Боковая панель управления точками
str.sidebar.header("📝 Настройка шагов маршрута")

# Синхронизация данных (координаты + готовый код) из JS в Python
incoming_data = str.sidebar.text_area("Системный буфер", value="", key="js_data_buffer", label_visibility="collapsed")
if incoming_data:
    try:
        parsed = json.loads(incoming_data)
        str.session_state.waypoints = parsed["points"]
        if "code" in parsed:
            str.session_state.generated_py_code = parsed["code"]
    except:
        pass

# Рендеринг настроек для каждой точки маршрута
updated_points = list(str.session_state.waypoints)
for i, pt in enumerate(updated_points):
    with str.sidebar.expander(f"📍 Точка {i+1}: {pt.get('comment', '') or 'Без имени'}", expanded=(i==len(updated_points)-1)):
        if i == 0:
            pt["comment"] = str.text_input(f"Заметка {i+1}", value=pt.get("comment", "Старт"), key=f"c_{i}")
        else:
            pt["comment"] = str.text_input(f"Заметка {i+1}", value=pt.get("comment", f"Шаг {i}"), key=f"c_{i}")
            move_mode = str.radio(
                f"Тип движения для шага {i+1}:",
                ["1. Простой код (Дистанция)", "2. Калибровка по датчику цвета (До линии)"],
                index=0 if pt.get("type", "straight") == "straight" else 1,
                key=f"t_{i}"
            )
            pt["type"] = "straight" if "1." in move_mode else "color_sensor"

str.session_state.waypoints = updated_points

# Слайдер начального направления
str.markdown("### 🧭 Начальное направление робота:")
angle_slider = str.slider("Задать угол стрелки старта (градусы):", -180, 180, int(str.session_state.start_angle), step=5)
str.session_state.start_angle = angle_slider

# Превращаем точки в JSON для передачи в JavaScript
points_json = json.dumps(str.session_state.waypoints)

# 3. HTML / JS Интерфейс интерактивной карты
html_code = f"""
<div id="container" style="position: relative; inline-block; width: 100%; max-width: 1100px; user-select: none;">
    <img id="field" src="data:image/png;base64,{img_base64}" style="width: 100%; height: auto; display: block;">
    <canvas id="overlay" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5;"></canvas>
    <div id="boxes_container"></div>
</div>

<div style="display: flex; gap: 15px; margin-top: 15px; font-family: sans-serif;">
    <button id="btn_add" style="background: #28a745; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">➕ Добавить точку</button>
    <button id="btn_pop" style="background: #dc3545; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">❌ Удалить последнюю</button>
    <button id="btn_swap" style="background: #007bff; color: white; border: none; padding: 12px 20px; font-size: 15px; font-weight: bold; border-radius: 6px; cursor: pointer;">🔄 Инвертировать путь (Swap)</button>
</div>

<script>
const W_MM = {FIELD_WIDTH_MM};
const H_MM = {FIELD_HEIGHT_MM};
const ROB_MM = {ZONE_SIZE_MM};
const SNAP_THRESHOLD = 3.5;

const img = document.getElementById('field');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');
const boxesContainer = document.getElementById('boxes_container');

let pts = {points_json};
let startAngleDeg = {angle_slider};

function sendDataToPython(currentCode) {{
    const parentData = {{ points: pts, code: currentCode }};
    const buffer = window.parent.document.querySelector('textarea[aria-label="Системный буфер"]');
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
    let pybricksCode = "# Робот собран с помощью Живого Навигатора WRO 2026\\nfrom pybricks.robotics import DriveBase\\nfrom pybricks.pupdevices import Motor, ColorSensor\\nfrom pybricks.parameters import Port\\n\\n# Инициализация\\nleft_motor = Motor(Port.A)\\nright_motor = Motor(Port.B)\\nrobot = DriveBase(left_motor, right_motor, wheel_diameter=56, axle_track=114)\\nline_sensor = ColorSensor(Port.C)\\n\\n";

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

        if (i === 0) {{
            box.style.background = 'rgba(255, 75, 75, 0.4)';
            box.style.border = '2px solid #ff4b4b';
            box.innerHTML = '<div style="position:relative; width:100%; height:100%; display:flex; align-items:center; justify-content:center;"><span style="z-index:2; margin-top:-10px;">СТАРТ</span><div style="position:absolute; width:0; height:0; border-left:6px solid transparent; border-right:6px solid transparent; border-bottom:20px solid #ffeb3b; transform:translateY(-5px); z-index:1;"></div></div>';
        }} else if (i === pts.length - 1) {{
            box.style.background = 'rgba(0, 0, 255, 0.4)';
            box.style.border = '2px solid #00f';
            box.innerText = p.type === "color_sensor" ? "👁️ ЛИНИЯ" : "🤖 РОБОТ";
        }} else {{
            box.style.background = 'rgba(255, 235, 59, 0.25)';
            box.style.border = '2px dashed #ffeb3b';
            box.innerText = i + 1;
            box.style.color = '#ffeb3b';
        }}

        boxesContainer.appendChild(box);
        setupDrag(box, p);
    }}
    
    // Передаем сгенерированный код наружу
    window.currentPybricksCode = pybricksCode;
}}

function setupDrag(el, pObject) {{
    let isDragging = false;
    el.addEventListener('mousedown', (e) => {{ 
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
    
    window.addEventListener('mouseup', () => {{ 
        if(isDragging) {{
            isDragging = false; 
            sendDataToPython(window.currentPybricksCode);
        }}
    }});
}}

document.getElementById('btn_add').addEventListener('click', () => {{
    let last = pts[pts.length - 1];
    pts.push({{ x: Math.min(W_MM, last.x + 200), y: Math.max(0, last.y - 200), type: "straight", comment: "Шаг " + (pts.length) }});
    drawScene();
    sendDataToPython(window.currentPybricksCode);
}});

document.getElementById('btn_pop').addEventListener('click', () => {{
    if(pts.length > 2) {{
        pts.pop();
        drawScene();
        sendDataToPython(window.currentPybricksCode);
    }}
}});

document.getElementById('btn_swap').addEventListener('click', () => {{
    pts.reverse();
    drawScene();
    sendDataToPython(window.currentPybricksCode);
}});

img.onload = () => {{
    drawScene();
    setTimeout(() => sendDataToPython(window.currentPybricksCode), 300);
}};
window.addEventListener('resize', drawScene);
if (img.complete) {{
    drawScene();
    setTimeout(() => sendDataToPython(window.currentPybricksCode), 300);
}}
</script>
"""

import streamlit.components.v1 as components
components.html(html_code, height=760, scrolling=False)

# 4. Вывод готового кода прямо на экран Streamlit (Пункт из твоего запроса)
str.markdown("### 💻 Нативный код Pybricks (Можно сразу копировать):")
str.code(str.session_state.generated_py_code, language="python")
