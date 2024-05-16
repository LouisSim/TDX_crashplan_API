# This is a sample Python script.
import requests
import tkinter as tk
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

ASSET_SEARCH_URL = 'https://gw-test.api.it.umich.edu/um/it/32/assets/search'
TICKET_CREATE_URL = 'https://gw-test.api.it.umich.edu/um/it/31/tickets'
USER_FETCH_URL = 'https://gw-test.api.it.umich.edu/um/it/people/'
TICKET_COMMENT_URL = 'https://gw-test.api.it.umich.edu/um/it/31/tickets/'


class MessageInfo:
    """Store the message information. it is a class in case it needs to expand later with description, location, ect"""
    message_type = ""
    user_name = ""
    text = ""

    def __init__(self, message_type, user_name):
        self.message_type = message_type
        self.user_name = user_name

    def __str__(self):
        return f"Type: {self.message_type}, Name: {self.user_name}"


def make_crashplan_sync_message(client_first_name, miws_number, user_fullname):
    """Create the message for a crashplan sync"""
    return (f"Hi {client_first_name},\n\n\t I am {user_fullname} with Neighborhood IT. From our records it seems that "
            "Crashplan, our data security application, has not fully backed"
            f" up your device (service tag {miws_number}). In order to resolve this, please just click on the crashplan"
            f" folder icon on the top right for mac, or under the carrot in the bottom right on Windows. If you cannot "
            f"find it, please search for crashplan on your device and open the application. After opening, your device"
            f" should continue to update.\n\n\tIf you have any questions or concerns, any errors pop up, or would like "
            f"to meet for assistance, please respond to this email.\n\nThank you,\n{user_fullname}")


def make_crashplan_setup_message(client_first_name, miws_number, user_fullname):
    """Create the message for a crashplan creation"""

    #  TODO: update to match email better
    message_setup = (
        f"Hi {client_first_name},\n\n"
        f"I am {user_fullname} with Neighborhood IT. Your device "
        f"(service tag {miws_number}) is not backed up with Crashplan. "
        f"Please follow the steps outlined here: "
        f"https://documentation.its.umich.edu/node/1687 in order to set up Crashplan "
        f"on your device. Crashplan is our data recovery device that allows us to back "
        f"up your data in case of a hardware or software failure.\n\n"
        f"If you have any issues or questions please let me know by responding to this "
        f"email. The same is true if you would like to set up a meeting to get more "
        f"information or help setting up Crashplan.\n\n"
        f"Thank you,\n{user_fullname}"
    )
    return message_setup


def get_device_info(input_list):
    """Query the Api in order to get relevant device information"""
    device_data = []
    for serial_number in input_list:
        payload = {'SerialNumber': serial_number}
        headers = {'Authorization': 'Bearer XXX', 'Content-Type': 'application/json'}
        search_response = []
        try:
            search_response_raw = requests.post(ASSET_SEARCH_URL, json=payload, headers=headers)
            search_response_raw.raise_for_status()
            search_response = search_response_raw.json()
            # TODO:these except statements most likely need to be changed, just did some basics
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            error_out()
        except requests.exceptions.RequestException as req_err:
            print(f'Request error occurred: {req_err}')
            error_out()
        except Exception as err:
            print(f'An error occurred: {err}')
            error_out()
        finally:
            if not search_response:
                print("Error with finding device: ", serial_number)
                error_out()
            if search_response.len() > 1:
                # more than one asset record returned
                error_out()
            else:
                device = {"assetID": search_response[0]["ID"], "serial": serial_number,
                          "ownerUID": search_response[0]["OwningCustomerUID"], "miws_tag": search_response[0]["tag"],
                          "locationID": search_response[0]["LocationID"],
                          "location": search_response[0]["LocationName"], "status": search_response[0]["StatusName"]}
                if (not device["ownerUID"]) or (not device["miws_tag"]):
                    print("This device has incomplete information: ", device)
                    continue
                if device["location"] == "Stockroom" or "In Stock" in device["status"]:
                    print("This device is currently in NIT possession: ", device)
                    continue
                device_data.append(device)
        return device_data


def add_user_data(devices):
    """Get user data based off of the device data. """

    for device in devices:
        user_response = {}
        try:
            headers = {'Authorization': 'Bearer XXX', 'Content-Type': 'application/json'}
            user_response_raw = requests.get(USER_FETCH_URL + device["ownerUID"],
                                             headers=headers)  # Use owner UID in order to get owner information
            user_response_raw.raise_for_status()
            user_response = user_response_raw.json()  # TODO: need to test at how this will output
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            error_out()
        except requests.exceptions.RequestException as req_err:
            print(f'Request error occurred: {req_err}')
            error_out()
        except Exception as err:
            print(f'An error occurred: {err}')
            error_out()
        finally:
            #  update the device data structure with the user information. User is a separate dictionary
            device["user"] = {"first_name": user_response["FirstName"], "last_name": user_response["LastName"],
                              "email": user_response["UserName"]}


def create_tickets(devices):
    """Create the tickets for each device"""

    """
    devices = [{assetID, serial, ownerUID, miws_tag, locationID, 
    location, status, user: {first_name, last_name, email}}][...]"""
    ticket_ids = []
    for device in devices:
        ticket_response = {}
        payload = {'TypeID': 63, 'Classification': '46', 'ServiceID': 125,
                   'Title': f'Crashplan issue for user {device['user']['email'][:-10]} on device {device['miws_tag']}',
                   'StatusID': 77, 'SourceID': 8, 'RequesterEmail': {device['user']['email']}, 'ResponsibleGroupID': 32,
                   # TODO:  32 should be central-5, may need to update input later to change this
                   'LocationID': device['locationID']}  # TODO: Good for now, might want to add description values later
        headers = {'Authorization': 'Bearer XXX', 'Content-Type': 'application/json'}
        try:
            ticket_response_raw = requests.post(TICKET_CREATE_URL, json=payload, headers=headers)
            ticket_response_raw.raise_for_status()
            ticket_response = ticket_response_raw.json()
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            error_out()
        except requests.exceptions.RequestException as req_err:
            print(f'Request error occurred: {req_err}')
            error_out()
        except Exception as err:
            print(f'An error occurred: {err}')
            error_out()
        ticket_ids.append(ticket_response['ID'])
    return ticket_ids


def send_message(ticket_ids, devices, message_info):
    """Send message to users through the ticket"""
    # Iterate through ticket id. The ticket id should be the same index as corresponding device
    for i in range(len(ticket_ids)):
        device = devices[i]
        comment = ""
        if message_info.message_type == "create":
            comment = make_crashplan_setup_message(device["user"]["first_name"], device["miws_tag"],
                                                   message_info.user_name)
        elif message_info.message_type == "sync":
            comment = make_crashplan_sync_message(device["user"]["first_name"], device["miws_tag"],
                                                  message_info.user_name)
        elif message_info.message_type == "custom":
            print("not ready yet")
            #  TODO: DEAL WITH CUSTOM MESSAGE LATER
        else:
            error_out()
        payload = {"Comments": comment,  # temp value
                   "Notify": [device['user']['email']], "IsPrivate": False, "IsRichHtml": False}
        # TODO: Html may need to be rich, look at later
        headers = {'Authorization': 'Bearer XXX', 'Content-Type': 'application/json'}
        try:
            ticket_response_raw = requests.post(TICKET_COMMENT_URL + str(ticket_ids[i]) + "/feed",
                                                json=payload, headers=headers)
            ticket_response_raw.raise_for_status()
            #  ticket_response = ticket_response_raw.json()
            #  Should not need this response, here if needed
        except requests.exceptions.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            error_out()
        except requests.exceptions.RequestException as req_err:
            print(f'Request error occurred: {req_err}')
            error_out()
        except Exception as err:
            print(f'An error occurred: {err}')
            error_out()


def error_out():  # TODO: UPDATE FOR LATER USE IN ORDER TO PROIDE FEEDBACK TO USER
    """Send error message and exit(1). Update for future use"""
    print("An error occurred")
    exit(1)


def submit_text():
    """Submit all the collected data to the API executor"""
    serial_numbers = t1.get("1.0", tk.END).strip()
    m.destroy()
    message_info = MessageInfo(message.get(), name.get())
    print(message_info)
    serial_list = serial_numbers.split()
    for number in serial_list:
        number = number.strip()
    print(serial_list)
    api_execute(serial_list, message_info)


def api_execute(input_list, message_info):  # List of serial numbers
    """Execute the API functions in order"""
    device_data = get_device_info(input_list)
    add_user_data(device_data)
    tickets = create_tickets(device_data)
    send_message(tickets, device_data, message_info)


def update_message():
    """Update the example message and name based on the inputs"""
    selected_option = message.get()
    name_var = name.get()
    if selected_option == "create":
        text_box.pack_forget()
        message_label.config(text="Message that will be printed:\n\n\n" + make_crashplan_setup_message("Device Owner", "MIWSXXXXX", name_var))
    elif selected_option == "sync":
        text_box.pack_forget()
        message_label.config(text="Message that will be printed\n\n\n" + make_crashplan_sync_message("Device Owner", "MIWSXXXXX", name_var))
    elif selected_option == "custom":
        message_label.config(text="Please input custom message ******NOT YET FUNCTIONAL******")
        text_box.pack(expand=True, fill='both', pady=10)
    else:
        message_label.config(text="Please select an option.")
        text_box.pack_forget()
        submit_button.config(state=tk.DISABLED)


class WrappingLabel(tk.Label):
    """a type of Label that automatically adjusts the wrap to the size"""
    def __init__(self, master=None, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        self.bind('<Configure>', lambda e: self.config(wraplength=self.winfo_width()))


def enable_submit():
    """Sets the submit button to active if a radiobutton is enabled"""
    if message.get():  # If any radiobutton is selected
        submit_button.config(state=tk.NORMAL)  # Enable the Submit button
    else:
        submit_button.config(state=tk.DISABLED)  # Disable the Submit button if no option is selected


if __name__ == '__main__':
    # Set up UI
    m = tk.Tk()
    m.geometry("600x700")

    # initialize needed variables
    message = tk.StringVar()
    name = tk.StringVar(value="Your Name")
    tk.Label(m, text="Input Serial numbers, one on each line (Maximum of 10)", font=('calibre', 12)).pack()
    #  create text box
    t1 = tk.Text(m, width=50, height=10)
    t1.pack(padx=20, pady=10)
    #  create options for message prompts
    r1 = tk.Radiobutton(m, text='Crashplan Create', variable=message, value='create', command=lambda: [update_message(), enable_submit()])
    r2 = tk.Radiobutton(m, text='Crashplan Sync', variable=message, value='sync',  command=lambda: [update_message(), enable_submit()])
    r3 = tk.Radiobutton(m, text='Custom', variable=message, value='custom', command=lambda: [update_message(), enable_submit()])
    r1.pack(anchor='w'), r2.pack(anchor='w'), r3.pack(anchor='w')
    #  get name of IT user
    tk.Label(m, text="Input your full name", font=('calibre', 12)).pack()
    e1 = tk.Entry(m, textvariable=name)
    e1.pack()
    #  Create Submit button
    submit_button = tk.Button(m, text="Submit", command=submit_text, width=30, bg="darkgrey", state=tk.DISABLED)
    submit_button.pack(padx=20, pady=10)

    #  Show preview of message that will be sent
    message_label = WrappingLabel(m, text="Please select an option.")
    message_label.pack(expand=True, fill=tk.X, padx=10)
    text_box = tk.Text(m, height=5, width=40)

    m.mainloop()

