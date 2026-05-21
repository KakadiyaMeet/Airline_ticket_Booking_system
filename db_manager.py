import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Default XAMPP password is empty
        database="airline1_db",
        port=3307
    )

# --- USER FUNCTIONS ---
def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(name, email, password, phone):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return False
            
        cursor.execute("INSERT INTO users (name, email, password, phone, role) VALUES (%s, %s, %s, %s, 'user')", 
                       (name, email, password, phone))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# --- FLIGHT FUNCTIONS ---



def get_all_flights():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM flights")
    data = cursor.fetchall()
    conn.close()
    return data

def search_flights_db(source, dest):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT * FROM flights 
        WHERE source=%s AND destination=%s 
        AND (eco_avail > 0 OR bus_avail > 0)
    """
    cursor.execute(query, (source, dest))
    data = cursor.fetchall()
    conn.close()
    return data

# --- ADMIN: ADD FLIGHT ---
def add_flight_to_db(flight_no, source, dest, dept_time, arr_time, eco_price, eco_seats, bus_price, bus_seats):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO flights 
            (flight_no, source, destination, dept_time, arr_time, 
             eco_price, eco_seats, eco_avail, 
             bus_price, bus_seats, bus_avail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Note: We pass eco_seats and bus_seats TWICE because a new flight starts with all seats available
        values = (flight_no, source, dest, dept_time, arr_time, 
                  eco_price, eco_seats, eco_seats, 
                  bus_price, bus_seats, bus_seats)
                  
        cursor.execute(query, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding flight: {e}")
        return False
    finally:
        conn.close()


# --- ADMIN: DELETE FLIGHT ---
def delete_flight_from_db(flight_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM flights WHERE id = %s", (flight_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting flight: {e}")
        return False
    finally:
        conn.close()

# --- BOOKING FUNCTIONS ---
# Concept 3.2: Function arguments (Accepts 5 positional arguments)

# ✅ Function now accepts 'payment_method'
def create_booking(user_id, flight_id, seats, class_type, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # ✅ Check seats availability again (Safety Check)
        if class_type == 'Economy':
            cursor.execute("SELECT eco_avail, eco_seats FROM flights WHERE id = %s", (flight_id,))
            res = cursor.fetchone()
            available = res[0]
            if available < seats: return False
            
            # Update Flight Seats
            new_avail = available - seats
            cursor.execute("UPDATE flights SET eco_avail = %s WHERE id = %s", (new_avail, flight_id))
            
        else: # Business Class
            cursor.execute("SELECT bus_avail, bus_seats FROM flights WHERE id = %s", (flight_id,))
            res = cursor.fetchone()
            available = res[0]
            if available < seats: return False
            
            # Update Flight Seats
            new_avail = available - seats
            cursor.execute("UPDATE flights SET bus_avail = %s WHERE id = %s", (new_avail, flight_id))

        # ✅ INSERT the booking with the Payment Method
        query = """
            INSERT INTO bookings (user_id, flight_id, seats, class_type, status, booking_date, payment_method) 
            VALUES (%s, %s, %s, %s, 'CONFIRMED', NOW(), %s)
        """
        cursor.execute(query, (user_id, flight_id, seats, class_type, payment_method))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error creating booking: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_user_bookings(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT b.id, b.booking_date, b.seats, b.status, b.class_type, b.payment_method,
               f.flight_no, f.source, f.destination, f.dept_time, 
               f.eco_price, f.bus_price 
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """
    cursor.execute(query, (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def cancel_booking_db(booking_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT flight_id, seats, status, class_type FROM bookings WHERE id=%s", (booking_id,))
        booking = cursor.fetchone() 
        
        if booking and booking[2] == 'CONFIRMED':
            flight_id, seats_to_return, _, class_type = booking
            seat_col = 'bus_avail' if class_type == 'Business' else 'eco_avail'

            cursor.execute(f"UPDATE flights SET {seat_col} = {seat_col} + %s WHERE id=%s", (seats_to_return, flight_id))
            cursor.execute("UPDATE bookings SET status='CANCELLED' WHERE id=%s", (booking_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error canceling: {e}")
        return False
    finally:
        conn.close()

# --- ADMIN DASHBOARD FUNCTIONS ---
def get_admin_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as flight_count FROM flights")
    flight_count = cursor.fetchone()['flight_count']
    cursor.execute("SELECT COUNT(*) as todays_bookings FROM bookings WHERE DATE(booking_date) = CURDATE()")
    todays_bookings = cursor.fetchone()['todays_bookings']
    conn.close()
    return flight_count, todays_bookings

def get_all_bookings_admin():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT b.id, b.seats, b.class_type, b.status, b.booking_date, b.payment_method,
               u.name as passenger_name, u.email, u.phone,
               f.flight_no, f.source, f.destination
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN flights f ON b.flight_id = f.id
        ORDER BY b.booking_date DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data