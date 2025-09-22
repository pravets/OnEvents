import os
import yaml
from datetime import datetime
from datetime import date
from datetime import timedelta
from pathlib import Path
from babel.dates import format_date
import shutil
import hashlib
import re

# Пути
EVENTS_DIR = Path("events")
TEMPLATE_FILE = Path("web/index.html")
OUTPUT_DIR = Path("site")
OUTPUT_FILE = OUTPUT_DIR / "index.html"

# Загружаем шаблон
template = TEMPLATE_FILE.read_text(encoding="utf-8")

# Список событий
events = []

for file in EVENTS_DIR.glob("*.yml"):
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    event_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    if event_date >= datetime.today().date():
        events.append(data)

# Сортируем по дате
events.sort(key=lambda e: e["date"])

# Функция генерации ICS файла для события
def generate_ics_content(event):
    """Генерирует содержимое .ics файла для события"""
    
    # Создаем уникальный UID на основе данных события
    uid_string = f"{event['title']}-{event['date']}-{event['city']}"
    uid = hashlib.md5(uid_string.encode('utf-8')).hexdigest() # NOSONAR
    
    # Формируем адрес
    location = event['city']
    if event['address']:
        location += f", {event['address']}"
    
    # Очищаем текст от HTML и специальных символов для ICS
    def clean_text(text):
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        # Экранируем специальные символы для ICS
        text = text.replace('\\', '\\\\')
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')
        text = text.replace('\n', '\\n')
        return text
    
    title = clean_text(event['title'])
    description = clean_text(event['description'])
    
    # Проверяем, есть ли секция sessions для события
    if 'sessions' in event and event['sessions']:
        sessions = event['sessions']
        # Сортируем сессии по дате
        sessions.sort(key=lambda x: x['date'])
        
        # Формируем ICS содержимое с несколькими VEVENT
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OnEvents//OnEvents Calendar//RU
CALSCALE:GREGORIAN
METHOD:PUBLISH"""
        
        # Нормализуем время к формату HHMMSS для ICS
        def to_hhmmss(time_str: str) -> str:
            s = str(time_str).strip()
            s = s.replace('.', ':')
            parts = s.split(':')
            if len(parts) == 1:
                hour = parts[0]
                minute = '00'
            else:
                hour = parts[0]
                minute = parts[1]
            hour = hour.zfill(2)
            minute = minute.zfill(2)
            return f"{hour}{minute}00"

        # Создаем отдельный VEVENT для каждой сессии
        for i, session in enumerate(sessions):
            session_date = datetime.strptime(session['date'], "%Y-%m-%d")
            session_uid = f"{uid}-{i+1}"  # Уникальный UID для каждой сессии
            
            # Формируем время начала и окончания (локальное время)
            start_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['start_time'])}"
            end_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['end_time'])}"
            
            # Название сессии с датой
            date_str = format_date(session_date, format="d MMMM", locale="ru")
            session_title = f"{title} ({date_str})"
            
            ics_content += f"""
BEGIN:VEVENT
UID:{session_uid}@onevents.ru
DTSTART:{start_datetime}
DTEND:{end_datetime}
SUMMARY:{session_title}
DESCRIPTION:{description}\\n\\nСсылка на регистрацию: {event['registration_url']}\\n\\nВремя: {session['start_time']}-{session['end_time']}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT"""
        
        ics_content += """
END:VCALENDAR"""
    else:
        # Обычное однодневное событие
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        
        # Формируем ICS содержимое
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OnEvents//OnEvents Calendar//RU
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}@onevents.ru
DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}
SUMMARY:{title}
DESCRIPTION:{description}\\n\\nСсылка на регистрацию: {event['registration_url']}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""
    
    return ics_content

# Функция генерации карточки
def render_event(e):
    date_obj = datetime.strptime(e['date'], "%Y-%m-%d")
    date_str = date_str = format_date(date_obj, format="d MMMM y", locale="ru")  # 15 сентября 2025
    
    
    if len(e['address']) == 0:
      address_str  = e['city']
    else:
      address_str  = e['city'] + ", "  + e['address']
    
    # Генерируем имя файла для .ics
    safe_title = re.sub(r'[^\w\s-]', '', e['title']).strip()
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    ics_filename = f"{e['date']}-{safe_title}.ics"
 
    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event"  data-city="{e['city']}">
      <div class="card-header" style="display:flex; align-items:flex-start; gap:1em;">
        <img class="logo-img" alt="Логотип «{e['title']}»" 
             src="img/{e['icon']}" width="72" height="72" 
             style="border-radius:50%; object-fit:cover;">
        <div class="event-info">
          <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{e['title']}</h2>
          <div class="meta-item">
            <span class="icon">📅</span>
            <time itemprop="startDate" datetime="{e['date']}">{date_str}</time>
          </div>
          <div class="meta-item">
            <span class="icon">📍</span>
            <span itemprop="location" itemscope itemtype="https://schema.org/Place">
              <span itemprop="addressLocality">{address_str}</span>
            </span>
          </div>
        </div>
      </div>
      <p>{e['description']}</p>
      <a href="{e['registration_url']}" role="button" target="_blank">Регистрация</a>
      <a href="calendar/{ics_filename}" role="button" download="{ics_filename}" style="margin-left:0.5rem;">Добавить в календарь</a>
    </article>
    """

# Генерируем HTML
events_html = "\n".join(render_event(e) for e in events)

# Подставляем в шаблон
today_date_str = format_date(date.today(), format="d MMMM y", locale="ru")
result_html = (
    template
    .replace("{{ events }}", events_html)
    .replace("{{ builddate }}", today_date_str)
)

# Создаем папку site при необходимости
OUTPUT_DIR.mkdir(exist_ok=True)

# Сохраняем результат
OUTPUT_FILE.write_text(result_html, encoding="utf-8")

# Копируем картинки
shutil.copytree("img", "site/img", dirs_exist_ok=True)

# Копируем Иконки
shutil.copytree("icons", "site/icons", dirs_exist_ok=True)

# Создаем папку для календарных файлов
calendar_dir = OUTPUT_DIR / "calendar"
calendar_dir.mkdir(exist_ok=True)

# Генерируем .ics файлы для каждого события
for event in events:
    # Генерируем имя файла для .ics
    safe_title = re.sub(r'[^\w\s-]', '', event['title']).strip()
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    ics_filename = f"{event['date']}-{safe_title}.ics"
    
    # Генерируем содержимое .ics файла
    ics_content = generate_ics_content(event)
    
    # Сохраняем .ics файл
    ics_file_path = calendar_dir / ics_filename
    ics_file_path.write_text(ics_content, encoding="utf-8")
