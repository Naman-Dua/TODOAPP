# 📝 Super Beautiful To-Do List (PyQt5)

A modern and user-friendly desktop To-Do List application built with **PyQt5**.
This app helps you manage your daily tasks with priorities, due dates, progress tracking, and a clean interface.

---

## ✨ Features

* ➕ Add tasks with:

  * Due dates
  * Priority levels (Low, Medium, High)
* 📅 Filter tasks by date
* ✅ Mark tasks as completed
* 📊 Visual progress bar showing completion percentage
* 🔔 Automatic overdue task notifications
* 🎨 Clean UI with light/dark theme support (ready)
* 📂 Persistent storage using `JSON`

---

## 🖼️ Interface Overview

* Task input field
* Due date picker
* Priority selector
* Task lists:

  * Ongoing tasks
  * Finished tasks
* Progress bar
* Filter by date
* Hide finished tasks toggle

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/todo-pyqt5.git
cd todo-pyqt5
```

### 2. Install dependencies

```bash
pip install PyQt5
```

---

## ▶️ Usage

Run the application:

```bash
python main.py
```

---

## 🧠 How It Works

* Tasks are stored in a local file: `tasks.json`
* Each task contains:

  * Task name
  * Due date
  * Priority level
* The app automatically:

  * Updates UI lists
  * Tracks progress
  * Checks for overdue tasks every minute

---

## 📁 Project Structure

```
todo-pyqt5/
│
├── main.py          # Main application file
├── tasks.json       # Stored tasks (auto-created)
└── README.md        # Project documentation
```

---

## 📊 Progress Calculation

Progress is calculated as:

```
(Completed Tasks / Total Tasks) × 100
```

Color indicators:

* 🔴 Red → < 50%
* 🟠 Orange → 50% – 79%
* 🟢 Green → 80%+

---

## ⚠️ Known Limitations

* Tasks with the same name overwrite each other
* Finished tasks are not persisted (can be improved)
* No edit/delete functionality yet
* Overdue notifications may repeat frequently

---

## 🚀 Future Improvements

* ✏️ Edit tasks
* 🗑️ Delete tasks
* 🌙 Toggle dark mode
* 🔍 Search functionality
* ☁️ Cloud sync
* 📱 Mobile version

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

## 💡 Author

Built with ❤️ using PyQt5.

---

## ⭐ Support

If you like this project, consider giving it a star ⭐ on GitHub!
