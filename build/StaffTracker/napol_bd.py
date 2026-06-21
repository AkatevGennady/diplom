# populate_db.py
import sqlite3
import random
from datetime import datetime, timedelta, date
import os

DB_NAME = "attendance.db"

# Данные для генерации
FIRST_NAMES = ['Александр', 'Дмитрий', 'Максим', 'Сергей', 'Андрей', 'Алексей', 'Иван', 'Михаил', 'Евгений', 'Владимир',
               'Анна', 'Елена', 'Ольга', 'Татьяна', 'Мария', 'Наталья', 'Ирина', 'Светлана', 'Екатерина', 'Юлия',
               'Николай', 'Павел', 'Роман', 'Виктор', 'Артём', 'Константин', 'Василий', 'Георгий', 'Степан', 'Фёдор',
               'Анастасия', 'Евгения', 'Галина', 'Людмила', 'Надежда', 'Алла', 'Жанна', 'Зоя', 'Инна', 'Вера']

LAST_NAMES = ['Иванов', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Петров', 'Соколов', 'Михайлов', 'Новиков',
              'Фёдоров',
              'Морозов', 'Волков', 'Алексеев', 'Лебедев', 'Семёнов', 'Егоров', 'Павлов', 'Козлов', 'Степанов',
              'Николаев',
              'Орлов', 'Андреев', 'Макаров', 'Никитин', 'Захаров', 'Зайцев', 'Соловьёв', 'Борисов', 'Яковлев',
              'Григорьев',
              'Кузьмин', 'Поляков', 'Сидоров', 'Калинин', 'Виноградов', 'Голубев', 'Денисов', 'Емельянов', 'Ковалёв',
              'Савельев']

PATRONYMICS = ['Александрович', 'Дмитриевич', 'Максимович', 'Сергеевич', 'Андреевич', 'Алексеевич', 'Иванович',
               'Михайлович',
               'Евгеньевич', 'Владимирович', 'Павлович', 'Николаевич', 'Викторович', 'Романович', 'Петрович',
               'Фёдорович',
               'Борисович', 'Григорьевич', 'Васильевич', 'Георгиевич',
               'Александровна', 'Дмитриевна', 'Максимовна', 'Сергеевна', 'Андреевна', 'Алексеевна', 'Ивановна',
               'Михайловна',
               'Евгеньевна', 'Владимировна', 'Павловна', 'Николаевна', 'Викторовна', 'Романовна', 'Петровна',
               'Фёдоровна']

POSITIONS = ['Разработчик', 'Тестировщик', 'Системный администратор', 'Менеджер проекта', 'Аналитик',
             'DevOps инженер', 'HR-менеджер', 'Бухгалтер', 'Юрист', 'Маркетолог',
             'Руководитель отдела', 'Главный разработчик', 'Инженер', 'Технический писатель',
             'Специалист по данным', 'Дизайнер', 'Продукт-менеджер', 'Бизнес-аналитик',
             'Специалист по безопасности', 'QA инженер']

DEPARTMENTS = ['IT-отдел', 'Бухгалтерия', 'Отдел кадров', 'Юридический отдел', 'Маркетинг',
               'Отдел продаж', 'Администрация', 'Технический отдел', 'Аналитический отдел']

ABSENCE_TYPES = ['Отпуск', 'Больничный', 'Прогул', 'Командировка', 'Учебный отпуск']


def get_random_name():
    """Генерация случайного ФИО"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    patronymic = random.choice(PATRONYMICS)
    return f"{last} {first} {patronymic}"


def generate_work_schedule():
    """Генерация случайного графика работы"""
    start_hours = [8, 9, 10]
    start_minutes = [0, 15, 30, 45]
    end_hours = [17, 18, 19, 20]
    end_minutes = [0, 15, 30, 45]

    start = f"{random.choice(start_hours):02d}:{random.choice(start_minutes):02d}:00"
    end = f"{random.choice(end_hours):02d}:{random.choice(end_minutes):02d}:00"
    return start, end


def generate_attendance_records(db, employee_id, start_date, end_date):
    """Генерация записей посещаемости для сотрудника за период"""
    cursor = db.cursor()

    # Получаем график работы сотрудника
    cursor.execute("SELECT work_start_time, work_end_time FROM employees WHERE id = ?", (employee_id,))
    work = cursor.fetchone()
    if not work:
        return

    work_start = datetime.strptime(work[0], '%H:%M:%S').time()
    work_end = datetime.strptime(work[1], '%H:%M:%S').time()

    current_date = start_date
    records = []

    while current_date <= end_date:
        # Пропускаем выходные (суббота и воскресенье)
        if current_date.weekday() < 5:  # 0-4 = понедельник-пятница
            # 80% вероятность что сотрудник работал в этот день
            if random.random() < 0.8:
                # Генерация времени прихода (с опозданием в 15% случаев)
                arrive_minutes = 0
                if random.random() < 0.15:  # опоздание
                    arrive_minutes = random.randint(5, 60)

                arrive_time = datetime.combine(current_date, work_start) + timedelta(minutes=arrive_minutes)

                # Генерация времени ухода (раньше или позже)
                leave_minutes = random.randint(-30, 60)
                leave_time = datetime.combine(current_date, work_end) + timedelta(minutes=leave_minutes)

                # Уход не может быть раньше прихода
                if leave_time <= arrive_time:
                    leave_time = arrive_time + timedelta(hours=4, minutes=random.randint(0, 60))

                records.append((employee_id, arrive_time, 'IN'))
                records.append((employee_id, leave_time, 'OUT'))

        current_date += timedelta(days=1)

    return records


def main():
    """Основная функция заполнения БД"""

    # Проверяем существование БД
    if not os.path.exists(DB_NAME):
        print(f"Ошибка: База данных {DB_NAME} не найдена!")
        print("Сначала запустите основное приложение для создания БД.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("Начало заполнения базы данных тестовыми данными...")

    # Очищаем существующие данные (кроме справочников)
    try:
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM absences")
        cursor.execute("DELETE FROM employees")
        print("Существующие данные очищены.")
    except sqlite3.Error:
        print("Очистка данных не требуется или таблицы пусты.")

    # 1. Добавляем отделы
    print("Добавление отделов...")
    department_ids = {}
    for dept in DEPARTMENTS:
        cursor.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (dept,))
        dept_id = cursor.execute("SELECT id FROM departments WHERE name = ?", (dept,)).fetchone()[0]
        department_ids[dept] = dept_id

    # 2. Добавляем сотрудников (25 человек)
    print("Добавление сотрудников...")
    employee_ids = []
    num_employees = 25

    for i in range(num_employees):
        full_name = get_random_name()
        department = random.choice(list(department_ids.keys()))
        department_id = department_ids[department]
        position = random.choice(POSITIONS)

        # Дата приёма (от 2018 до 2026 года)
        hire_year = random.randint(2018, 2026)
        hire_month = random.randint(1, 12)
        hire_day = random.randint(1, 28)
        hire_date = f"{hire_year}-{hire_month:02d}-{hire_day:02d}"

        # График работы
        work_start, work_end = generate_work_schedule()

        # Увольнение (10% сотрудников уволены)
        fire_date = None
        if random.random() < 0.1:
            fire_year = random.randint(hire_year, 2025)
            fire_month = random.randint(1, 12)
            fire_day = random.randint(1, 28)
            fire_date = f"{fire_year}-{fire_month:02d}-{fire_day:02d}"

        cursor.execute("""
            INSERT INTO employees (full_name, department_id, position, hire_date, fire_date, work_start_time, work_end_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (full_name, department_id, position, hire_date, fire_date, work_start, work_end))

        employee_id = cursor.lastrowid
        employee_ids.append(employee_id)

    print(f"Добавлено {len(employee_ids)} сотрудников.")

    # 3. Добавляем записи посещаемости за последние 90 дней
    print("Добавление записей посещаемости...")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=90)

    total_records = 0
    for emp_id in employee_ids:
        records = generate_attendance_records(conn, emp_id, start_date, end_date)
        if records:
            for record in records:
                try:
                    cursor.execute("""
                        INSERT INTO attendance (employee_id, check_time, direction)
                        VALUES (?, ?, ?)
                    """, (record[0], record[1], record[2]))
                    total_records += 1
                except sqlite3.Error:
                    # Пропускаем дублирующиеся записи
                    pass

    print(f"Добавлено {total_records} записей посещаемости.")

    # 4. Добавляем отсутствия (каждый 3-й сотрудник)
    print("Добавление записей отсутствий...")

    # Получаем ID типов отсутствий
    absence_type_ids = {}
    for at in ABSENCE_TYPES:
        cursor.execute("SELECT id FROM absence_types WHERE name = ?", (at,))
        result = cursor.fetchone()
        if result:
            absence_type_ids[at] = result[0]

    absence_count = 0
    for emp_id in employee_ids:
        # 30% сотрудников имеют отсутствия
        if random.random() < 0.3:
            absence_type = random.choice(list(absence_type_ids.keys()))
            absence_type_id = absence_type_ids[absence_type]

            # Дата начала отсутствия (за последние 60 дней)
            start_date_abs = datetime.now().date() - timedelta(days=random.randint(5, 60))
            # Длительность отсутствия
            duration = random.randint(1, 14)
            end_date_abs = start_date_abs + timedelta(days=duration)

            # Проверяем, чтобы дата не была в будущем
            if end_date_abs > datetime.now().date():
                end_date_abs = datetime.now().date()

            try:
                cursor.execute("""
                    INSERT INTO absences (employee_id, absence_type_id, start_date, end_date, note)
                    VALUES (?, ?, ?, ?, ?)
                """, (emp_id, absence_type_id, start_date_abs, end_date_abs,
                      f"Тестовое отсутствие: {absence_type}"))
                absence_count += 1
            except sqlite3.Error:
                pass

    print(f"Добавлено {absence_count} записей отсутствий.")

    # 5. Статистика
    print("\n" + "=" * 50)
    print("СТАТИСТИКА БАЗЫ ДАННЫХ:")
    print("=" * 50)

    cursor.execute("SELECT COUNT(*) FROM employees")
    count_emp = cursor.fetchone()[0]
    print(f"Всего сотрудников: {count_emp}")

    cursor.execute("SELECT COUNT(*) FROM employees WHERE fire_date IS NULL")
    count_active = cursor.fetchone()[0]
    print(f"Активных сотрудников: {count_active}")

    cursor.execute("SELECT COUNT(*) FROM attendance")
    count_att = cursor.fetchone()[0]
    print(f"Записей посещаемости: {count_att}")

    cursor.execute("SELECT COUNT(*) FROM absences")
    count_abs = cursor.fetchone()[0]
    print(f"Записей отсутствий: {count_abs}")

    cursor.execute("SELECT COUNT(*) FROM departments")
    count_dept = cursor.fetchone()[0]
    print(f"Отделов: {count_dept}")

    # Информация по отделам
    print("\nРаспределение по отделам:")
    cursor.execute("""
        SELECT d.name, COUNT(e.id) as count
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id AND e.fire_date IS NULL
        GROUP BY d.id
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} сотрудников")

    # Информация по должностям
    print("\nТоп-5 должностей:")
    cursor.execute("""
        SELECT position, COUNT(*) as count
        FROM employees
        WHERE fire_date IS NULL
        GROUP BY position
        ORDER BY count DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    # Сохраняем изменения
    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print("БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
    print("=" * 50)

    print("\nВы можете запустить основное приложение и работать с данными.")


if __name__ == "__main__":
    main()