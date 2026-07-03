import streamlit as str
import os
import math
from PIL import Image
import folium
from folium.plugins import MousePosition
from streamlit_folium import st_folium

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Интерактивный Навигатор WRO 2026")
str.write("Перетаскивай маркеры мышкой. Линия и дистанция обновятся автоматически.")

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

# Инициализация точек
if "robot_start" not in str.session_state:
    str.session_state.robot_start = [400, 400]
if "robot_end" not in str.session_state:
    str.session_state.robot_end = [1000, 600]

# Создаем карту
m = folium.Map(
    location=[FIELD_HEIGHT_MM / 2, FIELD_WIDTH_MM / 2],
    zoom_start=0,
    crs="Simple", 
    min_zoom=-2,
    max_zoom=3,
    dragging=True
)

bounds = [[0, 0], [FIELD_HEIGHT_MM, FIELD_WIDTH_MM]]
folium.ImageOverlay(image=image_file, bounds=bounds).add_to(m)

# Рисуем элементы
def add_robot_marker(m, coords, color, name):
    # Прямоугольник (робот)
    half = ZONE_SIZE_MM / 2
    rect_bounds = [[coords[1] - half, coords[0] - half], [coords[1] + half, coords[0] + half]]
    folium.Rectangle(bounds=rect_bounds, color=color, fill=True, fill_color=color, fill_opacity=0.5).add_to(m)
    # Маркер для перетаскивания
    folium.Marker(location=[coords[1], coords[0]], draggable=True, tooltip=name).add_to(m)

add_robot_marker(m, str.session_state.robot_start, "red", "Робот Старт")
add_robot_marker(m, str.session_state.robot_end, "blue", "Робот Финиш")

# Линия
folium.PolyLine(
    locations=[
        [str.session_state.robot_start[1], str.session_state.robot_start[0]],
        [str.session_state.robot_end[1], str.session_state.robot_end[0]]
    ],
    color="yellow", weight=4, opacity=0.8
).add_to(m)

m.fit_bounds(bounds)
map_data = st_folium(m, width=1000, height=500)

# Ювелирная подстройка
str.markdown("---")
str.subheader("🔧 Ручная подстройка координат (мм):")
col_s1, col_s2, col_e1, col_e2 = str.columns(4)

with col_s1:
    x1 = str.slider("X1", 0, FIELD_WIDTH_MM, int(str.session_state.robot_start[0]))
with col_s2:
    y1 = str.slider("Y1", 0, FIELD_HEIGHT_MM, int(str.session_state.robot_start[1]))
with col_e1:
    x2 = str.slider("X2", 0, FIELD_WIDTH_MM, int(str.session_state.robot_end[0]))
with col_e2:
    y2 = str.slider("Y2", 0, FIELD_HEIGHT_MM, int(str.session_state.robot_end[1]))

str.session_state.robot_start = [x1, y1]
str.session_state.robot_end = [x2, y2]

# Математика
dx = x2 - x1
dy = y2 - y1 
distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

# Результаты
st_col1, st_col2 = str.columns(2)
with st_col1:
    str.metric("📏 Дистанция", f"{round(distance, 1)} мм")
with st_col2:
    str.metric("🧭 Угол", f"{round(angle_deg, 1)}°")

str.subheader("💻 Код для Pybricks:")
str.code(f"robot.turn({round(angle_deg)})\nrobot.straight({round(distance)})", language="python")
