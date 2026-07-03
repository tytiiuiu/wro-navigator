import streamlit as str
import os
import math
from PIL import Image
import folium
from streamlit_folium import st_folium

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Интерактивный Навигатор WRO 2026")
str.write("Перетаскивай маркеры мышкой или двигай ползунки. Данные обновляются автоматически.")

# Находим картинку поля в папке
img_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.jfif')
image_file = None
for file in os.listdir('.'):
    if file.lower().endswith(img_extensions) and not file.startswith('processed_'):
        image_file = file
        break

if image_file is None:
    str.error("❌ Картинка поля не найдена в папке! Загрузите её в репозиторий.")
    str.stop()

# Открываем изображение через PIL (это гарантирует кроссплатформенность)
img_obj = Image.open(image_file)

# Инициализация точек в памяти
if "robot_start" not in str.session_state:
    str.session_state.robot_start = [400, 400]
if "robot_end" not in str.session_state:
    str.session_state.robot_end = [1000, 600]

# Создаем карту с простой прямоугольной сеткой
m = folium.Map(
    location=[FIELD_HEIGHT_MM / 2, FIELD_WIDTH_MM / 2],
    zoom_start=0,
    crs="Simple", 
    min_zoom=-2,
    max_zoom=3,
    dragging=True
)

# Передаем сам PIL-объект изображения — этот метод поддерживается Folium
bounds = [[0, 0], [FIELD_HEIGHT_MM, FIELD_WIDTH_MM]]
folium.raster_layers.ImageOverlay(image=img_obj, bounds=bounds).add_to(m)

# Рисуем элементы роботов
def add_robot_marker(m, coords, color, name):
    half = ZONE_SIZE_MM / 2
    rect_bounds = [[coords[1] - half, coords[0] - half], [coords[1] + half, coords[0] + half]]
    folium.Rectangle(bounds=rect_bounds, color=color, fill=True, fill_color=color, fill_opacity=0.4).add_to(m)
    folium.Marker(location=[coords[1], coords[0]], draggable=True, tooltip=name).add_to(m)

add_robot_marker(m, str.session_state.robot_start, "red", "Робот Старт")
add_robot_marker(m, str.session_state.robot_end, "blue", "Робот Финиш")

# Линия между роботами
folium.PolyLine(
    locations=[
        [str.session_state.robot_start[1], str.session_state.robot_start[0]],
        [str.session_state.robot_end[1], str.session_state.robot_end[0]]
    ],
    color="yellow", weight=4, opacity=0.8
).add_to(m)

m.fit_bounds(bounds)
map_data = st_folium(m, width=1000, height=500)

# Интерактивные ползунки под картой
str.markdown("---")
str.subheader("🔧 Управление позицией роботов (в миллиметрах):")
col_s1, col_s2, col_e1, col_e2 = str.columns(4)

with col_s1:
    x1 = str.slider("Робот 1 - X", 0, FIELD_WIDTH_MM, int(str.session_state.robot_start[0]))
with col_s2:
    y1 = str.slider("Робот 1 - Y", 0, FIELD_HEIGHT_MM, int(str.session_state.robot_start[1]))
with col_e1:
    x2 = str.slider("Робот 2 - X", 0, FIELD_WIDTH_MM, int(str.session_state.robot_end[0]))
with col_e2:
    y2 = str.slider("Робот 2 - Y", 0, FIELD_HEIGHT_MM, int(str.session_state.robot_end[1]))

str.session_state.robot_start = [x1, y1]
str.session_state.robot_end = [x2, y2]

# Математические расчеты движения
dx = x2 - x1
dy = y2 - y1 
distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

# Красивый вывод результатов расчета
st_col1, st_col2 = str.columns(2)
with st_col1:
    str.metric("📏 Необходимая дистанция", f"{round(distance, 1)} мм")
with st_col2:
    str.metric("🧭 Угол поворота", f"{round(angle_deg, 1)}°")

str.subheader("💻 Код для Pybricks:")
str.code(f"robot.turn({round(angle_deg)})\nrobot.straight({round(distance)})", language="python")
