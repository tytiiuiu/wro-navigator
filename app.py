import streamlit as str
from PIL import Image, ImageDraw
import os
import math

# Реальные размеры поля WRO 2026
FIELD_WIDTH_MM = 2362
FIELD_HEIGHT_MM = 1143
ZONE_SIZE_MM = 250  # 25х25 см = 250х250 мм

str.set_page_config(layout="wide")
str.title("🎯 Навигатор WRO 2026 (Робомиссия)")
str.write("Клик 1: Позиция робота (появится зона 25х25 см). Клик 2: Точка направления взгляда.")

# Ищем картинку в папке
img_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.jfif')
image_file = None
for file in os.listdir('.'):
    if file.lower().endswith(img_extensions) and not file.startswith('processed_'):
        image_file = file
        break

if image_file is None:
    str.error("❌ Картинка поля не найдена в папке 'wro_project'!")
    str.stop()

# Открываем изображение
base_img = Image.open(image_file).convert('RGB')
width_px, height_px = base_img.size

scale_x = FIELD_WIDTH_MM / width_px
scale_y = FIELD_HEIGHT_MM / height_px

# Хранилище точек в памяти страницы
if "wro_points" not in str.session_state:
    str.session_state.wro_points = []

# Создаем копию картинки для рисования сетки и робота
draw_img = base_img.copy()
draw = ImageDraw.Draw(draw_img, "RGBA")

# Рисуем квадрат робота, если поставлена первая точка
if len(str.session_state.wro_points) >= 1:
    p1 = str.session_state.wro_points[0]
    rect_w_px = ZONE_SIZE_MM / scale_x
    rect_h_px = ZONE_SIZE_MM / scale_y
    
    left = p1[0] - rect_w_px / 2
    top = p1[1] - rect_h_px / 2
    right = p1[0] + rect_w_px / 2
    bottom = p1[1] + rect_h_px / 2
    
    # Серый квадрат робота 25х25 см
    draw.rectangle([left, top, right, bottom], fill=(128, 128, 128, 100), outline=(255, 0, 0, 255), width=3)
    draw.ellipse([p1[0]-5, p1[1]-5, p1[0]+5, p1[1]+5], fill="red")

# Рисуем линию направления взгляда, если поставлена вторая точка
if len(str.session_state.wro_points) == 2:
    p2 = str.session_state.wro_points[1]
    draw.line([str.session_state.wro_points[0], p2], fill="yellow", width=4)
    draw.ellipse([p2[0]-5, p2[1]-5, p2[0]+5, p2[1]+5], fill="yellow")

# Вывод карты на экран
from streamlit_image_coordinates import streamlit_image_coordinates
value = streamlit_image_coordinates(draw_img, key="wro_click_map")

# Логика обработки кликов
if value:
    new_point = (value["x"], value["y"])
    if not str.session_state.wro_points or str.session_state.wro_points[-1] != new_point:
        if len(str.session_state.wro_points) >= 2:
            str.session_state.wro_points = []  # Сброс, если это уже третий клик
        str.session_state.wro_points.append(new_point)
        str.rerun()

# Считаем результаты, когда точки установлены
if len(str.session_state.wro_points) >= 1:
    p1 = str.session_state.wro_points[0]
    x1_mm = p1[0] * scale_x
    y1_mm = p1[1] * scale_y
    
    col1, col2 = str.columns(2)
    with col1:
        str.metric("🤖 Позиция робота (Точка 1)", f"X: {round(x1_mm)} мм | Y: {round(y1_mm)} мм")
    
    if len(str.session_state.wro_points) == 2:
        p2 = str.session_state.wro_points[1]
        x2_mm = p2[0] * scale_x
        y2_mm = p2[1] * scale_y
        
        dx = x2_mm - x1_mm
        dy = -(y2_mm - y1_mm)  # Переворачиваем Y для стандартных тригонометрических углов
        
        distance = (dx**2 + dy**2) ** 0.5
        angle_deg = math.degrees(math.atan2(dy, dx))
        
        with col2:
            str.metric("📏 Дистанция до Точки 2", f"{round(distance)} мм")
            str.metric("🧭 Куда направить робота (Угол)", f"{round(angle_deg)}°")
            
        str.subheader("💻 Готовый код для твоего робота WRO:")
        code_box = f"""# Направление взгляда и движение через одометрию
robot.turn({round(angle_deg)})       # Поворот в направлении точки
robot.straight({round(distance)})   # Едем точно туда в миллиметрах
"""
        str.code(code_box, language="python")

if str.button("🧹 Сбросить точки"):
    str.session_state.wro_points = []
    str.rerun()