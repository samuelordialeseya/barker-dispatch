import datetime
import csv
from datetime import date
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font

"""
B.A.R.K.E.R. - Tricycle Dispatch System

A comprehensive management system for tricycle drivers designed to:
1. Maintain a fair, automatic waiting queue using FIFO (First-In-First-Out) rotation
2. Track fares and calculate daily earnings using recursive functions
3. Quickly search driver profiles and manage incident/complaint records

CORE FEATURES:
- Dashboard Tab: Real-time queue management, dispatch operations, and trip history
- Admin Registry Tab: Driver registration, profile lookup, and incident tracking

DATA STRUCTURES:
- drivers_db (dict): Master driver registry with profiles
  Format: {body_num: {"name": str, "standing": str, "incidents": [list], "resolved": str}}
  
- shift_line (list): Active dispatch queue with driver status tracking
  Format: [{"body_num": str, "status": str, "ride_type": str, "fare": float}, ...]
  Status values: "waiting" or "dispatched"

- daily_earnings.csv: Transaction log for all completed rides
  Format: timestamp | body_num | ride_type | fare_amount

- drivers.csv: Persistent driver database
  Format: body_num | name | standing | incidents_serialized | resolved

WORKFLOW:
1. Check In: Driver joins queue with 'waiting' status
2. Dispatch: First waiting driver is selected and dispatched with ride details
3. Complete: Driver returns and re-joins end of queue (FIFO rotation)
4. Track: All transactions logged to daily_earnings.csv
5. Report: Generate daily totals and search driver history/incidents

PROFESSIONAL THEME:
- Font: Georgia serif (24pt bold titles, 11pt buttons, 10pt content)
- Colors: Green (#2E7D32) for positive actions, Blue (#1976D2) for info,
          Red (#D32F2F) for destructive actions, Orange (#F57C00) for warnings
"""

DRIVERS_FILE = "drivers.csv"

drivers_db = {}
shift_line = []  # Now stores dicts: {"body_num": "001", "status": "waiting", "ride_type": "Regular", "fare": 40}

# Load all registered drivers from CSV into memory
def load_drivers():
    """Load driver data from CSV file into the drivers_db dictionary.
    
    Parses driver information including name, standing, incidents list,
    and resolution status. Handles missing data gracefully.
    """
    global drivers_db
    try:
        with open(DRIVERS_FILE, mode='r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    # We use if/else logic to prevent crashes if old data is missing columns
                    incidents_str = row[3] if len(row) > 3 else ""
                    # Parse incidents from format "type1|desc1||type2|desc2"
                    incidents = []
                    if incidents_str and incidents_str != "None":
                        incident_pairs = incidents_str.split("||")
                        for pair in incident_pairs:
                            if "|" in pair:
                                inc_type, inc_desc = pair.split("|", 1)
                                incidents.append({"type": inc_type, "desc": inc_desc})
                    
                    drivers_db[row[0]] = {
                        "name": row[1],
                        "standing": row[2] if len(row) > 2 else "Good",
                        "incidents": incidents,
                        "resolved": row[4] if len(row) > 4 else "Yes"
                    }
    except FileNotFoundError:
        pass

# Save all driver data to CSV file
def save_drivers():
    """Save all driver data from memory to CSV file.
    
    Serializes incidents list to pipe-delimited format for storage.
    Overwrites existing file with current state.
    """
    global drivers_db
    with open(DRIVERS_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        for body_num, data in drivers_db.items():
            # Serialize incidents to format "type1|desc1||type2|desc2"
            incidents_str = ""
            if data["incidents"]:
                incidents_str = "||".join([f"{inc['type']}|{inc['desc']}" for inc in data["incidents"]])
            else:
                incidents_str = "None"
            # Write all data to the row
            writer.writerow([body_num, data["name"], data["standing"], incidents_str, data["resolved"]])

# Add a new driver to the database
def save_new_driver():
    """Create a new driver record with empty incident history.
    
    Validates that both body number and name are provided.
    Saves to database and updates UI display.
    """
    body_val = entry_admin_num.get()
    name_val = entry_name.get()

    if body_val == "" or name_val == "":
        messagebox.showerror("Error", "Both fields must be filled out!")
    else:
        # Give brand new drivers a perfectly clean slate
        drivers_db[body_val] = {
            "name": name_val,
            "standing": "Good",
            "incidents": [],
            "resolved": "Yes"
        }
        save_drivers()
        entry_admin_num.delete(0, tk.END)
        entry_name.delete(0, tk.END)
        update_driver_listbox()
        messagebox.showinfo("Success", f"Driver {body_val} saved!")

# Refresh the driver list display
def update_driver_listbox():
    """Refresh the driver listbox in Admin Registry tab.
    
    Clears existing list and repopulates with all registered drivers
    in 'Body# - Name' format.
    """
    # 1. Clear the listbox so we don't get duplicates when we refresh
    listbox_drivers.delete(0, tk.END)
    
    # 2. Loop through your dictionary
    for body_num, data in drivers_db.items():
        # 3. Create a nice looking string, like "001 - Juan dela Cruz"
        display_text = f"{body_num} - {data['name']}"
        
        # 4. Insert it into the listbox
        listbox_drivers.insert(tk.END, display_text)

# Refresh the dispatch queue display
def update_queue_display():
    """Update the queue listbox showing all drivers and their status.
    
    Displays drivers with their body number, name, status, and
    dispatch details (ride type and fare if applicable).
    """
    # Clear the listbox
    list_queue.delete(0, tk.END)
    
    # Display all drivers in queue with their status
    for driver in shift_line:
        body_num = driver["body_num"]
        driver_name = drivers_db[body_num]["name"]
        status = driver["status"].upper()
        
        if driver["status"] == "dispatched":
            display_text = f"[{body_num}] {driver_name} - DISPATCHED ({driver['ride_type']}, ₱{driver['fare']})"
        else:
            display_text = f"[{body_num}] {driver_name} - {status}"
        
        list_queue.insert(tk.END, display_text)

# Add a driver to the dispatch queue
def check_in_driver():
    """Check in a driver to the waiting queue.
    
    Validates driver exists and is not already in queue.
    Adds to shift_line with 'waiting' status.
    """
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

    # Check: Is the driver already in line?
    for driver in shift_line:
        if driver["body_num"] == body_val:
            messagebox.showinfo("Already In", f"Driver {body_val} is already in the queue.")
            return

    # Success! Add them to the virtual list (the backend) with status
    shift_line.append({
        "body_num": body_val,
        "status": "waiting",
        "ride_type": None,
        "fare": None
    })

    # Success! Show them in the Listbox (the frontend)
    driver_name = drivers_db[body_val]["name"]
    list_queue.insert(tk.END, f"[{body_val}] {driver_name} - WAITING")

    # Clean up the entry box
    entry_checkin_num.delete(0, tk.END)

# Dispatch the first waiting driver
def dispatch_driver():
    """Send the first waiting driver on a ride.
    
    Updates driver status to 'dispatched', logs the transaction,
    and records fare based on ride type (Regular or Special).
    """
    ride_type_get = ride_type.get()

    # Check if shift_line is empty
    if not shift_line:
        messagebox.showwarning("Warning","The line is empty")
        return
    
    # Find the first waiting driver
    waiting_driver = None
    for driver in shift_line:
        if driver["status"] == "waiting":
            waiting_driver = driver
            break
    
    if not waiting_driver:
        messagebox.showwarning("Warning","No waiting drivers to dispatch")
        return
    
    if ride_type_get == "Regular":
        fare = 40
    else:
        special_fare = entry_special_fare.get()
        if special_fare == "":
            messagebox.showerror("Error", "Empty Special Fare")
            return
        else:
            fare = special_fare
    
    # Update driver status to dispatched
    waiting_driver["status"] = "dispatched"
    waiting_driver["ride_type"] = ride_type_get
    waiting_driver["fare"] = fare

    # Clear fare entry box
    entry_special_fare.delete(0, tk.END)

    # Log earning
    log_earnings(waiting_driver["body_num"], ride_type_get, fare)

    # Refresh queue display
    update_queue_display()

    view_history()

    # Success Message
    messagebox.showinfo("Success", f"Driver {waiting_driver['body_num']} dispatched!\nTotal Fare Collected: ₱{fare}")

# Record a trip transaction to earnings file
def log_earnings(body_num, ride_type_val, fare_amount):
    """Write a completed trip to the daily earnings CSV.
    
    Records timestamp, driver body number, ride type, and fare amount.
    """
    # Get current time
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Open the CSV in "a" (append) mode. 
    # (newline="" prevents weird blank rows between entries on Windows)
    with open("daily_earnings.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        
        # Write a single row with the transaction details
        writer.writerow([now, body_num, ride_type_val, fare_amount])

# Calculate total earnings using recursion
def calculate_total_earnings(fares_list):
    """Recursively sum all fares in a list.
    
    Base case: empty list returns 0.
    Recursive case: add first fare to result of remaining list.
    """
    # Base Case
    if len(fares_list) == 0:
        return 0 
    
    else:
        # Take the first fare, and add it to the result of the rest of the list
        return fares_list[0] + calculate_total_earnings(fares_list[1:])

# Display total daily earnings
def show_daily_total():
    """Calculate and show today's total fares and trip count.
    
    Reads daily_earnings.csv, filters by today's date,
    and recursively sums all fares.
    """
    all_fares = []
    today = date.today().strftime("%Y-%m-%d")
    
    try:
        with open("daily_earnings.csv", mode='r') as file:
            reader = csv.reader(file)
            # Loop through each row in the CSV - only today's transactions
            for row in reader:
                # Safety check: make sure the row isn't blank
                if len(row) >= 4:
                    # Check if this transaction is from today
                    transaction_date = row[0].split(" ")[0]  # Extract date part
                    if transaction_date == today:
                        # The fare is the 4th item (index 3)
                        try:
                            fare_number = float(row[3])
                            all_fares.append(fare_number)
                        except ValueError:
                            pass
        
        if all_fares:
            grand_total = calculate_total_earnings(all_fares)
            num_trips = len(all_fares)
            # Show Total with trip count
            messagebox.showinfo("Daily Report", f"Total Fares Collected Today: ₱{grand_total}\n\nTrips: {num_trips}")
        else:
            messagebox.showinfo("Daily Report", "No dispatch records yet for today. Total: ₱0")

    except FileNotFoundError:
        # If file doesn't exist yet, they made 0 pesos.
        messagebox.showinfo("Daily Report", "No dispatch records yet for today. Total: ₱0")

# Display trip history for a specific date
def view_history_by_date(selected_date=None):
    """Show all trips from a selected date in reverse chronological order.
    
    Defaults to today if no date provided. Displays time, body number,
    driver name, ride type, and fare for each trip.
    """
    # 1. Clear the listbox first so we don't duplicate history
    listbox_history.delete(0, tk.END)
    
    # Get the selected date or use today's date
    if selected_date:
        date_str = selected_date.strftime("%Y-%m-%d")
    else:
        date_str = date.today().strftime("%Y-%m-%d")
    
    try:
        # 2. Open the CSV in "r" (read) mode
        with open("daily_earnings.csv", mode="r") as file:
            reader = csv.reader(file)
            
            # 3. Collect today's transactions
            todays_transactions = []
            for row in reader:
                # Safety check: make sure the row has all 4 pieces of data
                if len(row) >= 4:
                    # Check if this transaction is from selected date
                    transaction_date = row[0].split(" ")[0]  # Extract date part (YYYY-MM-DD)
                    if transaction_date == date_str:
                        todays_transactions.append(row)
            
            # 4. Sort transactions by timestamp (most recent first)
            todays_transactions.sort(key=lambda x: x[0], reverse=True)
            
            # 5. Display sorted transactions with driver names
            if todays_transactions:
                for row in todays_transactions:
                    # row[0] is time, row[1] is body num, row[2] is ride type, row[3] is fare
                    time = row[0]
                    body_num = row[1]
                    ride_type = row[2]
                    fare = row[3]
                    
                    # Lookup driver name
                    driver_name = drivers_db.get(body_num, {}).get("name", "Unknown")
                    
                    # Format: "10:30 | Body: 001 | Juan dela Cruz | Regular | ₱40"
                    display_text = f"{time} | Body: {body_num} | {driver_name} | {ride_type} | ₱{fare}"
                    listbox_history.insert(tk.END, display_text)
            else:
                listbox_history.insert(tk.END, f"No trips recorded on {date_str}.")
                    
    except FileNotFoundError:
        # If no trips have happened on this date
        listbox_history.insert(tk.END, f"No trip records found for {date_str}.")

# Display today's trip history
def view_history():
    """Show today's trip history by calling view_history_by_date().
    """
    # Default view for today
    view_history_by_date()

# Remove a driver from the dispatch queue
def remove_from_queue():
    """Remove selected driver from the queue without re-adding.
    
    Validates that a driver is selected before removal.
    """
    # Check if curselected
    if not list_queue.curselection():
        messagebox.showwarning("Warning","Please select a driver first")
        return
    
    # Get position of driver to remove
    index = list_queue.curselection()[0]

    # Get driver info before removing
    removed_driver = shift_line[index]
    body_num = removed_driver["body_num"]

    # Remove driver from queue
    shift_line.pop(index)

    # Update display
    update_queue_display()

    messagebox.showinfo("Success",f"Driver {body_num} removed from queue")
    return

# Complete a ride and return driver to queue
def complete_ride():
    """Mark a dispatched driver as arrived and return to queue (FIFO).
    
    Removes driver from current position and appends to end of queue
    as 'waiting' to maintain fair rotation.
    """
    # Check if curselected
    if not list_queue.curselection():
        messagebox.showwarning("Warning","Please select a driver first")
        return
    
    # Get position of driver
    index = list_queue.curselection()[0]
    driver = shift_line[index]
    
    # Check if driver is dispatched
    if driver["status"] != "dispatched":
        messagebox.showwarning("Warning","Only dispatched drivers can complete rides")
        return
    
    # Remove driver from current position
    shift_line.pop(index)
    
    # Add driver back to the END of the queue as waiting (FIFO)
    shift_line.append({
        "body_num": driver["body_num"],
        "status": "waiting",
        "ride_type": None,
        "fare": None
    })
    
    # Update display
    update_queue_display()
    
    messagebox.showinfo("Success",f"Driver {driver['body_num']} Arrived and Returned to Queue")

# Remove a driver from the database
def delete_driver():
    """Delete selected driver from the driver database.
    
    Removes from dictionary and saves changes to CSV.
    """
    # Safety Check
    if not listbox_drivers.curselection():
        messagebox.showwarning("Warning","Please select a driver first")
        return
    
    # Get info
    selected_text = listbox_drivers.get(listbox_drivers.curselection()[0])

    # Split Dict key for csv deletion
    body_num = selected_text.split(" - ")[0]

    # Delete from dict
    del drivers_db[body_num]

    save_drivers()
    update_driver_listbox()

    messagebox.showinfo("Success","Driver deleted from database")
    return

# Look up and display a driver's profile
def search_driver_profile():
    """Find driver by body number and display profile with incidents.
    
    Shows driver name, standing, all incidents, and resolution status.
    Displays in scrollable text widget with color-coded status.
    """
    search_num = entry_search_num.get()
    
    if search_num in drivers_db:
        data = drivers_db[search_num]
        
        # Figure out what to show based on if they are cleared or not
        if data['resolved'] == "Yes":
            status_text = "[CLEARED]"
            text_color = "green"
        else:
            status_text = "[ACTIVE ISSUES]"
            text_color = "red"
            
        profile = f"Name: {data['name']}\nStanding: {data['standing']}\n\n--- Records {status_text} ---"
        
        # Display all incidents
        if data['incidents']:
            for idx, incident in enumerate(data['incidents'], 1):
                profile += f"\n\n#{idx}\nType: {incident['type']}\nDetails: {incident['desc']}"
        else:
            profile += "\nNo incidents on record."
        
        # Update text widget
        lbl_profile_result.config(state=tk.NORMAL)
        lbl_profile_result.delete("1.0", tk.END)
        lbl_profile_result.insert("1.0", profile)
        lbl_profile_result.tag_config("color", foreground=text_color)
        lbl_profile_result.tag_add("color", "1.0", tk.END)
        lbl_profile_result.config(state=tk.DISABLED)
    else:
        lbl_profile_result.config(state=tk.NORMAL)
        lbl_profile_result.delete("1.0", tk.END)
        lbl_profile_result.insert("1.0", "Driver not found.")
        lbl_profile_result.tag_config("color", foreground="red")
        lbl_profile_result.tag_add("color", "1.0", tk.END)
        lbl_profile_result.config(state=tk.DISABLED)

# Add a new incident or lost item to driver's record
def add_incident():
    """File a new complaint or lost item report for a driver.
    
    Appends to incidents list, marks standing as 'Review Needed',
    and marks resolved status as 'No'.
    """
    body_num = entry_search_num.get()
    inc_type = combo_incident_type.get()
    inc_desc = entry_incident_desc.get()
    
    # Safety checks
    if body_num not in drivers_db:
        messagebox.showerror("Error", "Search for a valid driver first.")
        return
    if inc_type == "" or inc_desc == "":
        messagebox.showerror("Error", "Please select a type and enter a description.")
        return
        
    # Append the new incident to the list (don't overwrite)
    drivers_db[body_num]["incidents"].append({"type": inc_type, "desc": inc_desc})
    drivers_db[body_num]["resolved"] = "No"
    drivers_db[body_num]["standing"] = "Review Needed" # Terminal knows they have an issue
    
    save_drivers()
    search_driver_profile() # Instantly refresh the screen
    entry_incident_desc.delete(0, tk.END)
    messagebox.showinfo("Logged", f"New issue added to Driver {body_num}'s profile.")

# Mark a specific incident as resolved
def resolve_incident():
    """Remove a specific incident from driver's record by issue number.
    
    If no incidents remain, marks driver as fully resolved and standing
    updated to 'Good'.
    """
    body_num = entry_search_num.get()
    issue_num_str = entry_issue_num_to_resolve.get()
    
    if body_num not in drivers_db:
        messagebox.showerror("Error", "Search for a valid driver first.")
        return
    
    # Check if they even have issues
    if not drivers_db[body_num]["incidents"]:
        messagebox.showinfo("Info", "This driver has no incidents to resolve.")
        return
    
    # Require a number to be entered
    if issue_num_str == "":
        messagebox.showerror("Error", "Please enter an issue number to resolve.")
        return
    
    # Try to resolve specific issue number
    try:
        issue_num = int(issue_num_str) - 1  # Convert to 0-based index
        if issue_num < 0 or issue_num >= len(drivers_db[body_num]["incidents"]):
            messagebox.showerror("Error", f"Issue #{issue_num + 1} not found.")
            return
        
        # Remove the specific incident
        removed_incident = drivers_db[body_num]["incidents"].pop(issue_num)
        
        # If no more incidents, mark as fully resolved
        if not drivers_db[body_num]["incidents"]:
            drivers_db[body_num]["resolved"] = "Yes"
            drivers_db[body_num]["standing"] = "Good"
        
        save_drivers()
        search_driver_profile()
        entry_issue_num_to_resolve.delete(0, tk.END)
        messagebox.showinfo("Resolved", f"Issue #{issue_num + 1} ({removed_incident['type']}) is removed!")
        
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid issue number.")

# Load trip history for a user-selected date
def load_history_for_date():
    """Fetch and display trip history for the date entered by user.
    
    Validates date format (YYYY-MM-DD) before querying.
    """
    try:
        date_str = history_date_var.get()
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        view_history_by_date(selected_date)
    except ValueError:
        messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format (e.g., 2026-04-20)")

root = tk.Tk()
root.title("B.A.R.K.E.R. - Tricycle Dispatch System")
root.geometry("1000x600") # Set a starting size for app
root.minsize(1000, 600)
root.state('zoomed')  # Start maximized on Windows

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
button_checkIn = tk.Button(frame_left, text="Check In", font=("Georgia", 11), bg="#2E7D32", fg="white", command=check_in_driver)
button_checkIn.pack(pady=15)

# Display Queue
list_queue = tk.Listbox(frame_left, bd = 1)
list_queue.pack(pady = 5 ,padx = 10, fill = "both", expand = True)

# Remove driver (Dashboard)
button_remove_driver = tk.Button(frame_left, text="Remove Driver from Line", font=("Georgia", 11), bg="#D32F2F", fg="white", command=remove_from_queue)
button_remove_driver.pack(pady = 10 ,padx = 10)

# Complete ride button
button_complete_ride = tk.Button(frame_left, text="Return to Queue", font=("Georgia", 11), bg="#2E7D32", fg="white", command=complete_ride)
button_complete_ride.pack(pady = 5 ,padx = 10)

#  Create a Right Frame for Stats/Logs
frame_right = tk.Frame(tab_dashboard, width=600, bd=2, relief="groove")
frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Dispatch Panel Label
lbl_dispatch = tk.Label(frame_right, text="Dispatch Panel", font=("Georgia", 24, "bold"))
lbl_dispatch.pack(pady = 10)

# The Variable to Track the Radio Buttons
# This tells Python to remember which button is clicked. It defaults to "Regular".
ride_type = tk.StringVar(value="Regular")

# Radio Buttons
radio_regular = tk.Radiobutton(frame_right, text="Regular (₱40 - 4 Pax)", variable=ride_type, value="Regular")
radio_regular.pack(anchor="w", padx=20, pady=5)

radio_special = tk.Radiobutton(frame_right, text="Special (Custom Fare)", variable=ride_type, value="Special")
radio_special.pack(anchor="w", padx=20, pady=5)

# Entry Box for Special Fare
lbl_special_fare = tk.Label(frame_right, text="If Special, enter amount (₱):")
lbl_special_fare.pack(pady=(15, 0))

entry_special_fare = tk.Entry(frame_right, bd=2)
entry_special_fare.pack(pady=5)

# Dispatch Button (We will add the command later!)
button_dispatch = tk.Button(frame_right, text="Dispatch Tricycle", bg="#2E7D32", fg="white", font=("Georgia", 11), command=dispatch_driver)
button_dispatch.pack(pady=20)

# Daily Total Button
button_daily_total = tk.Button(frame_right, text="Calculate Daily Total", bg="#1976D2", fg="white", font=("Georgia", 11), command=show_daily_total)
button_daily_total.pack(pady=10)

# History Label
lbl_history = tk.Label(frame_right, text="Live Trip History Log", font=("Georgia", 16, "bold"))
lbl_history.pack(pady=(15, 5))

# Date picker frame
frame_date_picker = tk.Frame(frame_right)
frame_date_picker.pack(pady=5)

lbl_history_date = tk.Label(frame_date_picker, text="Date (YYYY-MM-DD):")
lbl_history_date.pack(side=tk.LEFT, padx=5)

history_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
entry_history_date = tk.Entry(frame_date_picker, textvariable=history_date_var, width=12, justify="center")
entry_history_date.pack(side=tk.LEFT, padx=5)



button_load_history = tk.Button(frame_date_picker, text="Load", font=("Georgia", 11), bg="#1976D2", fg="white", command=load_history_for_date)
button_load_history.pack(side=tk.LEFT, padx=5)

# History Listbox (Made it wider so the text fits nicely)
listbox_history = tk.Listbox(frame_right, height=8, width=50, bd=2)
listbox_history.pack(pady=5)

# Refresh History Button
button_refresh_history = tk.Button(frame_right, text="Refresh Today's History", font=("Georgia", 11), bg="#1976D2", fg="white", command=view_history)
button_refresh_history.pack(pady=5)

# Total Fare Label
lbl_total_fare = tk.Label(frame_right)

# ADMIN REGISTRY - LEFT AND RIGHT FRAMES

# Create Left Frame for Driver Management
frame_admin_left = tk.Frame(tab_admin, width=400, bd=2, relief="groove")
frame_admin_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# LEFT FRAME: Add New Driver Section
lbl_add_driver = tk.Label(frame_admin_left, text="Add New Driver", font=("Georgia", 16, "bold"))
lbl_add_driver.pack(pady=10)

lbl_name = tk.Label(frame_admin_left, text="Driver Name:")
lbl_name.pack(pady=5)

entry_name = tk.Entry(frame_admin_left)
entry_name.pack(pady=5)

lbl_number = tk.Label(frame_admin_left, text="Body Number:")
lbl_number.pack(pady=5)

entry_admin_num = tk.Entry(frame_admin_left)
entry_admin_num.pack(pady=5)

button_save = tk.Button(frame_admin_left, text="Save", command=save_new_driver, bg="#1976D2", fg="white", font=("Georgia", 11))
button_save.pack(pady=10)

# Drivers List Label
lbl_drivers_list = tk.Label(frame_admin_left, text="Registered Drivers", font=("Georgia", 16, "bold"))
lbl_drivers_list.pack(pady=(15, 5))

# Display List of Drivers
listbox_drivers = tk.Listbox(frame_admin_left, bd=1)
listbox_drivers.pack(fill="both", expand=True, padx=10, pady=5)

# Delete Driver Button
button_delete_driver = tk.Button(frame_admin_left, text="Remove Driver from Database", bg="#D32F2F", fg="white", font=("Georgia", 11), command=delete_driver)
button_delete_driver.pack(pady=10, padx=10)

# Create Right Frame for Driver Profiles and Incidents
frame_admin_right = tk.Frame(tab_admin, width=600, bd=2, relief="groove")
frame_admin_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# RIGHT FRAME: Driver Profile Search Section
lbl_search_title = tk.Label(frame_admin_right, text="Look Up Driver Profile", font=("Georgia", 16, "bold"))
lbl_search_title.pack(pady=10)

entry_search_num = tk.Entry(frame_admin_right)
entry_search_num.pack(pady=5)

button_search = tk.Button(frame_admin_right, text="Search Body Number", font=("Georgia", 11), bg="#1976D2", fg="white", command=search_driver_profile)
button_search.pack(pady=5)

# Profile display with limited height and scrollbar
frame_profile_display = tk.Frame(frame_admin_right, height=150, bd=2, relief="sunken")
frame_profile_display.pack(pady=10, padx=5, fill="both", expand=False)
frame_profile_display.pack_propagate(False)

scrollbar_profile = tk.Scrollbar(frame_profile_display)
scrollbar_profile.pack(side=tk.RIGHT, fill=tk.Y)

lbl_profile_result = tk.Text(frame_profile_display, font=("Georgia", 10), height=8, width=35, yscrollcommand=scrollbar_profile.set, state=tk.DISABLED, wrap=tk.WORD)
lbl_profile_result.pack(side=tk.LEFT, fill="both", expand=True)
scrollbar_profile.config(command=lbl_profile_result.yview)

# Divider
ttk.Separator(frame_admin_right, orient='horizontal').pack(fill='x', pady=10)

# Incident Management Section
lbl_incident = tk.Label(frame_admin_right, text="File a Report or Lost Item", font=("Georgia", 16, "bold"))
lbl_incident.pack(pady=5)

combo_incident_type = ttk.Combobox(frame_admin_right, values=["Complaint / Report", "Lost Item"], state="readonly")
combo_incident_type.set("Lost Item")
combo_incident_type.pack(pady=5)

lbl_desc = tk.Label(frame_admin_right, text="Explain the issue/item:")
lbl_desc.pack()

entry_incident_desc = tk.Entry(frame_admin_right, width=40)
entry_incident_desc.pack(pady=5)

button_add_incident = tk.Button(frame_admin_right, text="Submit Active Issue", bg="#F57C00", fg="white", font=("Georgia", 11), command=add_incident)
button_add_incident.pack(pady=5)

# Resolve Specific Issue Section
lbl_resolve_issue = tk.Label(frame_admin_right, text="Resolve Specific Issue (enter #):", font=("Georgia", 11))
lbl_resolve_issue.pack(pady=(10, 5))

entry_issue_num_to_resolve = tk.Entry(frame_admin_right, width=10)
entry_issue_num_to_resolve.pack(pady=5)

button_resolve = tk.Button(frame_admin_right, text="Mark as Resolved", bg="#2E7D32", fg="white", font=("Georgia", 11), command=resolve_incident)
button_resolve.pack(pady=5)



load_drivers()
update_driver_listbox()
update_queue_display()
root.mainloop()