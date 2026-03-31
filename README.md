# B.A.R.K.E.R. - Tricycle Dispatch System 🛺

B.A.R.K.E.R. is a Python-based desktop application designed to manage tricycle terminal dispatching. Built using Tkinter for the graphical user interface and CSV for lightweight database management, this system digitizes driver registration and terminal queueing.

## 🚀 Features

* **Admin Registry:** Register new tricycle drivers by entering their Body Number and Name.
* **Persistent Storage:** Driver data is automatically saved to a local `drivers.csv` file, ensuring no data is lost when the application is closed.
* **Live Roster:** View a real-time, scrollable list of all registered drivers.
* **Shift Line Queueing:** Dispatchers can "Check In" drivers as they arrive at the terminal.
* **Smart Error Handling:** The check-in system automatically prevents unregistered drivers from joining the queue and stops drivers from being added to the line twice.

## 💻 Tech Stack

* **Language:** Python 3
* **Frontend/GUI:** Tkinter (`ttk.Notebook`, `Frame`, `Listbox`, `Entry`, `Button`)
* **Backend/Storage:** Python `csv` module
* **Alerts:** Tkinter `messagebox`

## 🛠️ How to Run

1. Make sure you have [Python](https://www.python.org/downloads/) installed on your computer.
2. Clone this repository to your local machine:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/final_project-tkinter.git](https://github.com/YOUR_USERNAME/final_project-tkinter.git)
