import json
import sys
import uuid
from pathlib import Path

from PyQt5.QtCore import QDate, QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


TASKS_FILE = Path(__file__).resolve().parent / "tasks.json"


class TodoApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Super Beautiful To-Do List")
        self.setGeometry(220, 120, 840, 760)

        self.is_dark_mode = False
        self.tasks = []
        self.editing_task_id = None
        self.last_overdue_signature = ()
        self.selection_guard = False

        self.load_tasks()
        self.init_ui()
        self.refresh_styles()

        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_due_dates)
        self.notification_timer.start(60000)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        self.title_label = QLabel("Task Horizon")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title_block.addWidget(self.title_label)

        self.subtitle_label = QLabel("Plan faster, filter smarter, and keep momentum visible.")
        title_block.addWidget(self.subtitle_label)

        header_row.addLayout(title_block)
        header_row.addStretch()

        self.theme_button = QPushButton("Switch Theme", self)
        self.theme_button.clicked.connect(self.toggle_theme)
        header_row.addWidget(self.theme_button)

        main_layout.addLayout(header_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.total_chip = QLabel("Total: 0")
        self.active_chip = QLabel("Active: 0")
        self.completed_chip = QLabel("Done: 0")
        self.overdue_chip = QLabel("Overdue: 0")
        for chip in (self.total_chip, self.active_chip, self.completed_chip, self.overdue_chip):
            chip.setAlignment(Qt.AlignCenter)
            stats_row.addWidget(chip)
        main_layout.addLayout(stats_row)

        compose_row = QHBoxLayout()
        compose_row.setSpacing(10)

        self.task_entry = QLineEdit(self)
        self.task_entry.setPlaceholderText("Enter your task")
        self.task_entry.returnPressed.connect(self.add_task)
        compose_row.addWidget(self.task_entry, 3)

        self.due_date_picker = QDateEdit(self)
        self.due_date_picker.setCalendarPopup(True)
        self.due_date_picker.setDate(QDate.currentDate())
        compose_row.addWidget(self.due_date_picker, 1)

        self.priority_combobox = QComboBox(self)
        self.priority_combobox.addItems(["Low", "Medium", "High"])
        self.priority_combobox.setCurrentText("Medium")
        compose_row.addWidget(self.priority_combobox, 1)

        self.add_task_button = QPushButton("Add Task", self)
        self.add_task_button.clicked.connect(self.add_task)
        compose_row.addWidget(self.add_task_button, 1)

        self.cancel_edit_button = QPushButton("Cancel Edit", self)
        self.cancel_edit_button.clicked.connect(self.cancel_edit)
        compose_row.addWidget(self.cancel_edit_button, 1)

        main_layout.addLayout(compose_row)

        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search tasks...")
        self.search_input.textChanged.connect(self.update_task_lists)
        filters_row.addWidget(self.search_input, 3)

        self.view_filter_combobox = QComboBox(self)
        self.view_filter_combobox.addItems(["All Tasks", "Selected Date", "Today", "Overdue", "High Priority"])
        self.view_filter_combobox.currentTextChanged.connect(self.update_task_lists)
        filters_row.addWidget(self.view_filter_combobox, 1)

        self.date_filter_picker = QDateEdit(self)
        self.date_filter_picker.setCalendarPopup(True)
        self.date_filter_picker.setDate(QDate.currentDate())
        self.date_filter_picker.dateChanged.connect(self.update_task_lists)
        filters_row.addWidget(self.date_filter_picker, 1)

        main_layout.addLayout(filters_row)

        self.ongoing_label = QLabel("In Progress")
        self.ongoing_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(self.ongoing_label)

        self.ongoing_tasks_list = QListWidget(self)
        self.ongoing_tasks_list.itemSelectionChanged.connect(self.sync_ongoing_selection)
        self.ongoing_tasks_list.itemDoubleClicked.connect(lambda _: self.start_edit_selected_task())
        main_layout.addWidget(self.ongoing_tasks_list)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.mark_done_button = QPushButton("Mark as Done", self)
        self.mark_done_button.clicked.connect(self.mark_done)
        action_row.addWidget(self.mark_done_button)

        self.edit_button = QPushButton("Edit Selected", self)
        self.edit_button.clicked.connect(self.start_edit_selected_task)
        action_row.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Selected", self)
        self.delete_button.clicked.connect(self.delete_selected_task)
        action_row.addWidget(self.delete_button)

        self.reopen_button = QPushButton("Reopen Selected", self)
        self.reopen_button.clicked.connect(self.reopen_task)
        action_row.addWidget(self.reopen_button)

        action_row.addStretch()

        self.hide_finished_checkbox = QCheckBox("Hide Finished Tasks", self)
        self.hide_finished_checkbox.stateChanged.connect(self.toggle_hide_finished)
        action_row.addWidget(self.hide_finished_checkbox)

        main_layout.addLayout(action_row)

        self.finished_label = QLabel("Completed")
        self.finished_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        main_layout.addWidget(self.finished_label)

        self.finished_tasks_list = QListWidget(self)
        self.finished_tasks_list.itemSelectionChanged.connect(self.sync_finished_selection)
        self.finished_tasks_list.itemDoubleClicked.connect(lambda _: self.start_edit_selected_task())
        main_layout.addWidget(self.finished_tasks_list)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)
        self.update_task_lists()

    def get_input_style(self):
        if self.is_dark_mode:
            return """
                padding: 12px;
                font-size: 15px;
                border-radius: 14px;
                border: 1px solid #334155;
                background-color: #18202a;
                color: #f8fafc;
            """
        return """
            padding: 12px;
            font-size: 15px;
            border-radius: 14px;
            border: 1px solid #d7c8b6;
            background-color: #fffaf2;
            color: #1f2937;
        """

    def get_button_style(self, variant="primary"):
        if self.is_dark_mode:
            styles = {
                "primary": """
                    background-color: #f59e0b;
                    color: #111827;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: none;
                    font-weight: 600;
                """,
                "secondary": """
                    background-color: #253244;
                    color: #e2e8f0;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: 1px solid #334155;
                    font-weight: 600;
                """,
                "danger": """
                    background-color: #ea580c;
                    color: white;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: none;
                    font-weight: 600;
                """,
            }
        else:
            styles = {
                "primary": """
                    background-color: #d97706;
                    color: white;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: none;
                    font-weight: 600;
                """,
                "secondary": """
                    background-color: #efe4d6;
                    color: #1f2937;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: 1px solid #d7c8b6;
                    font-weight: 600;
                """,
                "danger": """
                    background-color: #c2410c;
                    color: white;
                    font-size: 15px;
                    padding: 10px 14px;
                    border-radius: 14px;
                    border: none;
                    font-weight: 600;
                """,
            }
        return styles[variant]

    def get_list_style(self):
        if self.is_dark_mode:
            return """
                font-size: 15px;
                background-color: #18202a;
                color: #f8fafc;
                border-radius: 16px;
                border: 1px solid #334155;
                padding: 10px;
            """
        return """
            font-size: 15px;
            background-color: #fffaf2;
            color: #1f2937;
            border-radius: 16px;
            border: 1px solid #d7c8b6;
            padding: 10px;
        """

    def get_progress_style(self, chunk_color):
        background = "#273142" if self.is_dark_mode else "#eadfce"
        return f"""
            QProgressBar {{
                border-radius: 12px;
                height: 22px;
                background-color: {background};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 12px;
            }}
        """

    def get_chip_style(self):
        if self.is_dark_mode:
            return """
                background-color: #223042;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 10px 12px;
                font-weight: 600;
            """
        return """
            background-color: #efe4d6;
            color: #1f2937;
            border: 1px solid #d7c8b6;
            border-radius: 16px;
            padding: 10px 12px;
            font-weight: 600;
        """

    def refresh_styles(self):
        window_color = "#141a20" if self.is_dark_mode else "#f4efe7"
        text_color = "#f8fafc" if self.is_dark_mode else "#1f2937"
        muted_color = "#94a3b8" if self.is_dark_mode else "#6b7280"

        self.setStyleSheet(f"background-color: {window_color}; color: {text_color};")
        self.title_label.setStyleSheet(f"color: {text_color};")
        self.subtitle_label.setStyleSheet(f"color: {muted_color}; font-size: 13px;")
        self.ongoing_label.setStyleSheet(f"color: {text_color};")
        self.finished_label.setStyleSheet(f"color: {text_color};")
        self.status_label.setStyleSheet(f"color: {muted_color}; font-size: 13px;")

        for chip in (self.total_chip, self.active_chip, self.completed_chip, self.overdue_chip):
            chip.setStyleSheet(self.get_chip_style())

        for widget in (
            self.task_entry,
            self.due_date_picker,
            self.priority_combobox,
            self.search_input,
            self.view_filter_combobox,
            self.date_filter_picker,
        ):
            widget.setStyleSheet(self.get_input_style())

        for widget in (self.ongoing_tasks_list, self.finished_tasks_list):
            widget.setStyleSheet(self.get_list_style())

        self.add_task_button.setStyleSheet(self.get_button_style("primary"))
        self.cancel_edit_button.setStyleSheet(self.get_button_style("secondary"))
        self.theme_button.setStyleSheet(self.get_button_style("secondary"))
        self.mark_done_button.setStyleSheet(self.get_button_style("secondary"))
        self.edit_button.setStyleSheet(self.get_button_style("secondary"))
        self.reopen_button.setStyleSheet(self.get_button_style("secondary"))
        self.delete_button.setStyleSheet(self.get_button_style("danger"))
        self.theme_button.setText("Light Theme" if self.is_dark_mode else "Dark Theme")
        self.toggle_hide_finished()
        self.update_progress()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.refresh_styles()

    def active_tasks(self):
        return [task for task in self.tasks if not task["completed"]]

    def completed_tasks(self):
        return [task for task in self.tasks if task["completed"]]

    def add_task(self):
        task_name = self.task_entry.text().strip()
        due_date = self.due_date_picker.date().toString("yyyy-MM-dd")
        priority = self.priority_combobox.currentText()

        if not task_name:
            QMessageBox.warning(self, "Input Error", "Please enter a task.")
            return

        if self.editing_task_id:
            task = self.find_task(self.editing_task_id)
            if task:
                task["name"] = task_name
                task["due_date"] = due_date
                task["priority"] = priority
        else:
            self.tasks.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": task_name,
                    "due_date": due_date,
                    "priority": priority,
                    "completed": False,
                }
            )

        self.cancel_edit()
        self.save_tasks()
        self.update_task_lists()

    def update_task_lists(self):
        priority_map = {"Low": 1, "Medium": 2, "High": 3}
        selected_date = self.date_filter_picker.date().toString("yyyy-MM-dd")
        today = QDate.currentDate().toString("yyyy-MM-dd")
        query = self.search_input.text().strip().lower()
        filter_mode = self.view_filter_combobox.currentText()

        self.ongoing_tasks_list.clear()
        ongoing_tasks = sorted(
            self.active_tasks(),
            key=lambda task: (task["due_date"], -priority_map.get(task["priority"], 0), task["name"].lower()),
        )

        visible_ongoing = 0
        for task in ongoing_tasks:
            if query and query not in f"{task['name']} {task['priority']} {task['due_date']}".lower():
                continue

            if filter_mode == "Selected Date" and task["due_date"] != selected_date:
                continue
            if filter_mode == "Today" and task["due_date"] != today:
                continue
            if filter_mode == "Overdue" and task["due_date"] >= today:
                continue
            if filter_mode == "High Priority" and task["priority"] != "High":
                continue

            task_display = f"{task['name']}\nDue: {task['due_date']} | Priority: {task['priority']} | Status: Open"
            item = QListWidgetItem(task_display)
            item.setData(Qt.UserRole, task["id"])
            self.ongoing_tasks_list.addItem(item)
            visible_ongoing += 1

        self.finished_tasks_list.clear()
        visible_finished = 0
        if not self.hide_finished_checkbox.isChecked():
            for task in self.completed_tasks():
                if query and query not in f"{task['name']} {task['priority']} {task['due_date']}".lower():
                    continue
                if filter_mode == "Selected Date" and task["due_date"] != selected_date:
                    continue
                if filter_mode == "Today" and task["due_date"] != today:
                    continue
                if filter_mode == "High Priority" and task["priority"] != "High":
                    continue
                if filter_mode == "Overdue":
                    continue

                task_display = f"{task['name']}\nDue: {task['due_date']} | Priority: {task['priority']} | Status: Done"
                item = QListWidgetItem(task_display)
                item.setData(Qt.UserRole, task["id"])
                self.finished_tasks_list.addItem(item)
                visible_finished += 1

        overdue_count = sum(1 for task in self.active_tasks() if task["due_date"] < today)
        self.total_chip.setText(f"Total: {len(self.tasks)}")
        self.active_chip.setText(f"Active: {len(self.active_tasks())}")
        self.completed_chip.setText(f"Done: {len(self.completed_tasks())}")
        self.overdue_chip.setText(f"Overdue: {overdue_count}")
        self.status_label.setText(
            f"Showing {visible_ongoing} active tasks and {visible_finished} completed tasks for {filter_mode.lower()}."
        )
        self.update_progress()
        self.update_action_buttons()

    def update_progress(self):
        total_tasks = len(self.tasks)
        if total_tasks == 0:
            self.progress_bar.setStyleSheet(self.get_progress_style("#4CAF50"))
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("No tasks yet")
            return

        completed_count = len(self.completed_tasks())
        progress = (completed_count / total_tasks) * 100

        if progress < 50:
            chunk_color = "red"
        elif progress < 80:
            chunk_color = "orange"
        else:
            chunk_color = "green"

        self.progress_bar.setStyleSheet(self.get_progress_style(chunk_color))
        self.progress_bar.setValue(int(progress))
        self.progress_bar.setFormat(f"{int(progress)}% complete")

    def mark_done(self):
        selected_item = self.ongoing_tasks_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a task to mark as done.")
            return

        task_id = selected_item.data(Qt.UserRole)
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                break

        self.save_tasks()
        self.update_task_lists()

    def toggle_hide_finished(self):
        hidden = self.hide_finished_checkbox.isChecked()
        self.finished_label.setVisible(not hidden)
        self.finished_tasks_list.setVisible(not hidden)
        self.update_task_lists()

    def sync_ongoing_selection(self):
        if self.selection_guard:
            return
        self.selection_guard = True
        self.finished_tasks_list.clearSelection()
        self.selection_guard = False
        self.update_action_buttons()

    def sync_finished_selection(self):
        if self.selection_guard:
            return
        self.selection_guard = True
        self.ongoing_tasks_list.clearSelection()
        self.selection_guard = False
        self.update_action_buttons()

    def update_action_buttons(self):
        has_ongoing = self.ongoing_tasks_list.currentItem() is not None
        has_finished = self.finished_tasks_list.currentItem() is not None
        has_selection = has_ongoing or has_finished

        self.mark_done_button.setEnabled(has_ongoing)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.reopen_button.setEnabled(has_finished)

    def get_selected_task(self):
        selected_item = self.ongoing_tasks_list.currentItem() or self.finished_tasks_list.currentItem()
        if not selected_item:
            return None
        return self.find_task(selected_item.data(Qt.UserRole))

    def find_task(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def start_edit_selected_task(self):
        task = self.get_selected_task()
        if not task:
            QMessageBox.warning(self, "Selection Error", "Please select a task to edit.")
            return

        self.editing_task_id = task["id"]
        self.task_entry.setText(task["name"])
        self.due_date_picker.setDate(QDate.fromString(task["due_date"], "yyyy-MM-dd"))
        self.priority_combobox.setCurrentText(task["priority"])
        self.add_task_button.setText("Save Changes")
        self.status_label.setText(f"Editing '{task['name']}'. Update the form and click Save Changes.")

    def cancel_edit(self):
        self.editing_task_id = None
        self.task_entry.clear()
        self.due_date_picker.setDate(QDate.currentDate())
        self.priority_combobox.setCurrentText("Medium")
        self.add_task_button.setText("Add Task")

    def delete_selected_task(self):
        task = self.get_selected_task()
        if not task:
            QMessageBox.warning(self, "Selection Error", "Please select a task to delete.")
            return

        answer = QMessageBox.question(
            self,
            "Delete Task",
            f"Delete '{task['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.tasks = [existing_task for existing_task in self.tasks if existing_task["id"] != task["id"]]
        self.cancel_edit()
        self.save_tasks()
        self.update_task_lists()

    def reopen_task(self):
        selected_item = self.finished_tasks_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selection Error", "Please select a completed task to reopen.")
            return

        task = self.find_task(selected_item.data(Qt.UserRole))
        if task:
            task["completed"] = False
            self.save_tasks()
            self.update_task_lists()

    def check_due_dates(self):
        today = QDate.currentDate().toString("yyyy-MM-dd")
        overdue_tasks = sorted(
            task["name"] for task in self.active_tasks() if task["due_date"] < today
        )
        overdue_signature = tuple(overdue_tasks)

        if overdue_tasks and overdue_signature != self.last_overdue_signature:
            self.last_overdue_signature = overdue_signature
            QMessageBox.warning(
                self,
                "Overdue Tasks",
                f"You have overdue tasks: {', '.join(overdue_tasks)}",
            )
        elif not overdue_tasks:
            self.last_overdue_signature = ()

    def save_tasks(self):
        with TASKS_FILE.open("w", encoding="utf-8") as file:
            json.dump({"tasks": self.tasks}, file, indent=2)

    def load_tasks(self):
        try:
            with TASKS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            self.tasks = []
            return
        except json.JSONDecodeError:
            self.tasks = []
            return

        if isinstance(data, dict) and "tasks" in data:
            self.tasks = [self.normalize_task(task) for task in data["tasks"]]
            return

        if isinstance(data, dict):
            # Migrate the original {task_name: {due_date, priority}} format.
            self.tasks = [
                {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "due_date": details.get("due_date", QDate.currentDate().toString("yyyy-MM-dd")),
                    "priority": details.get("priority", "Low"),
                    "completed": False,
                }
                for name, details in data.items()
            ]
            return

        self.tasks = []

    def normalize_task(self, task):
        return {
            "id": task.get("id", str(uuid.uuid4())),
            "name": task.get("name", "").strip(),
            "due_date": task.get("due_date", QDate.currentDate().toString("yyyy-MM-dd")),
            "priority": task.get("priority", "Low"),
            "completed": bool(task.get("completed", False)),
        }


def main():
    app = QApplication(sys.argv)
    window = TodoApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
