# Super Beautiful To-Do List (PyQt5)

A desktop To-Do List application built with PyQt5.

## Features

- Add tasks with due dates and priority levels.
- Search tasks instantly.
- Filter tasks by date, today, overdue status, or high priority.
- Edit existing tasks from the main form.
- Delete tasks you no longer need.
- Mark tasks as completed.
- Reopen completed tasks.
- Track completion progress with a progress bar.
- Show overdue task reminders.
- Persist ongoing and finished tasks in `tasks.json`.

## Installation

```bash
pip install PyQt5
```

## Usage

Run the application from the project folder:

```bash
python todo.py
```

## Storage

Tasks are saved in `tasks.json` next to `todo.py`.

Each task stores:

- A unique ID
- Task name
- Due date
- Priority
- Completion status

The app can still read the older storage format used by previous versions and will migrate it in memory when loaded.

## Project Structure

```text
TODOAPP/
|-- todo.py
|-- tasks.json
`-- README.md
```

## Notes

- Multiple tasks can now share the same name without overwriting each other.
- Finished tasks remain available after restarting the app.
- Overdue reminders are shown only when the overdue task set changes, which avoids repeated popups every minute for the same tasks.
- The UI includes a light/dark theme toggle, summary chips, and a faster task action row for edit/delete/reopen workflows.
