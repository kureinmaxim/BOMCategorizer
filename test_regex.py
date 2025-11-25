import re

def clean_note(note):
    # Паттерн для поиска начала блока замены
    # Ищем: "замена", "допуск. замена", "допускается замена" и т.д.
    replacement_pattern = r'(?i)(?:допуск[\.\s]*замена|допускается\s+замена|замена\s+на|доп[\.\s]*замена|замена)'
    
    match = re.search(replacement_pattern, note)
    if match:
        # Берем все, что было ДО замены
        cleaned = note[:match.start()].strip()
        # Убираем лишние знаки препинания в конце (запятые, точки с запятой)
        cleaned = cleaned.rstrip(';,.\r\n')
        return cleaned
    return note

# Тестовый пример
text = "05К 432–К00S3, ф. Rosenberger\nДопуск. замена: QASNL-FF, ф. Qualwave"
cleaned_text = clean_note(text)
print(f"Original: {text}")
print(f"Cleaned:  '{cleaned_text}'")

