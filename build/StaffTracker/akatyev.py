# main.py
import sys
import os
import sqlite3
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QComboBox, QLabel, QDateEdit,
                             QMessageBox, QHeaderView, QGroupBox, QFormLayout,
                             QTextEdit, QFileDialog, QDialog, QDialogButtonBox,
                             QSpinBox, QCheckBox, QListWidget, QListWidgetItem,
                             QSplitter, QFrame)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QColor, QFont
import pandas as pd
from datetime import datetime as dt

# --- Конфигурация ---
DB_NAME = "attendance.db"
REPORTS_DIR = "reports"


class Database:
    """Класс для работы с базой данных SQLite"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.conn = None
            self.cursor = None
            self._connect()
            self._create_tables()

    def _connect(self):
        """Подключение к БД"""
        try:
            self.conn = sqlite3.connect(DB_NAME)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка БД", f"Не удалось подключиться к БД: {e}")

    def _create_tables(self):
        """Создание таблиц, индексов и триггеров"""
        self.cursor.executescript("""
            -- Таблица отделов
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                head_employee_id INTEGER NULL
            );

            -- Таблица сотрудников
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name VARCHAR(150) NOT NULL,
                department_id INTEGER NOT NULL,
                position VARCHAR(100) NOT NULL,
                hire_date DATE NOT NULL,
                fire_date DATE NULL,
                work_start_time TIME NOT NULL DEFAULT '09:00:00',
                work_end_time TIME NOT NULL DEFAULT '18:00:00',
                FOREIGN KEY (department_id) REFERENCES departments(id)
            );

            -- Таблица посещаемости
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                check_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                direction VARCHAR(3) NOT NULL CHECK (direction IN ('IN', 'OUT')),
                is_late BOOLEAN DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            -- Таблица отсутствий
            CREATE TABLE IF NOT EXISTS absences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                absence_type_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                note TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id),
                FOREIGN KEY (absence_type_id) REFERENCES absence_types(id)
            );

            -- Таблица типов отсутствий
            CREATE TABLE IF NOT EXISTS absence_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE
            );

            -- Индексы
            CREATE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance(employee_id, DATE(check_time));
            CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(check_time);

            -- Триггер для запрета двойного IN
            CREATE TRIGGER IF NOT EXISTS prevent_double_in
            BEFORE INSERT ON attendance
            BEGIN
                SELECT CASE
                    WHEN NEW.direction = 'IN' AND EXISTS (
                        SELECT 1 FROM attendance 
                        WHERE employee_id = NEW.employee_id 
                        AND DATE(check_time) = DATE(NEW.check_time)
                        AND direction = 'IN'
                    ) THEN RAISE(ABORT, 'Сотрудник уже отметил приход сегодня')
                END;
            END;

            -- Триггер для автоматического определения опоздания
            CREATE TRIGGER IF NOT EXISTS set_late_flag
            BEFORE INSERT ON attendance
            BEGIN
                UPDATE attendance SET is_late = CASE
                    WHEN NEW.direction = 'IN' AND TIME(NEW.check_time) > (
                        SELECT work_start_time FROM employees WHERE id = NEW.employee_id
                    ) THEN 1
                    ELSE 0
                END WHERE id = NEW.id;
            END;
        """)

        # Заполнение начальными данными
        self._init_data()
        self.conn.commit()

    def _init_data(self):
        """Инициализация начальных данных"""
        # Добавление типов отсутствий
        absence_types = ['Отпуск', 'Больничный', 'Прогул', 'Командировка', 'Учебный отпуск']
        for at in absence_types:
            self.cursor.execute("INSERT OR IGNORE INTO absence_types (name) VALUES (?)", (at,))

        # Добавление тестового отдела
        self.cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", ("IT-отдел",))

    def execute(self, query, params=None):
        """Выполнение запроса"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            QMessageBox.critical(None, "Ошибка БД", f"Ошибка выполнения запроса: {e}")
            return None

    def fetch_all(self, query, params=None):
        """Выполнение запроса с возвратом всех строк"""
        cursor = self.execute(query, params)
        if cursor:
            return cursor.fetchall()
        return []

    def fetch_one(self, query, params=None):
        """Выполнение запроса с возвратом одной строки"""
        cursor = self.execute(query, params)
        if cursor:
            return cursor.fetchone()
        return None

    def get_last_id(self):
        """Получение последнего ID"""
        return self.cursor.lastrowid

    def backup(self):
        """Создание резервной копии БД"""
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            with sqlite3.connect(backup_name) as backup_conn:
                self.conn.backup(backup_conn)
            return backup_name
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось создать бэкап: {e}")
            return None

    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()


# --- Модели данных ---
class Employee:
    """Модель сотрудника"""

    def __init__(self, id=None, full_name="", department_id=0, position="",
                 hire_date=None, fire_date=None, work_start="09:00", work_end="18:00"):
        self.id = id
        self.full_name = full_name
        self.department_id = department_id
        self.position = position
        self.hire_date = hire_date or date.today()
        self.fire_date = fire_date
        self.work_start = work_start
        self.work_end = work_end


class AttendanceService:
    """Сервис для работы с посещаемостью"""

    def __init__(self, db: Database):
        self.db = db

    def mark_arrival(self, employee_id: int) -> bool:
        """Отметка прихода"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.execute(
                "INSERT INTO attendance (employee_id, check_time, direction) VALUES (?, ?, ?)",
                (employee_id, current_time, 'IN')
            )
            return True
        except sqlite3.Error as e:
            QMessageBox.warning(None, "Ошибка", str(e))
            return False

    def mark_departure(self, employee_id: int) -> bool:
        """Отметка ухода"""
        # Проверяем, был ли приход сегодня
        today = date.today().isoformat()
        check_in = self.db.fetch_one(
            """SELECT id FROM attendance 
               WHERE employee_id = ? AND DATE(check_time) = ? AND direction = 'IN' 
               ORDER BY check_time DESC LIMIT 1""",
            (employee_id, today)
        )
        if not check_in:
            QMessageBox.warning(None, "Ошибка", "Сначала нужно отметить приход")
            return False

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db.execute(
            "INSERT INTO attendance (employee_id, check_time, direction) VALUES (?, ?, ?)",
            (employee_id, current_time, 'OUT')
        )
        return True

    def get_today_attendance(self, employee_id: int) -> dict:
        """Получение сегодняшней посещаемости сотрудника"""
        today = date.today().isoformat()
        rows = self.db.fetch_all(
            """SELECT direction, check_time FROM attendance 
               WHERE employee_id = ? AND DATE(check_time) = ? 
               ORDER BY check_time""",
            (employee_id, today)
        )
        result = {'IN': None, 'OUT': None}
        for row in rows:
            result[row['direction']] = row['check_time']
        return result

    def get_daily_report(self, date_str: str) -> list:
        """Отчёт за день"""
        return self.db.fetch_all("""
            SELECT e.full_name, e.position, 
                   MIN(CASE WHEN a.direction='IN' THEN a.check_time END) as time_in,
                   MAX(CASE WHEN a.direction='OUT' THEN a.check_time END) as time_out,
                   SUM(CASE WHEN a.is_late THEN 1 ELSE 0 END) as late_count
            FROM employees e
            LEFT JOIN attendance a ON e.id = a.employee_id AND DATE(a.check_time) = ?
            WHERE e.fire_date IS NULL
            GROUP BY e.id
        """, (date_str,))

    def get_monthly_report(self, year: int, month: int) -> list:
        """Отчёт за месяц"""
        return self.db.fetch_all("""
            SELECT e.id, e.full_name, e.position,
                   DATE(a.check_time) as work_date,
                   MIN(CASE WHEN a.direction='IN' THEN a.check_time END) as time_in,
                   MAX(CASE WHEN a.direction='OUT' THEN a.check_time END) as time_out,
                   SUM(CASE WHEN a.is_late THEN 1 ELSE 0 END) as late_count
            FROM employees e
            LEFT JOIN attendance a ON e.id = a.employee_id 
                AND strftime('%Y', a.check_time) = ? 
                AND strftime('%m', a.check_time) = ?
            WHERE e.fire_date IS NULL
            GROUP BY e.id, DATE(a.check_time)
            ORDER BY e.full_name, work_date
        """, (str(year), str(month).zfill(2)))

    def get_late_list(self, start_date: str, end_date: str) -> list:
        """Список опозданий за период"""
        return self.db.fetch_all("""
            SELECT e.full_name, e.position, a.check_time, 
                   e.work_start_time,
                   strftime('%s', a.check_time) - strftime('%s', e.work_start_time) as late_minutes
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.is_late = 1 
                AND DATE(a.check_time) BETWEEN ? AND ?
            ORDER BY a.check_time DESC
        """, (start_date, end_date))


# --- Диалог добавления сотрудника ---
class AddEmployeeDialog(QDialog):
    def __init__(self, db: Database, employee_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.employee_id = employee_id
        self.setWindowTitle("Добавить сотрудника" if not employee_id else "Редактировать сотрудника")
        self.setMinimumWidth(400)
        self.init_ui()
        if employee_id:
            self.load_employee()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО:", self.full_name_edit)

        self.department_combo = QComboBox()
        self.load_departments()
        form.addRow("Отдел:", self.department_combo)

        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Разработчик")
        form.addRow("Должность:", self.position_edit)

        self.hire_date = QDateEdit()
        self.hire_date.setDate(QDate.currentDate())
        self.hire_date.setCalendarPopup(True)
        form.addRow("Дата приёма:", self.hire_date)

        self.work_start = QLineEdit("09:00")
        form.addRow("Начало работы:", self.work_start)

        self.work_end = QLineEdit("18:00")
        form.addRow("Конец работы:", self.work_end)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_departments(self):
        self.department_combo.clear()
        deps = self.db.fetch_all("SELECT id, name FROM departments ORDER BY name")
        for dep in deps:
            self.department_combo.addItem(dep['name'], dep['id'])
        if self.department_combo.count() == 0:
            self.department_combo.addItem("IT-отдел", 1)

    def load_employee(self):
        emp = self.db.fetch_one("SELECT * FROM employees WHERE id = ?", (self.employee_id,))
        if emp:
            self.full_name_edit.setText(emp['full_name'])
            idx = self.department_combo.findData(emp['department_id'])
            if idx >= 0:
                self.department_combo.setCurrentIndex(idx)
            self.position_edit.setText(emp['position'])
            self.hire_date.setDate(QDate.fromString(emp['hire_date'], "yyyy-MM-dd"))
            self.work_start.setText(emp['work_start_time'])
            self.work_end.setText(emp['work_end_time'])

    def get_employee_data(self):
        return {
            'full_name': self.full_name_edit.text().strip(),
            'department_id': self.department_combo.currentData(),
            'position': self.position_edit.text().strip(),
            'hire_date': self.hire_date.date().toString("yyyy-MM-dd"),
            'work_start': self.work_start.text().strip(),
            'work_end': self.work_end.text().strip()
        }


# --- Главное окно приложения ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.attendance_service = AttendanceService(self.db)
        self.current_employee_id = None
        self.setWindowTitle("StaffTracker - Учёт посещаемости сотрудников")
        self.setMinimumSize(1000, 700)

        self.init_ui()
        self.load_employees()
        self.update_status()

    def init_ui(self):
        """Инициализация интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель со статусом
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(self.status_frame)
        self.status_label = QLabel("Готов к работе")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(QLabel("База данных: SQLite"))
        main_layout.addWidget(self.status_frame)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_employees_tab(), "Сотрудники")
        self.tabs.addTab(self.create_attendance_tab(), "Посещаемость")
        self.tabs.addTab(self.create_reports_tab(), "Отчёты")
        self.tabs.addTab(self.create_absences_tab(), "Отсутствия")
        main_layout.addWidget(self.tabs)

        # Нижняя панель
        bottom_layout = QHBoxLayout()
        backup_btn = QPushButton("📁 Создать бэкап")
        backup_btn.clicked.connect(self.backup_database)
        bottom_layout.addWidget(backup_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(
            QLabel(f"Записей: {len(self.db.fetch_all('SELECT COUNT(*) as count FROM employees'))} сотрудников"))
        main_layout.addLayout(bottom_layout)

    def create_employees_tab(self):
        """Вкладка управления сотрудниками"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Панель управления
        control_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск сотрудников...")
        self.search_edit.textChanged.connect(self.filter_employees)
        control_layout.addWidget(self.search_edit)

        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_employee)
        control_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Редактировать")
        edit_btn.clicked.connect(self.edit_employee)
        control_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Уволить")
        delete_btn.clicked.connect(self.fire_employee)
        control_layout.addWidget(delete_btn)

        layout.addLayout(control_layout)

        # Таблица сотрудников
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(7)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "ФИО", "Отдел", "Должность", "Дата приёма", "Начало", "Конец"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employees_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.employees_table.itemClicked.connect(self.on_employee_selected)
        layout.addWidget(self.employees_table)

        return tab

    def create_attendance_tab(self):
        """Вкладка учета посещаемости"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Левая панель - список сотрудников
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Выберите сотрудника:"))

        self.attendance_list = QListWidget()
        self.attendance_list.setMaximumWidth(300)
        self.attendance_list.itemClicked.connect(self.on_attendance_employee_selected)
        left_layout.addWidget(self.attendance_list)

        # Правая панель - информация и кнопки
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.emp_info_label = QLabel("Выберите сотрудника для отметки")
        self.emp_info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(self.emp_info_label)

        # Информация о сегодняшней посещаемости
        self.today_info_label = QLabel("Сегодня: нет отметок")
        right_layout.addWidget(self.today_info_label)

        # Кнопки
        btn_layout = QHBoxLayout()
        arrive_btn = QPushButton("✅ Пришёл")
        arrive_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        arrive_btn.clicked.connect(self.mark_arrival)
        btn_layout.addWidget(arrive_btn)

        depart_btn = QPushButton("❌ Ушёл")
        depart_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 16px; padding: 10px;")
        depart_btn.clicked.connect(self.mark_departure)
        btn_layout.addWidget(depart_btn)
        right_layout.addLayout(btn_layout)

        # История отметок
        right_layout.addWidget(QLabel("История отметок сегодня:"))
        self.attendance_history = QTableWidget()
        self.attendance_history.setColumnCount(3)
        self.attendance_history.setHorizontalHeaderLabels(["Время", "Тип", "Опоздание"])
        self.attendance_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.attendance_history)

        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        return tab

    def create_reports_tab(self):
        """Вкладка отчётов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Панель управления
        control_layout = QHBoxLayout()

        control_layout.addWidget(QLabel("Период:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        control_layout.addWidget(self.start_date)

        control_layout.addWidget(QLabel(" - "))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        control_layout.addWidget(self.end_date)

        self.report_type = QComboBox()
        self.report_type.addItems(["Дневной отчёт", "Месячный отчёт", "Опоздания"])
        control_layout.addWidget(self.report_type)

        generate_btn = QPushButton("📊 Сформировать отчёт")
        generate_btn.clicked.connect(self.generate_report)
        control_layout.addWidget(generate_btn)

        export_btn = QPushButton("📤 Экспорт в Excel")
        export_btn.clicked.connect(self.export_report)
        control_layout.addWidget(export_btn)

        layout.addLayout(control_layout)

        # Таблица отчёта
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Сотрудник", "Должность", "Дата", "Приход", "Уход", "Опозданий"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.report_table)

        # Статистика
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)

        return tab

    def create_absences_tab(self):
        """Вкладка отсутствий"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Панель управления
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Сотрудник:"))
        self.absence_employee_combo = QComboBox()
        self.load_employees_combo(self.absence_employee_combo)
        control_layout.addWidget(self.absence_employee_combo)

        control_layout.addWidget(QLabel("Тип:"))
        self.absence_type_combo = QComboBox()
        self.load_absence_types()
        control_layout.addWidget(self.absence_type_combo)

        control_layout.addWidget(QLabel("Начало:"))
        self.absence_start = QDateEdit()
        self.absence_start.setDate(QDate.currentDate())
        self.absence_start.setCalendarPopup(True)
        control_layout.addWidget(self.absence_start)

        control_layout.addWidget(QLabel("Конец:"))
        self.absence_end = QDateEdit()
        self.absence_end.setDate(QDate.currentDate().addDays(7))
        self.absence_end.setCalendarPopup(True)
        control_layout.addWidget(self.absence_end)

        add_absence_btn = QPushButton("➕ Добавить")
        add_absence_btn.clicked.connect(self.add_absence)
        control_layout.addWidget(add_absence_btn)

        layout.addLayout(control_layout)

        # Таблица отсутствий
        self.absence_table = QTableWidget()
        self.absence_table.setColumnCount(5)
        self.absence_table.setHorizontalHeaderLabels([
            "Сотрудник", "Тип", "Начало", "Конец", "Примечание"
        ])
        self.absence_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.absence_table)

        self.load_absences()

        return tab

    # --- Методы работы с сотрудниками ---

    def load_employees(self):
        """Загрузка списка сотрудников"""
        employees = self.db.fetch_all("""
            SELECT e.*, d.name as department_name 
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            WHERE e.fire_date IS NULL
            ORDER BY e.full_name
        """)

        self.employees_table.setRowCount(len(employees))
        self.attendance_list.clear()

        for i, emp in enumerate(employees):
            self.employees_table.setItem(i, 0, QTableWidgetItem(str(emp['id'])))
            self.employees_table.setItem(i, 1, QTableWidgetItem(emp['full_name']))
            self.employees_table.setItem(i, 2, QTableWidgetItem(emp['department_name']))
            self.employees_table.setItem(i, 3, QTableWidgetItem(emp['position']))
            self.employees_table.setItem(i, 4, QTableWidgetItem(emp['hire_date']))
            self.employees_table.setItem(i, 5, QTableWidgetItem(emp['work_start_time']))
            self.employees_table.setItem(i, 6, QTableWidgetItem(emp['work_end_time']))

            # Для списка в вкладке посещаемости
            item = QListWidgetItem(f"{emp['full_name']} ({emp['position']})")
            item.setData(Qt.ItemDataRole.UserRole, emp['id'])
            self.attendance_list.addItem(item)

        # Обновляем комбобоксы
        self.load_employees_combo(self.absence_employee_combo)

    def load_employees_combo(self, combo):
        """Загрузка списка сотрудников в комбобокс"""
        combo.clear()
        employees = self.db.fetch_all("""
            SELECT id, full_name FROM employees WHERE fire_date IS NULL ORDER BY full_name
        """)
        for emp in employees:
            combo.addItem(emp['full_name'], emp['id'])

    def load_absence_types(self):
        """Загрузка типов отсутствий"""
        self.absence_type_combo.clear()
        types = self.db.fetch_all("SELECT id, name FROM absence_types ORDER BY name")
        for at in types:
            self.absence_type_combo.addItem(at['name'], at['id'])

    def filter_employees(self):
        """Фильтрация списка сотрудников"""
        search_text = self.search_edit.text().lower()
        for i in range(self.employees_table.rowCount()):
            item = self.employees_table.item(i, 1)
            if item:
                visible = search_text in item.text().lower()
                self.employees_table.setRowHidden(i, not visible)

    def on_employee_selected(self, item):
        """Выбор сотрудника в таблице"""
        row = item.row()
        self.current_employee_id = int(self.employees_table.item(row, 0).text())

    def on_attendance_employee_selected(self, item):
        """Выбор сотрудника в списке посещаемости"""
        emp_id = item.data(Qt.ItemDataRole.UserRole)
        if emp_id:
            self.current_employee_id = emp_id
            self.update_attendance_info(emp_id)

    def add_employee(self):
        """Добавление сотрудника"""
        dialog = AddEmployeeDialog(self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_employee_data()
            if not data['full_name']:
                QMessageBox.warning(self, "Ошибка", "Введите ФИО")
                return

            self.db.execute("""
                INSERT INTO employees (full_name, department_id, position, hire_date, work_start_time, work_end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data['full_name'], data['department_id'], data['position'],
                  data['hire_date'], data['work_start'], data['work_end']))

            self.load_employees()
            self.update_status()
            QMessageBox.information(self, "Успех", "Сотрудник добавлен")

    def edit_employee(self):
        """Редактирование сотрудника"""
        if not self.current_employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        dialog = AddEmployeeDialog(self.db, self.current_employee_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_employee_data()
            if not data['full_name']:
                QMessageBox.warning(self, "Ошибка", "Введите ФИО")
                return

            self.db.execute("""
                UPDATE employees 
                SET full_name=?, department_id=?, position=?, 
                    hire_date=?, work_start_time=?, work_end_time=?
                WHERE id=?
            """, (data['full_name'], data['department_id'], data['position'],
                  data['hire_date'], data['work_start'], data['work_end'], self.current_employee_id))

            self.load_employees()
            self.update_status()
            QMessageBox.information(self, "Успех", "Данные обновлены")

    def fire_employee(self):
        """Увольнение сотрудника"""
        if not self.current_employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите уволить этого сотрудника?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute(
                "UPDATE employees SET fire_date = ? WHERE id = ?",
                (date.today().isoformat(), self.current_employee_id)
            )
            self.load_employees()
            self.update_status()
            QMessageBox.information(self, "Успех", "Сотрудник уволен")

    # --- Методы работы с посещаемостью ---

    def update_attendance_info(self, employee_id):
        """Обновление информации о посещаемости сотрудника"""
        emp = self.db.fetch_one("SELECT full_name, position FROM employees WHERE id = ?", (employee_id,))
        if emp:
            self.emp_info_label.setText(f"{emp['full_name']} - {emp['position']}")

        attendance = self.attendance_service.get_today_attendance(employee_id)
        info_text = f"Сегодня: "
        if attendance['IN']:
            info_text += f"Пришёл в {attendance['IN'][11:16]} "
        else:
            info_text += "не отмечен приход "
        if attendance['OUT']:
            info_text += f"| Ушёл в {attendance['OUT'][11:16]}"
        else:
            info_text += "| уход не отмечен"
        self.today_info_label.setText(info_text)

        # История отметок
        rows = self.db.fetch_all("""
            SELECT check_time, direction, is_late FROM attendance 
            WHERE employee_id = ? AND DATE(check_time) = DATE('now')
            ORDER BY check_time DESC
        """, (employee_id,))

        self.attendance_history.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.attendance_history.setItem(i, 0, QTableWidgetItem(row['check_time'][11:16]))
            direction_text = "✅ Пришёл" if row['direction'] == 'IN' else "❌ Ушёл"
            self.attendance_history.setItem(i, 1, QTableWidgetItem(direction_text))
            late_text = "⚠️ Опоздание" if row['is_late'] else "Нет"
            self.attendance_history.setItem(i, 2, QTableWidgetItem(late_text))

    def update_status(self):
        """Обновление статуса"""
        count = self.db.fetch_one("SELECT COUNT(*) as count FROM employees WHERE fire_date IS NULL")
        if count:
            self.status_label.setText(f"Активных сотрудников: {count['count']}")

    def mark_arrival(self):
        """Отметка прихода"""
        if not self.current_employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        if self.attendance_service.mark_arrival(self.current_employee_id):
            self.update_attendance_info(self.current_employee_id)
            QMessageBox.information(self, "Успех", "Приход отмечен")

    def mark_departure(self):
        """Отметка ухода"""
        if not self.current_employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        if self.attendance_service.mark_departure(self.current_employee_id):
            self.update_attendance_info(self.current_employee_id)
            QMessageBox.information(self, "Успех", "Уход отмечен")

    # --- Методы работы с отчётами ---

    def generate_report(self):
        """Генерация отчёта"""
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        report_type = self.report_type.currentText()

        if report_type == "Дневной отчёт":
            data = self.attendance_service.get_daily_report(end)
            self.report_table.setColumnCount(5)
            self.report_table.setHorizontalHeaderLabels([
                "Сотрудник", "Должность", "Приход", "Уход", "Опозданий"
            ])
        elif report_type == "Месячный отчёт":
            year = int(end.split('-')[0])
            month = int(end.split('-')[1])
            data = self.attendance_service.get_monthly_report(year, month)
            self.report_table.setColumnCount(6)
            self.report_table.setHorizontalHeaderLabels([
                "Сотрудник", "Должность", "Дата", "Приход", "Уход", "Опозданий"
            ])
        else:  # Опоздания
            data = self.attendance_service.get_late_list(start, end)
            self.report_table.setColumnCount(5)
            self.report_table.setHorizontalHeaderLabels([
                "Сотрудник", "Должность", "Время прихода", "Начало смены", "Опоздание (мин)"
            ])

        self.report_table.setRowCount(len(data))
        for i, row in enumerate(data):
            for j in range(len(row)):
                val = str(row[j]) if row[j] is not None else ""
                self.report_table.setItem(i, j, QTableWidgetItem(val))

        self.report_table.resizeColumnsToContents()
        self.stats_label.setText(f"Всего записей: {len(data)}")

    def export_report(self):
        """Экспорт отчёта в Excel"""
        if self.report_table.rowCount() == 0:
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте отчёт")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт",
            f"{REPORTS_DIR}/report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        # Создаем директорию если её нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Извлекаем данные из таблицы
            headers = []
            for j in range(self.report_table.columnCount()):
                headers.append(self.report_table.horizontalHeaderItem(j).text())

            data = []
            for i in range(self.report_table.rowCount()):
                row = []
                for j in range(self.report_table.columnCount()):
                    item = self.report_table.item(i, j)
                    row.append(item.text() if item else "")
                data.append(row)

            df = pd.DataFrame(data, columns=headers)
            df.to_excel(file_path, index=False, engine='openpyxl')

            QMessageBox.information(self, "Успех", f"Отчёт сохранён в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт: {e}")

    # --- Методы работы с отсутствиями ---

    def load_absences(self):
        """Загрузка списка отсутствий"""
        absences = self.db.fetch_all("""
            SELECT a.id, e.full_name, at.name as type_name, a.start_date, a.end_date, a.note
            FROM absences a
            JOIN employees e ON a.employee_id = e.id
            JOIN absence_types at ON a.absence_type_id = at.id
            WHERE e.fire_date IS NULL
            ORDER BY a.start_date DESC
        """)

        self.absence_table.setRowCount(len(absences))
        for i, row in enumerate(absences):
            self.absence_table.setItem(i, 0, QTableWidgetItem(row['full_name']))
            self.absence_table.setItem(i, 1, QTableWidgetItem(row['type_name']))
            self.absence_table.setItem(i, 2, QTableWidgetItem(row['start_date']))
            self.absence_table.setItem(i, 3, QTableWidgetItem(row['end_date']))
            self.absence_table.setItem(i, 4, QTableWidgetItem(row['note'] or ""))

    def add_absence(self):
        """Добавление отсутствия"""
        employee_id = self.absence_employee_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        absence_type_id = self.absence_type_combo.currentData()
        start = self.absence_start.date().toString("yyyy-MM-dd")
        end = self.absence_end.date().toString("yyyy-MM-dd")

        if start > end:
            QMessageBox.warning(self, "Ошибка", "Дата начала не может быть позже даты окончания")
            return

        self.db.execute("""
            INSERT INTO absences (employee_id, absence_type_id, start_date, end_date)
            VALUES (?, ?, ?, ?)
        """, (employee_id, absence_type_id, start, end))

        self.load_absences()
        QMessageBox.information(self, "Успех", "Отсутствие добавлено")

    # --- Служебные методы ---

    def backup_database(self):
        """Создание резервной копии"""
        backup_file = self.db.backup()
        if backup_file:
            QMessageBox.information(self, "Успех", f"Бэкап создан: {backup_file}")


# --- Запуск приложения ---
def main():
    app = QApplication(sys.argv)

    # Создаем папку для отчётов
    os.makedirs(REPORTS_DIR, exist_ok=True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()