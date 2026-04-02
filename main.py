import csv
from datetime import date
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font

DRIVERS_FILE = "drivers.csv"
TRANSACTIONS_FILE = "transactions.csv"

drivers_db = {}
transactions = []
shift_line = [] # You'll need this for the queue later!

# This function pulls data from the CSV file into your computer's memory (the dictionary)
def load_drivers():
    # 1. Tell Python to use the global dictionary defined at the top of your script
    global drivers_db
    
    try:
        # 2. Open the file in 'r' (read) mode. 'with' ensures the file closes automatically.
        with open(DRIVERS_FILE, mode='r') as f:
            # 3. Create a reader object that splits the lines by commas
            reader = csv.reader(f)
            
            # 4. Loop through every row found in the CSV file
            for row in reader:
                # 5. CSV rows are lists: row[0] is the Body Number, row[1] is the Name.
                # We save it to the dictionary: drivers_db['001'] = 'Juan'
                if len(row) >= 2:  # Safety check to make sure the row isn't empty
                    drivers_db[row[0]] = row[1]
                    
    except FileNotFoundError:
        # 6. If the file doesn't exist (first time running), just skip this and move on.
        pass

# This function takes your dictionary and saves it back into the CSV file
def save_drivers():
    # 1. Access the global dictionary
    global drivers_db
    
    # 2. Open the file in 'w' (write) mode. 
    # newline='' prevents blank lines from appearing between rows on Windows.
    with open(DRIVERS_FILE, mode='w', newline='') as f:
        # 3. Create the writer tool
        writer = csv.writer(f)
        
        # 4. Loop through the dictionary items (both the key and the value)
        for body_num, name in drivers_db.items():
            # 5. Write the pair as a single row in the CSV
            writer.writerow([body_num, name])

def save_transaction(tx):
    # 'tx' is a dictionary containing the trip details
    # Open the file in 'a' mode (Append). This adds to the bottom.
    with open(TRANSACTIONS_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        # We take the values out of the dictionary and put them in a list
        # Order matters! Date, Time, Body #, Name, Type, Fee
        row = [tx['date'], tx['time'], tx['body'], tx['name'], tx['type'], tx['fee']]
        
        # This adds the single line to the bottom of the CSV
        writer.writerow(row)

def load_transactions():
    global transactions
    transactions = []
    # 1. Get today's date in a specific format: YYYY-MM-DD
    today = date.today().strftime('%Y-%m-%d')
    
    try:
        with open(TRANSACTIONS_FILE, mode='r') as f:
            reader = csv.reader(f)
            for row in reader:
                # 2. Check if the date in the CSV (row[0]) matches today's date
                if row[0] == today:
                    # 3. If it matches, turn it back into a dictionary and add to our list
                    tx_dict = {
                        'date': row[0],
                        'time': row[1],
                        'body': row[2],
                        'name': row[3],
                        'type': row[4],
                        'fee': float(row[5]) # Convert the string "40" into the number 40.0
                    }
                    transactions.append(tx_dict)
    except FileNotFoundError:
        pass

def save_new_driver():
    # 1. Grab what the dispatcher typed
    body_val = entry_admin_num.get()
    name_val = entry_name.get()

    # 2. Safety Check: If EITHER box is totally empty (""), don't save.
    if body_val == "" or name_val == "":
        print("Error: Both fields must be filled out!")
        # (Later, we can change this print to a cool pop-up error window)
    else:
        # 3. Add the new driver to your computer's memory (the dictionary)
        drivers_db[body_val] = name_val
        
        # 4. Permanently save it to the hard drive (your Phase 1 function)
        save_drivers()
        
        # 5. Clean up: Erase the entry boxes from start (0) to finish (tk.END)
        entry_admin_num.delete(0, tk.END)
        entry_name.delete(0, tk.END)
        
        # update driver listbox
        update_driver_listbox()

        print(f"Success: Driver {body_val} - {name_val} saved to database!")

def update_driver_listbox():
    # 1. Clear the listbox so we don't get duplicates when we refresh
    listbox_drivers.delete(0, tk.END)
    
    # 2. Loop through your dictionary
    for body_num, name in drivers_db.items():
        # 3. Create a nice looking string, like "001 - Juan dela Cruz"
        display_text = f"{body_num} - {name}"
        
        # 4. Insert it into the listbox
        listbox_drivers.insert(tk.END, display_text)

def check_in_driver():
    # Get the number from the Dashboard entry box
    body_val = entry_checkin_num.get()

    # Safety Check: Did they leave it blank?
    if body_val == "":
        messagebox.showwarning("Input Error", "Please enter a Body Number first.")
        return

    # Validation: Does this driver exist in the Admin Registry?
    if body_val not in drivers_db:
        messagebox.showerror("Not Found", f"Body Number {body_val} is not registered")
        return

    # 4. Logic: Is the driver already in line?
    if body_val in shift_line:
        messagebox.showinfo("Already In", f"Driver {body_val} is already in the queue.")
        return

    # 5. Success! Add them to the virtual list (the backend)
    shift_line.append(body_val)

    # 6. Success! Show them in the Listbox (the frontend)
    # We look up the name from the dictionary to make it look nice
    driver_name = drivers_db[body_val]
    list_queue.insert(tk.END, f"{body_val} - {driver_name}")

    # 7. Clean up the entry box
    entry_checkin_num.delete(0, tk.END)

root = tk.Tk()
root.title("B.A.R.K.E.R. - Tricycle Dispatch System")
root.geometry("1000x600") # Set a starting size for your app
print(font.families())

#  Create the notebook container
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both') # Make it fill the whole window

#  Create the 'pages' as Frames
tab_dashboard = ttk.Frame(notebook)
tab_admin = ttk.Frame(notebook)

# Add the pages to the notebook with labels
notebook.add(tab_dashboard, text="Dashboard")
notebook.add(tab_admin, text="Admin Registry")

# DASHBOARD

#  Create a Left Frame for the Queue
frame_left = tk.Frame(tab_dashboard, width=400, bd=2, relief="groove") 
frame_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# Label For Body Number Entry Box
lbl_entry_number = tk.Label(frame_left, text = "Enter Body Number:")
lbl_entry_number.pack(pady = 10)

# Entry Box for Body Number
entry_checkin_num = tk.Entry(frame_left, bd = 2)
entry_checkin_num.pack()

# Check In Button
button_checkIn = tk.Button(frame_left, text="Check In", command=check_in_driver)
button_checkIn.pack(pady=15)

list_queue = tk.Listbox(frame_left, bd = 1)
list_queue.pack(pady = 10 ,padx = 10, fill = "both", expand ="True")

#  Create a Right Frame for Stats/Logs
frame_right = tk.Frame(tab_dashboard, width=600, bd=2, relief="groove")
frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Dispatch Panel Label
lbl_dispatch = tk.Label(frame_right, text="Dispatch Panel", font=("Century Gothic", 20))
lbl_dispatch.pack(pady = 10)

# The Variable to Track the Radio Buttons
# This tells Python to remember which button is clicked. It defaults to "Regular".
ride_type = tk.StringVar(value="Regular")

# Radio Buttons
radio_regular = tk.Radiobutton(frame_right, text="Regular (%40 - 4 Pax)", variable=ride_type, value="Regular")
radio_regular.pack(anchor="w", padx=20, pady=5)

radio_special = tk.Radiobutton(frame_right, text="Special (Custom Fare)", variable=ride_type, value="Special")
radio_special.pack(anchor="w", padx=20, pady=5)

# Entry Box for Special Fare
lbl_special_fare = tk.Label(frame_right, text="If Special, enter amount (₱):")
lbl_special_fare.pack(pady=(15, 0))

entry_special_fare = tk.Entry(frame_right, bd=2)
entry_special_fare.pack(pady=5)

# Dispatch Button (We will add the command later!)
button_dispatch = tk.Button(frame_right, text="Dispatch Tricycle", bg="green", fg="white", font=("Arial", 10, "bold"))
button_dispatch.pack(pady=20)

# Total Fare Label
lbl_total_fare = tk.Label(frame_right)

# ADMIN REGISTRY 

# Create the Label, Parent it to tab_admin, and set the text
lbl_name = tk.Label(tab_admin, text="Driver Name:")
#  Pack it so it actually appears on the screen
lbl_name.pack(pady=5)

#  Create the Entry box and Parent it to tab_admin
entry_name = tk.Entry(tab_admin)
#  Pack it onto the screen right below the label
entry_name.pack(pady=5)

# Create Label for Body Number
lbl_number = tk.Label(tab_admin, text="Body Number:")
lbl_number.pack(pady=5)

# Create Entry box for body number
entry_admin_num = tk.Entry(tab_admin)
entry_admin_num.pack(pady=5)

# Save button
button_save = tk.Button(tab_admin, text="Save", command=save_new_driver)
button_save.pack(pady=10)

# Display List of Drivers
listbox_drivers = tk.Listbox(tab_admin)
listbox_drivers.pack(fill="both", expand=True, padx=20, pady=10)







load_drivers()
load_transactions()
update_driver_listbox()
root.mainloop()