# onevents/utils/text.py

import re

# Общие регулярные выражения
SAFE_CHARS_PATTERN = re.compile(r'[^\w\s-]')
DASHES_SPACES_PATTERN = re.compile(r'[-\s]+')

def clean_text(text):
    """Очищает текст от HTML и экранирует специальные символы для ICS"""
    # Убираем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Экранируем специальные символы для ICS
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text


def make_slug(text: str) -> str:
    """Готовит безопасный слаг для имени файла из названия города."""
    safe = SAFE_CHARS_PATTERN.sub('', str(text)).strip()
    safe = DASHES_SPACES_PATTERN.sub('-', safe)
    return safe.lower()


def to_hhmmss(time_str: str) -> str:
    """Нормализует время к формату HHMMSS для ICS"""
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
