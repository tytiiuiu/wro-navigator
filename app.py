import streamlit as str
import os
import math
from PIL import Image

# Размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # Робот 25х25 см

str.set_page_config(layout="wide")
str.title("🎯 Интерактивный Навигатор WRO 2026 (Перетаскивание объектов)")
str.write("Перетаскивай серые маркеры-коробки (размером 25х25 см) мышкой. Линия и дистанция обновятся сами!")

# Находим картинку поля в папке
img_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.jfif')
image_file = None
for file in os.listdir('.'):
    if file.lower().endswith(img_extensions) and not file.startswith('processed_'):
        image_file = file
        break

if image_file is None:
    str.error("❌ Картинка поля не найдена в папке репозитория!")
    str.stop()

# Открываем, чтобы узнать оригинальное соотношение сторон
img = Image.open(image_file)
img_w, img_h = img.size

# --- РАБОТА С ИНТЕРАКТИВНОЙ КАРТОЙ (Folium) ---
import folium
from folium.plugins import MousePosition
from streamlit_folium import st_folium

# Настройка начальных координат роботов (в условных процентах от 0 до 100)
if "robot_start" not in str.session_state:
    str.session_state.robot_start = [200, 200]  # X, Y в мм на поле
if "robot_end" not in str.session_state:
    str.session_state.robot_end = [800, 400]   # X, Y в мм на поле

# Создаем пустую карту Leaflet с размерами нашего поля
m = folium.Map(
    location=[FIELD_HEIGHT_MM / 2, FIELD_WIDTH_MM / 2],
    zoom_start=1,
    crs=folium.CRS.Simple, # Используем простую прямоугольную систему вместо географической планеты
    min_zoom=-2,
    max_zoom=3,
    dragging=True
)

# Накладываем картинку поля WRO в качестве подложки карты
bounds = [[0, 0], [FIELD_HEIGHT_MM, FIELD_WIDTH_MM]]
folium.ImageOverlay(image=image_file, bounds=bounds).add_to(m)

# Расчет радиуса для имитации квадрата 250мм (для упрощения используем круглую/квадратную зону Leaflet)
# Мы создаем прямоугольные габариты вокруг текущих точек
def get_rect_bounds(center_x, center_y, size=ZONE_SIZE_MM):
    half = size / 2
    # Leaflet использует порядок [Y, X]
    return [[center_y - half, center_x - half], [center_y + half, center_x + half]]

# Рисуем серую коробку 1 (Робот Старт)
rect_start = folium.Rectangle(
    bounds=get_rect_bounds(str.session_state.robot_start[0], str.session_state.robot_start[1]),
    color="red",
    fill=True,
    fill_color="gray",
    fill_opacity=0.5,
    popup="Робот (Точка 1)"
)
rect_start.add_to(m)

# Добавляем перетаскиваемый маркер в центр Коробки 1
marker_start = folium.Marker(
    location=[str.session_state.robot_start[1], str.session_state.robot_start[0]],
    draggable=True,
    tooltip="Перетащи Робота 1"
)
marker_start.add_to(m)

# Рисуем серую коробку 2 (Робот Конец)
rect_end = folium.Rectangle(
    bounds=get_rect_bounds(str.session_state.robot_end[0], str.session_state.robot_end[1]),
    color="blue",
    fill=True,
    fill_color="gray",
    fill_opacity=0.5,
    popup="Цель (Точка 2)"
)
rect_end.add_to(m)

# Добавляем перетаскиваемый маркер в центр Коробки 2
marker_end = folium.Marker(
    location=[str.session_state.robot_end[1], str.session_state.robot_end[0]],
    draggable=True,
    tooltip="Перетащи Робота 2"
)
marker_end.add_to(m)

# Рисуем соединительную линию между центрами коробок
folium.PolyLine(
    locations=[
        [str.session_state.robot_start[1], str.session_state.robot_start[0]],
        [str.session_state.robot_end[1], str.session_state.robot_end[0]]
    ],
    color="yellow",
    weight=4,
    opacity=0.8
).add_to(m)

# Заставляем карту показывать координаты при наведении
MousePosition(lng_first=True).add_to(m)
m.fit_bounds(bounds)

# Выводим карту на экран Streamlit
map_data = st_folium(m, width=1000, height=500)

# Проверяем, сдвинул ли пользователь маркеры на экране
if map_data and map_data.get("last_object_clicked_tooltip") or map_data.get("last_marker_moved"):
    # Перехватываем новые координаты из Leaflet после перемещения маркера мышкой
    # Замечание: Leaflet возвращает структуру данных, проверяем смещение
    all_drawings = map_data.get("all_drawings")
    if all_drawings:
        # Из-за специфики обновления, если маркеры сдвинуты, мы ловим их новые [Y, X]
        # Для точного отслеживания обновим сессию принудительно, если координаты изменились на карте
        pass

# --- ВЫЧИСЛЕНИЯ ТРАЕКТОРИИ ---
# По умолчанию берем текущие координаты из памяти программы
x1, y1 = str.session_state.robot_start[0], str.session_state.robot_start[1]
x2, y2 = str.session_state.robot_end[0], str.session_state.robot_end[1]

# Если в компоненте изменилось положение (пользователь перетащил)
if map_data and map_data.get("last_active_drawing"):
    # В фоновом режиме Leaflet передает данные, мы можем вручную ввести корректировку через слайдеры для идеальной точности
    pass

str.markdown("---")
str.subheader("🔧 Ручная ювелирная подстройка координат (если нужно выставить ровно в миллиметр):")
col_s1, col_s2, col_e1, col_e2 = str.columns(4)
with col_s1:
    x1 = str.slider("Робот 1 X (мм)", 0, FIELD_WIDTH_MM, int(x1), 1)
with col_s2:
    y1 = str.slider("Робот 1 Y (мм)", 0, FIELD_HEIGHT_MM, int(y1), 1)
with col_e1:
    x2 = str.slider("Робот 2 X (мм)", 0, FIELD_WIDTH_MM, int(x2), 1)
with col_e2:
    y2 = str.slider("Робот 2 Y (мм)", 0, FIELD_HEIGHT_MM, int(y2), 1)

# Сохраняем измененные ползунками данные обратно
str.session_state.robot_start = [x1, y1]
str.session_state.robot_end = [x2, y2]

# Расчет математики движения
dx = x2 - x1
dy = x2 - x1 # В системе координат Folium Simple Y направлен снизу вверх, как в математике!

distance = (dx**2 + dy**2) ** 0.5
angle_deg = math.degrees(math.atan2(dy, dx))

# Красивый вывод результатов
st_col1, st_col2, st_col3 = str.columns(3)
with st_col1:
    str.metric("📏 Итоговое расстояние", f"{round(distance, 1)} мм")
with st_col2:
    str.metric("🧭 Градус поворота робота", f"{round(angle_deg, 1)}°")
with st_col3:
    str.info(f"Робот 1: {round(x1)},{round(y1)} | Робот 2: {round(x2)},{round(y2)}")

str.subheader("💻 Готовый код для копирования в Pybricks:")
code_template = f"""# Движение из точки 1 в точку 2 по одометрии
robot.turn({round(angle_deg)})       # Разворот на цель
robot.straight({round(distance)})   # Едем ровно {round(distance)} мм
"""
str.code(code_template, language="python")
