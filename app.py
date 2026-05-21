import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from db_manager import *
from datetime import date
import time 

# --- OOP CLASS DEFINITIONS ---
# --- OOP CLASS DEFINITIONS ---
class User:
    def __init__(self, id, name, email, phone, role):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.role = role

# --- STREAMLIT UI SETUP ---
# st.set_page_config(page_title="SkyLine System", layout="wide")
st.set_page_config(page_title="SkyLine SQL System", page_icon="✈️", layout="wide")

# INITIALIZE SEARCH HISTORY STACK (Module 5.1)
if 'search_stack' not in st.session_state:
    st.session_state['search_stack'] = [("", "")] # Empty Source/Dest to start

if 'user' not in st.session_state:
    st.session_state['user'] = None

if 'src_val' not in st.session_state:
    st.session_state.src_val = ""

if 'dest_val' not in st.session_state:
    st.session_state.dest_val = ""

# --- SIDEBAR (AUTHENTICATION) ---
st.sidebar.title("✈️ SkyLine System")

if st.session_state['user']:
    # LOGOUT LOGIC
    st.sidebar.success(f"User: {st.session_state['user'].name}")
    if st.sidebar.button("Logout", type="primary"):
        st.session_state['user'] = None
        time.sleep(1)
        st.rerun()
else:
    # LOGIN / REGISTER TABS
    choice = st.sidebar.radio("Menu", ["Login", "Register"])
    
    if choice == "Login":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user_data = login_user(email, password)
            
            if user_data:
                # FIX: Ensure we pass all 5 arguments in the correct order
                # 1. id, 2. name, 3. email, 4. phone, 5. role
                current_user = User(
                    user_data['id'], 
                    user_data['name'], 
                    user_data['email'], 
                    user_data.get('phone'),  # Use .get() to avoid errors if phone is missing
                    user_data['role']
                )
                
                st.session_state['user'] = current_user
                st.rerun()
            else:
                st.sidebar.error("Invalid Email or Password")

    elif choice == "Register":
        st.sidebar.subheader("Create New Account")
        name = st.sidebar.text_input("Full Name")
        new_email = st.sidebar.text_input("Email Address")
        phone = st.sidebar.text_input("Phone Number", max_chars=10) # Added Phone
        new_pass = st.sidebar.text_input("Create Password", type="password")
        
        if st.sidebar.button("Register Now", type="primary"):
            if name and new_email and phone and new_pass:
                # Call updated register function with phone
                if register_user(name, new_email, new_pass, phone):
                    st.sidebar.success("Account Created! Please Login.")
                else:
                    st.sidebar.error("Email already exists.")
            else:
                st.sidebar.warning("Please fill all fields.")
# ================= MAIN DASHBOARD =================

if st.session_state['user']:
    user = st.session_state['user']

    # --- ADMIN VIEW (UPDATED WITH DELETE FEATURE) ---
    # ================= ADMIN VIEW =================
    if user.role == 'admin':
        st.title("👨‍💻 System Administrator")
        
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard & Bookings", "✈️ Manage Flights", "📈 Analytics"])

        # TAB 1: DASHBOARD & GLOBAL BOOKINGS
        with tab1:
            st.subheader("System Overview")
            
            # Fetch Stats from Database
            flight_count, todays_bookings = get_admin_dashboard_stats()
            
            # Display Beautiful Metric Cards
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Total Active Flights", value=flight_count, delta="Available", delta_color="normal")
            col2.metric(label="Today's Bookings", value=todays_bookings, delta="New", delta_color="normal")
            
            st.divider()
            
            # Display All Bookings Across System
            st.subheader("📋 All Global Bookings")
            all_bookings = get_all_bookings_admin()
            
            if all_bookings:
                for b in all_bookings:
                    with st.container():
                        c1, c2 = st.columns([4, 1])
                        
                        # Passenger & Flight Details
                        c1.markdown(f"**👤 Passenger:** {b['passenger_name']} ({b['email']}) ")
                        c1.markdown(f"**✈️ Flight:** {b['flight_no']} | {b['source']} ➝ {b['destination']}")
                        c1.caption(f"📅 Booked on: {b['booking_date']} | Class: {b['class_type']} | Seats: {b['seats']}")
                        
                        # Status Badge
                        if b['status'] == 'CONFIRMED':
                            c2.success("CONFIRMED")
                        else:
                            c2.error("CANCELLED")
                        st.divider()
            else:
                st.info("No bookings have been made yet.")

        # ... inside Admin View ...
        
        # TAB 2: MANAGE FLIGHTS
        # TAB 2: MANAGE FLIGHTS
        # TAB 2: MANAGE FLIGHTS
        with tab2:
            st.header("Manage Flights")
            
            # ==========================================
            # ➕ SECTION 1: ADD NEW FLIGHT
            # ==========================================
            st.subheader("➕ Add New Flight")
            
            with st.form("add_flight_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                new_flight_no = c1.text_input("Flight Number (e.g. AI-202)")
                new_source = c2.text_input("Source City")
                new_dest = c3.text_input("Destination City")
                
                c4, c5 = st.columns(2)
                new_dept = c4.time_input("Departure Time")
                new_arr = c5.time_input("Arrival Time")
                
                c6, c7, c8, c9 = st.columns(4)
                new_eco_price = c6.number_input("Economy Price (₹)", min_value=1000.0, step=500.0)
                new_eco_seats = c7.number_input("Economy Seats", min_value=10, step=10, value=150)
                new_bus_price = c8.number_input("Business Price (₹)", min_value=2000.0, step=1000.0)
                new_bus_seats = c9.number_input("Business Seats", min_value=5, step=5, value=20)
                
                submit_flight = st.form_submit_button("Add Flight to System", type="primary")
                
                if submit_flight:
                    if not new_flight_no or not new_source or not new_dest:
                        st.error("⚠️ Please fill in the Flight Number, Source, and Destination.")
                    else:
                        if add_flight_to_db(new_flight_no, new_source, new_dest, new_dept, new_arr, 
                                            new_eco_price, new_eco_seats, new_bus_price, new_bus_seats):
                            st.success(f"✅ Flight {new_flight_no} successfully added!")
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Failed to add flight.")

            st.divider()

            # ==========================================
            # 🗑️ SECTION 2: DELETE EXISTING FLIGHT
            # ==========================================
            st.subheader("🗑️ Delete Flight")
            
            flights = get_all_flights() # Fetch all current flights
            
            if flights:
                # Format the list so it looks good in the dropdown box
                flight_options = [f"{f['id']} - {f['flight_no']} ({f['source']} -> {f['destination']})" for f in flights]
                
                selected_flight = st.selectbox("Select Flight to Delete", flight_options)
                
                if st.button("Delete Selected Flight", type="primary"):
                    try:
                        # Extract just the ID number from the dropdown string
                        flight_id = int(selected_flight.split(' - ')[0])
                        
                        if delete_flight_from_db(flight_id):
                            st.success("filght is delete successfully") # Your custom message!
                            import time
                            time.sleep(2) # Pauses so you can read the message
                            st.rerun()
                        else:
                            st.error("Error deleting flight.")
                            
                    except ValueError:
                        st.error("Invalid selection")
            else:
                st.info("No flights available to delete.")

                
        with tab3:
            st.subheader("Flight Price Analysis")
            flights = get_all_flights()
            if flights:
                # Concept 5.1: List Comprehensions
                names = [f['flight_no'] for f in flights]
                prices = [float(f['eco_price']) for f in flights]
                
                # Concept 9.3: Using NumPy to create numeric spacing
                # This gives each bar a fixed numerical coordinate
                x_indexes = np.arange(len(names))
                
                # Concept 10.1: Increase width to 20 or more for 100+ flights
                # A wider figsize forces the X-axis to stretch out
                fig, ax = plt.subplots(figsize=(22, 8)) 
                
                # Concept 10.1: Set width to 0.4 to create visible gaps between 'candles'
                ax.bar(x_indexes, prices, color='#ff4b4b', width=0.4)
                
                # THE FIX: Combining rotation, alignment, and smaller font
                plt.xticks(
                    ticks=x_indexes, 
                    labels=names, 
                    rotation=90,      # Vertical rotation saves the most horizontal space
                    ha='center',      # Center alignment works best with 90-degree rotation
                    fontsize=6        # Smallest legible font size for high density
                )
                
                # Concept 10.1: Adding Grids for clarity
                ax.grid(axis='y', linestyle='--', alpha=0.3)
                ax.set_ylabel("Ticket Price (₹)")
                ax.set_xlabel("Flight Number")
                
                # Concept 10.2: Displaying the stretched chart
                st.pyplot(fig)


    # --- USER VIEW ---
    else:
        st.title(f"Welcome, {user.name} 👋")
        
        # Tabs for Search vs History
        tab_book, tab_history = st.tabs(["✈️ Book Flight", "📜 My Bookings"])

        # TAB 1: BOOKING
        with tab_book:
            # --- STACK IMPLEMENTATION: Initialize History Stack ---
            # Get the top of the stack (Module 5.1)
            current_history = st.session_state['search_stack'][-1]

            c1, c2, c3 = st.columns(3)
            # Use 'value' from stack history
            src = c1.text_input("Source City", value=current_history[0])
            dest = c2.text_input("Destination City", value=current_history[1])
            travel_date = c3.date_input("Travel Date", min_value=date.today())

            col_search, col_back = st.columns([1, 5])

            # FIND FLIGHTS (Push to Stack)
            if col_search.button("Find Flights"):
                if src or dest:
                    st.session_state['search_stack'].append((src, dest)) # Module 5.1: Append
                    st.session_state['flights_found'] = search_flights_db(src, dest)
                    st.rerun()

            # UNDO SEARCH (Pop from Stack)
            if len(st.session_state['search_stack']) > 1:
                if col_back.button("⬅ Undo Search"):
                    st.session_state['search_stack'].pop() # Module 5.1: Pop
                    
                    # Peek at previous and re-fetch flights
                    new_top = st.session_state['search_stack'][-1]
                    st.session_state['flights_found'] = search_flights_db(new_top[0], new_top[1])
                    st.rerun()

            # --- DISPLAY RESULTS ---
            if 'flights_found' in st.session_state and st.session_state['flights_found']:
                flights = st.session_state['flights_found']
                st.success(f"Found {len(flights)} flights")
                
                # for f in flights:
                #     with st.expander(f"{f['flight_no']} | {f['dept_time']} - {f['arr_time']}"):
                        
                #         # 1. Class Selection
                #         seat_type = st.radio("Select Class", ["Economy", "Business"], key=f"class_{f['id']}", horizontal=True)

                #         # ---------------------------------------------------------
                #         # 💳 NEW: PAYMENT METHOD SELECTION (Add this here)
                #         # ---------------------------------------------------------
                #         pay_method = st.radio("Select Payment Method", ["Credit Card", "UPI"], key=f"pay_{f['id']}", horizontal=True)
                        
                #         # 2. Base Price Logic
                #         if seat_type == "Economy":
                #             base_price = float(f['eco_price'])
                #             available = f['eco_avail']
                #         else:
                #             base_price = float(f['bus_price'])
                #             available = f['bus_avail']

                #         # Seasonal Pricing Logic
                #         if travel_date.month in [5, 6]:
                #             final_price = base_price * 1.20
                #             surge_msg = " (⚠️ Peak Season +20%)"
                #         else:
                #             final_price = base_price
                #             surge_msg = ""

                #         # 3. Display Updated Price
                #         st.markdown(f"**Price:** ₹{final_price:,.2f}{surge_msg} | **Available:** {available} seats")
                        
                #         # 4. Input for Passengers
                #         seats_req = st.number_input("Passengers", 1, 10, 1, key=f"qty_{f['id']}")

                #         # ... (Previous code: Passengers & Total Cost calculation) ...
                #         seats_req = st.number_input("Passengers", 1, 10, 1, key=f"qty_{f['id']}")
                #         total_cost = final_price * seats_req
                #         st.caption(f"Total to Pay: ₹{total_cost:,.2f}")

                #         # ---------------------------------------------------------
                #         # 💳 NEW: PAYMENT GATEWAY UI
                #         # ---------------------------------------------------------
                #         st.divider()
                #         payment_method = st.radio("Select Payment Method", ["Credit Card", "UPI"], key=f"pay_{f['id']}", horizontal=True)
                        
                #         # Variable to track if they entered the right details
                #         payment_valid = False 
                        
                #         if payment_method == "Credit Card":
                #             # max_chars=16 stops them from typing more than 16 characters
                #             card_no = st.text_input("Enter 16-Digit Card Number", max_chars=16, placeholder="1234567812345678", key=f"cc_{f['id']}")
                            
                #             # Check if it is exactly 16 digits AND only numbers
                #             if len(card_no) == 16 and card_no.isdigit():
                #                 payment_valid = True
                                
                #         elif payment_method == "UPI":
                #             # max_chars=10 stops them from typing more than 10 characters
                #             upi_no = st.text_input("Enter 10-Digit UPI Number", max_chars=10, placeholder="9876543210", key=f"upi_{f['id']}")
                            
                #             # Check if it is exactly 10 digits AND only numbers
                #             if len(upi_no) == 10 and upi_no.isdigit():
                #                 payment_valid = True
                #         # ---------------------------------------------------------

                #         # 6. BOOKING BUTTON (Now checks payment first)
                #         if st.button(f"Pay ₹{total_cost:,.2f} & Book {seat_type}", key=f"btn_{f['id']}", type="primary"):
                            
                #             # ❌ Step A: Check if Payment info is missing/wrong
                #             if not payment_valid:
                #                 st.error(f"⚠️ Please enter a valid {payment_method} number before booking.")
                                
                #             # ✅ Step B: Check Seats & Book Ticket
                #             elif seats_req <= available:
                #                 if create_booking(user.id, f['id'], seats_req, seat_type):
                #                     st.balloons()
                #                     st.success("your flight ticket is book successfully ! thank you")
                                    
                #                     # Pause to let the user read the success message
                #                     import time
                #                     time.sleep(2) 
                                    
                #                     st.session_state['search_results'] = None
                #                     st.rerun()
                #             else:
                #                 st.error(f"Not enough seats in {seat_type} class.")
                for index, f in enumerate(flights):
                    
                    with st.expander(f"{f['flight_no']} | {f['dept_time']} - {f['arr_time']}"):
                        
                        # 1. Class Selection
                        seat_type = st.radio("Select Class", ["Economy", "Business"], key=f"class_{f['id']}_{index}", horizontal=True)
                        
                        # 2. Base Price & Availability
                        if seat_type == "Economy":
                            base_price = float(f['eco_price'])
                            available = f['eco_avail']
                        else:
                            base_price = float(f['bus_price'])
                            available = f['bus_avail']

                        # 3. Peak Season Logic (May & June)
                        if travel_date.month in [5, 6]:
                            final_price = base_price * 1.20
                            surge_msg = " (⚠️ Peak Season +20%)"
                        else:
                            final_price = base_price
                            surge_msg = ""

                        st.markdown(f"**Price:** ₹{final_price:,.2f}{surge_msg} | **Available:** {available} seats")
                        
                        # 4. Passengers Input
                        seats_req = st.number_input("Passengers", 1, 10, 1, key=f"qty_{f['id']}_{index}")
                        
                        total_cost = final_price * seats_req
                        st.caption(f"Total to Pay: ₹{total_cost:,.2f}")

                        # 5. Payment Gateway
                        st.divider()
                        payment_method = st.radio("Select Payment Method", ["Credit Card", "UPI"], key=f"pay_{f['id']}_{index}", horizontal=True)
                        payment_valid = False 
                        
                        if payment_method == "Credit Card":
                            card_no = st.text_input("Enter 16-Digit Card Number", max_chars=16, placeholder="1234567812345678", key=f"cc_{f['id']}_{index}")
                            if len(card_no) == 16 and card_no.isdigit():
                                payment_valid = True
                        elif payment_method == "UPI":
                            upi_no = st.text_input("Enter 10-Digit UPI Number", max_chars=10, placeholder="9876543210", key=f"upi_{f['id']}_{index}")
                            if len(upi_no) == 10 and upi_no.isdigit():
                                payment_valid = True

                        # 6. Book Button
                        if st.button(f"Pay ₹{total_cost:,.2f} & Book {seat_type}", key=f"btn_{f['id']}_{index}", type="primary"):
                            
                            if not payment_valid:
                                st.error(f"⚠️ Please enter a valid {payment_method} number before booking.")
                            elif seats_req <= available:
                                if create_booking(user.id, f['id'], seats_req, seat_type, payment_method):
                                    st.success("your flight ticket is book successfully ! thank you")
                                    
                                    import time
                                    time.sleep(2) 
                                    
                                    st.session_state['flights_found'] = None 
                                    st.rerun()
                            else:
                                st.error(f"Not enough seats in {seat_type} class.")



                        
                        # # 5. Calculate Total
                        # total_cost = final_price * seats_req
                        # st.caption(f"Total to Pay: ₹{total_cost:,.2f}")

                        # # 6. Booking Button Logic
                        # # Update the button text to show the payment method
                        # if st.button(f"Confirm & Book via {pay_method}", key=f"btn_{f['id']}"):
                        #     if seats_req <= available:
                        #         # IMPORTANT: Added 'pay_method' to the arguments below
                        #         if create_booking(user.id, f['id'], seats_req, seat_type, pay_method): 
                        #             st.success(f"Ticket booked successfully via {pay_method}! Thank you.")
                        #             time.sleep(1)
                        #             st.rerun()
                        #     else:
                        #         st.error(f"Not enough seats in {seat_type} class.")
            elif 'flights_found' in st.session_state:
                st.warning("No flights found.")
        # TAB 2: BOOKING HISTORY
        with tab_history:
            st.subheader("My Bookings")
            my_bookings = get_user_bookings(user.id)
            
            if my_bookings:
                for b in my_bookings:
                    with st.container():
                        # Logic to find which price to use
                        if b.get('class_type') == 'Business':
                            ticket_cost = b['bus_price']
                        else:
                            ticket_cost = b['eco_price']
                            
                        # Calculate Total
                        total = float(ticket_cost) * b['seats']

                        # Display
                        st.markdown(f"**{b['flight_no']}** | {b['source']} ➝ {b['destination']}")
                        st.caption(f"Date: {b['booking_date']} | Class: {b.get('class_type', 'Economy')}")
                        st.write(f"**Seats:** {b['seats']} | **Total Cost:** ₹{total:,.2f} | **Status:** {b['status']}")
                        
                        # Cancel Button
                        if b['status'] == 'CONFIRMED':
                            if st.button("Cancel Booking", key=f"cncl_{b['id']}"):
                                if cancel_booking_db(b['id']):
                                    st.warning("Booking Cancelled.")
                                    st.rerun()
                        st.divider()
            else:
                st.info("No booking history found.")
else:
    # Landing Page
    st.title("SkyLine Booking System ✈️")
    st.image("https://images.unsplash.com/photo-1436491865332-7a61a109cc05", use_container_width=True)
    st.info("Please login from the sidebar to access the system.")