 📊 StaffTracker - Система учёта посещаемости сотрудников

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/SQLite-3.8+-orange.svg" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Development-brightgreen.svg" alt="Status">
</p>

## 📋 О проекте

**StaffTracker** - это десктопное приложение для автоматизации учёта рабочего времени сотрудников. Разработано в рамках дипломного проекта по специальности "Информационные системы и программирование".

### 🎯 Основные возможности

- ✅ **Управление сотрудниками** - добавление, редактирование, увольнение
- ⏰ **Учёт посещаемости** - отметка прихода/ухода с автоматической фиксацией времени
- 📊 **Формирование отчётов** - дневные, месячные отчёты, список опозданий
- 📤 **Экспорт в Excel** - выгрузка отчётов в формате .xlsx
- 🏖️ **Учёт отсутствий** - отпуска, больничные, командировки и др.
- 💾 **Резервное копирование** - автоматическое создание бэкапов БД
- 🔒 **Локальное хранение** - все данные хранятся локально в SQLite

### 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│                    (PyQt5 / Tkinter)                        │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
│               (AttendanceService, Employee)                 │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
│                    (Database, DAO)                          │
├─────────────────────────────────────────────────────────────┤
│                    Data Storage Layer                       │
│                    (SQLite Database)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### Требования

- Python 3.7 или выше
- pip (менеджер пакетов Python)

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/yourusername/stafftracker.git
cd stafftracker
```

2. **Установите зависимости**
```bash
pip install -r requirements.txt
```

3. **Запустите приложение**
```bash
python main.py
```

### Сборка EXE

Для создания standalone-приложения:

```bash
# Установка PyInstaller
pip install pyinstaller

# Сборка
pyinstaller --onefile --windowed --name="StaffTracker" main.py
```

Готовый файл будет в папке `dist/`

## 📦 Зависимости

```
PyQt5 >= 5.15.0    # Графический интерфейс
pandas >= 1.3.0    # Экспорт в Excel
openpyxl >= 3.0.0  # Работа с Excel
sqlite3            # Встроенная БД (входит в Python)
```

## 📁 Структура проекта

```
stafftracker/
├── main.py              # Основной файл приложения
├── populate_db.py       # Скрипт заполнения тестовыми данными
├── requirements.txt     # Зависимости
├── build.bat           # Скрипт сборки EXE (Windows)
├── attendance.db       # База данных SQLite (создаётся автоматически)
├── reports/            # Папка для отчётов
└── data/               # Папка для данных
```

## 🗄️ Структура базы данных

```sql
employees          attendance         absences
┌────────────┐    ┌────────────┐     ┌────────────┐
│ id         │    │ id         │     │ id         │
│ full_name  │    │ employee_id│◄─── │ employee_id│
│ department │    │ check_time │     │ type_id    │
│ position   │    │ direction  │     │ start_date │
│ hire_date  │    │ is_late    │     │ end_date   │
│ fire_date  │    └────────────┘     └────────────┘
│ work_start │           ▲
│ work_end   │           │
└────────────┘           │
       │                  │
       ▼                  │
departments               │
┌────────────┐           │
│ id         │           │
│ name       │           │
└────────────┘           │
                          │
absence_types            │
┌────────────┐           │
│ id         │           │
│ name       │◄──────────┘
└────────────┘
```

## 💡 Использование

### 1️⃣ Добавление сотрудника

Перейдите на вкладку "Сотрудники" → нажмите "Добавить" → заполните форму.

### 2️⃣ Отметка посещаемости

Перейдите на вкладку "Посещаемость" → выберите сотрудника → нажмите "Пришёл" или "Ушёл".

### 3️⃣ Формирование отчёта

Перейдите на вкладку "Отчёты" → выберите период → нажмите "Сформировать отчёт".

### 4️⃣ Экспорт в Excel

После формирования отчёта нажмите "Экспорт в Excel".

## 📊 Пример отчёта

| Сотрудник | Должность | Дата | Приход | Уход | Опозданий |
|-----------|-----------|------|--------|------|-----------|
| Иванов И.И. | Разработчик | 2026-05-01 | 09:05 | 18:10 | 1 |
| Петрова А.А. | Тестировщик | 2026-05-01 | 09:20 | 18:00 | 1 |
| Сидоров С.С. | Менеджер | 2026-05-01 | 09:00 | 18:15 | 0 |

## 🧪 Тестирование

Заполнение тестовыми данными:

```bash
python populate_db.py
```

Скрипт создаст:
- 25 сотрудников с реалистичными данными
- Записи посещаемости за последние 90 дней
- Различные типы отсутствий

## 📈 Планы развития

- [ ] Добавление авторизации с ролями
- [ ] Веб-интерфейс
- [ ] Уведомления о опозданиях
- [ ] Интеграция с 1С
- [ ] Мобильное приложение
- [ ] Облачное хранение данных

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте изменения в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## 📝 Лицензия

Проект распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](LICENSE).

## 👤 Автор

**Акатьев Геннадий**
- Студент ЧУПО «Высшая школа предпринимательства»
- Специальность: Информационные системы и программирование (09.02.07)
- Год: 2026

## 📞 Контакты

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Благодарности

- Руководителю дипломного проекта за ценные советы
- Всем, кто помогал в тестировании
- Open Source сообществу за отличные библиотеки

---

<p align="center">
  <i>⭐ Если этот проект помог вам, поставьте звезду на GitHub! ⭐</i>
</p>

---

## 🛠️ Файл requirements.txt

```
PyQt5>=5.15.0
pandas>=1.3.0
openpyxl>=3.0.0
```

## 📝 Лицензия (LICENSE)

```
MIT License

Copyright (c) 2026 Акатьев Геннадий

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📋 .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
dist/
build/
*.egg-info/
*.egg

# Database
*.db
*.db-journal
backup_*.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
reports/*.xlsx
data/
*.log
```

## 🐍 .python-version

```
3.9.6
```

---

<p align="center">
  <b>StaffTracker v1.0</b><br>
  © 2026 Акатьев Геннадий
</p>
