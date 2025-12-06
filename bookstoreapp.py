import streamlit as st
import sqlite3
import pandas as pd
import time

# --- CUSTOM DESIGN & STYLING ---
# Setting Streamlit page config and custom CSS for a cleaner look
st.set_page_config(
    page_title="Simple Bookstore App", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS for main title and general look
st.markdown(
    """
    <style>
    /* Ensure the main content uses a pleasing font (like Segoe UI or similar clean sans-serif) */
    .stApp {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Style the main application title */
    .main-header {
        font-size: 3em;
        font-weight: 700;
        color: #4B0082; /* Deep Purple */
        text-align: center;
        padding-bottom: 20px;
    }
    /* Style the sidebar navigation title */
    .sidebar-title {
        font-size: 1.5em;
        font-weight: 600;
        color: #0077B6; /* Dark Blue */
    }
    /* Custom style for primary buttons */
    div.stButton > button:first-child {
        background-color: #0077B6; /* Dark Blue */
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 5px;
    }
    /* Style for 'Out of Stock' text in tables (Styling relies on Streamlit version compatibility) */
    .out-of-stock {
        color: #D62828; /* Red */
        font-weight: 700;
        background-color: #F8D7DA;
        padding: 3px 6px;
        border-radius: 3px;
        display: inline-block;
        font-size: 0.9em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- DATABASE SETUP ---
DB_NAME = 'bookstore.db'

def init_db():
    """Initializes the SQLite database and creates the tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Books Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            author TEXT NOT NULL,
            copies INTEGER NOT NULL
        )
    """)

    # 2. Orders Table (Includes 'status' and 'username')
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            username TEXT,             
            quantity INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pending',  
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)
    
    # 3. Users Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)
    
    # Ensure the default admin user ('library') exists
    try:
        c.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                  ('library', 'admin@bookstore.com', '1234', 1))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()

# --- BOOK CRUD FUNCTIONS ---

def add_book(name, author, copies):
    """Adds a new book to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO books (name, author, copies) VALUES (?, ?, ?)", 
              (name, author, copies))
    conn.commit()
    conn.close()

def get_all_books():
    """Retrieves all books as a Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, name, author, copies FROM books", conn)
    conn.close()
    return df

def get_book_by_id(book_id):
    """Retrieves a single book's details based on its ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, author, copies FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    conn.close()
    return book 

def update_book(book_id, name, author, copies):
    """Updates the details of an existing book."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE books SET name=?, author=?, copies=? WHERE id=?", 
              (name, author, copies, book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    """Deletes a book from the database based on its ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return True
    
# --- AUTH & ORDER FUNCTIONS ---

def register_user(username, email, password):
    """Adds a new user to the database with is_admin=0 (regular user)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                  (username, email, password, 0))
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Username already exists. Please choose another."
    except Exception as e:
        conn.close()
        return False, f"An error occurred: {e}"

def verify_login(username, password):
    """Checks the database for matching username and password."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE username = ? AND password = ?", 
              (username, password))
    result = c.fetchone()
    conn.close()
    
    if result:
        return True, result[0] 
    return False, None

def get_all_users():
    """Retrieves all registered users as a Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, username, email, is_admin FROM users", conn)
    conn.close()
    return df

def get_low_stock_books(threshold=5):
    """Retrieves books with copies less than or equal to the defined threshold."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, name, copies FROM books WHERE copies <= ? AND copies > 0"
    df = pd.read_sql_query(query, conn, params=(threshold,))
    conn.close()
    return df

def get_out_of_stock_books():
    """Retrieves books with exactly 0 copies remaining."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, name, author FROM books WHERE copies = 0"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_user_orders(username):
    """Retrieves all orders placed by a specific user."""
    conn = sqlite3.connect(DB_NAME)
    query = f"""
    SELECT 
        o.id AS Order_ID,
        b.name AS Book_Name,
        o.quantity AS Quantity,
        o.status AS Status,
        o.timestamp AS Order_Time
    FROM orders o
    JOIN books b ON o.book_id = b.id
    WHERE o.username = ?
    ORDER BY o.timestamp DESC
    """
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df

def record_order_submission(cart_items, username):
    """Records a pending order submitted by a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check current stock before recording the pending order
    for book_id, quantity in cart_items.items():
        book = get_book_by_id(book_id)
        if not book or book[3] < quantity:
             conn.close()
             return False, f"Stock error: Not enough copies of Book ID {book_id}."
             
        # Insert each cart item as a separate pending order row
        c.execute("INSERT INTO orders (book_id, username, quantity, status) VALUES (?, ?, ?, ?)", 
                  (book_id, username, quantity, 'Pending'))

    conn.commit()
    conn.close()
    return True, None

def process_checkout(order_id):
    """
    Admin function to finalize the order (change status, decrement stock).
    Returns success status, message, and the new stock level.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. Get order details
    c.execute("SELECT book_id, quantity FROM orders WHERE id = ? AND status = 'Pending'", (order_id,))
    order_details = c.fetchone()

    if not order_details:
        conn.close()
        return False, "Order not found or already processed.", 0

    book_id, quantity = order_details
    
    # Verify stock one last time before processing
    c.execute("SELECT copies FROM books WHERE id = ?", (book_id,))
    current_copies = c.fetchone()[0]

    if current_copies < quantity:
        conn.close()
        return False, f"Stock mismatch for Book ID {book_id}. Cannot complete checkout.", 0
    
    # Calculate new copies
    new_copies = current_copies - quantity
    
    # 2. Decrement stock (Inventory change happens ONLY on Admin Checkout)
    c.execute("UPDATE books SET copies = ? WHERE id = ?", (new_copies, book_id))
    
    # 3. Update order status
    c.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
    
    conn.commit()
    conn.close()
    # Return True, message, and the new stock level
    return True, f"Order {order_id} processed.", new_copies


# Initialize the database when the app starts
init_db()

# --- STREAMLIT UI AND LOGIC ---

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'current_user' not in st.session_state: 
    st.session_state.current_user = None     

def login_screen():
    """Handles the login and registration interfaces."""
    st.markdown("<h1 class='main-header'>📚 Simple Bookstore App</h1>", unsafe_allow_html=True)
    
    login_tab, register_tab = st.tabs(["🔒 Login", "📝 Register"])

    # --- LOGIN TAB ---
    with login_tab:
        st.subheader("Sign In")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                is_valid, is_admin_status = verify_login(username, password)
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.is_admin = (is_admin_status == 1)
                    st.session_state.current_user = username 
                    st.success(f"Welcome back, {username}!")
                    st.rerun() 
                else:
                    st.error("Invalid Username or Password")

    # --- REGISTER TAB ---
    with register_tab:
        st.subheader("Create an Account")
        reg_username = st.text_input("New Username", key="reg_username")
        reg_email = st.text_input("Email (for record)", key="reg_email")
        reg_password = st.text_input("New Password", type="password", key="reg_password")
        
        if st.button("Register", key="register_button"):
            if not reg_username or not reg_email or not reg_password:
                st.error("Please fill in all fields.")
            else:
                if "@" not in reg_email or "." not in reg_email:
                    st.error("Please enter a valid email address.")
                else:
                    success, message = register_user(reg_username, reg_email, reg_password)
                    if success:
                        st.success(f"{message} You can now log in using the Login tab.")
                    else:
                        st.error(message)


def display_books(df):
    """
    Displays the list of books in a table, 
    showing 'Out of Stock' when copies are 0, using plain text.
    """
    st.header("📖 Available Books")
    
    # --- Transform copies column (FIXED) ---
    def format_copies(copies):
        if str(copies) == '0':
            # FIX: Return plain text only to avoid error in older Streamlit versions
            return 'Out of Stock' 
        return str(copies)

    if 'copies' in df.columns:
        df['Copies in Stock'] = df['copies'].apply(format_copies)
    
    # Drop the original numeric copies column
    df_display = df.drop(columns=['copies'], errors='ignore')
    
    # Final display using st.dataframe 
    st.dataframe(
        df_display, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("Book ID"),
            "name": st.column_config.TextColumn("Book Name"),
            "author": st.column_config.TextColumn("Author"),
            "Copies in Stock": st.column_config.TextColumn("Copies in Stock"),
        }
    )


def main_app():
    """The main application interface after login."""
    
    st.sidebar.markdown('<p class="sidebar-title">Bookstore Navigation</p>', unsafe_allow_html=True)
    
    # Navigation menu updated for Admin access
    if st.session_state.is_admin:
        menu_options = ["View Books", "Manage Books", "View Orders", "View Users", "Books Out of Stock"]
        choice = st.sidebar.selectbox("Select Action", menu_options)
        
        # --- ADMIN LOW STOCK NOTIFICATION ---
        low_stock_df = get_low_stock_books()
        if not low_stock_df.empty:
            st.error(f"🚨 Inventory Alert: {len(low_stock_df)} book(s) are running low on stock!")
            with st.expander("Click to view low stock details"):
                st.dataframe(low_stock_df, hide_index=True)
        
    else:
        # Regular users only see View Books and Cart & Order
        menu_options = ["View Books", "Cart & Order", "Order Status"]
        choice = st.sidebar.selectbox("Select Action", menu_options)
        
    # --- 1. VIEW BOOKS (Shared) ---
    if choice == "View Books":
        books_df = get_all_books()
        display_books(books_df)

    # --- 2. MANAGE BOOKS (Admin Only) ---
    elif choice == "Manage Books":
        if not st.session_state.is_admin:
            st.error("Access Denied: Only administrators can manage books.")
            return

        st.header("✏️ Manage Books (Admin)")
        manage_choice = st.radio("Choose Action", ["➕ Add New Book", "🔄 Update Book Info", "🗑️ Delete Book"])

        if manage_choice == "➕ Add New Book":
            st.subheader("➕ Add Books")
            with st.form("add_book_form"):
                book_name = st.text_input("Book Name")
                author_name = st.text_input("Author Name")
                no_copies = st.number_input("Number of Copies", min_value=1, step=1)
                
                submitted = st.form_submit_button("Add Book")
                if submitted:
                    if book_name and author_name and no_copies > 0:
                        add_book(book_name, author_name, no_copies)
                        st.success(f"Book '{book_name}' added!")
                    else:
                        st.error("Please fill all fields.")
        
        elif manage_choice == "🔄 Update Book Info":
            st.subheader("🔄 Update Book Info")
            
            books_df = get_all_books()
            if not books_df.empty:
                book_id_list = books_df['id'].tolist()
                # Use names for better selection
                book_names = {row['id']: f"{row['name']} (ID: {row['id']})" for index, row in books_df.iterrows()}
                selected_book_option = st.selectbox("Select Book to Update", list(book_names.values()))
                
                if selected_book_option:
                    # Retrieve the ID from the selected option string
                    book_id_to_update = [k for k, v in book_names.items() if v == selected_book_option][0]
                    current_book = get_book_by_id(book_id_to_update)
                    
                    if current_book:
                        with st.form("update_book_form"):
                            new_name = st.text_input("Book Name", value=current_book[1])
                            new_author = st.text_input("Author Name", value=current_book[2])
                            new_copies = st.number_input("Number of Copies", min_value=0, step=1, value=current_book[3])
                            
                            submitted = st.form_submit_button("Update Book")
                            if submitted:
                                update_book(book_id_to_update, new_name, new_author, new_copies)
                                
                                st.toast(f"✅ Book ID {book_id_to_update} details updated!", icon='✅')
                                st.success(f"✅ The details for Book ID **{book_id_to_update}** have been updated!")
                                time.sleep(1) 
                                
                                st.rerun() 
            else:
                st.info("No books available to update.")

        elif manage_choice == "🗑️ Delete Book":
            st.subheader("🗑️ Delete Book")
            books_df = get_all_books()

            if not books_df.empty:
                book_id_list = books_df['id'].tolist()
                book_id_to_delete = st.selectbox("Select Book ID to Delete", book_id_list)

                book_to_delete = get_book_by_id(book_id_to_delete)
                if book_to_delete:
                    st.warning(f"Are you sure you want to delete: **{book_to_delete[1]}** by **{book_to_delete[2]}** (ID: {book_to_delete[0]})?")
                    
                    if st.button(f"Confirm Delete Book ID {book_id_to_delete}"):
                        delete_book(book_id_to_delete)
                        st.success(f"Book ID {book_id_to_delete} has been successfully deleted.")
                        st.rerun() 
            else:
                st.info("No books available to delete.")


    # --- 3. VIEW ORDERS (Admin Only) ---
    elif choice == "View Orders":
        if not st.session_state.is_admin:
            st.error("Access Denied: Only administrators can view orders.")
            return

        st.header("📦 Order Processing (Admin)")
        conn = sqlite3.connect(DB_NAME)
        # Fetch ALL orders, showing status
        query = """
        SELECT 
            o.id AS Order_ID,
            o.username AS User,
            b.name AS Book_Name,
            o.quantity AS Quantity,
            o.status AS Status,
            o.timestamp AS Order_Time
        FROM orders o
        JOIN books b ON o.book_id = b.id
        ORDER BY o.timestamp DESC
        """
        orders_df = pd.read_sql_query(query, conn)
        conn.close()
        
        pending_orders = orders_df[orders_df['Status'] == 'Pending']

        # --- PENDING ORDERS SECTION ---
        st.subheader("🔔 Pending Orders")
        if not pending_orders.empty:
            
            st.dataframe(pending_orders.drop(columns=['Status']), use_container_width=True)
            
            st.markdown("---")
            st.subheader("Process Checkout")
            
            order_id_list = pending_orders['Order_ID'].tolist()
            order_id_to_process = st.selectbox("Select Order ID to Checkout", order_id_list)
            
            if st.button("✅ Process Checkout (Decrement Stock)"):
                # Capture the new_copies count
                success, message, new_copies = process_checkout(order_id_to_process)
                
                if success:
                    st.success(f"Order {order_id_to_process} successfully checked out and stock updated!")
                    
                    # --- LOW STOCK WARNING POP-UP ---
                    if new_copies <= 5:
                        st.warning(f"🚨 LOW STOCK ALERT: The remaining copies for this book are **{new_copies}**!")
                    
                    st.rerun()
                else:
                    st.error(f"Error processing order {order_id_to_process}: {message}")
        else:
            st.info("No pending orders require processing.")

        # --- COMPLETED ORDERS SECTION ---
        st.subheader("History of Completed Orders")
        completed_orders = orders_df[orders_df['Status'] == 'Completed']
        if not completed_orders.empty:
            st.dataframe(completed_orders, use_container_width=True)
        else:
            st.info("No orders have been completed yet.")


    # --- 4. VIEW USERS (Admin Only) ---
    elif choice == "View Users":
        if not st.session_state.is_admin:
            st.error("Access Denied: Only administrators can view users.")
            return

        st.header("👥 Registered Users")
        users_df = get_all_users()
        
        users_df['Role'] = users_df['is_admin'].apply(lambda x: "Admin" if x == 1 else "Regular User")
        users_df = users_df.drop(columns=['is_admin'])

        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True,
                         column_config={
                             "id": "User ID", 
                             "username": "Username", 
                             "email": "Email",
                         })
        else:
            st.info("No users have registered yet (except the default admin).")

    # --- 5. BOOKS OUT OF STOCK (Admin Only) ---
    elif choice == "Books Out of Stock":
        if not st.session_state.is_admin:
            st.error("Access Denied: Only administrators can view this report.")
            return

        st.header("❌ Books Out of Stock")
        st.subheader("List of books with 0 copies remaining")

        out_of_stock_df = get_out_of_stock_books()

        if not out_of_stock_df.empty:
            st.dataframe(out_of_stock_df, use_container_width=True,
                         column_config={
                             "id": "Book ID", 
                             "name": "Book Name", 
                             "author": "Author",
                         })
            st.warning(f"Total out of stock titles: **{len(out_of_stock_df)}**")
        else:
            st.success("🎉 Excellent! All books currently have stock.")

    # --- 6. ORDER STATUS (User Only) ---
    elif choice == "Order Status":
        st.header("⏳ Your Order Status")
        
        user_orders_df = get_user_orders(st.session_state.current_user)
        
        if not user_orders_df.empty:
            st.subheader(f"Orders for {st.session_state.current_user}")
            st.dataframe(user_orders_df, use_container_width=True,
                         column_config={
                            "Order_ID": "ID", 
                            "Book_Name": "Book", 
                            "Quantity": "Qty", 
                            "Status": "Status", 
                            "Order_Time": "Time Placed"
                         })
        else:
            st.info("You have not placed any orders yet.")


    # --- 7. CART & ORDER (User Only) ---
    elif choice == "Cart & Order":
        if st.session_state.is_admin:
            st.error("Access Denied. Admins manage orders in 'View Orders'.")
            return

        st.header("🛒 Cart Management")
        books_df = get_all_books()
        books_in_stock = books_df[books_df['copies'] > 0]

        if books_in_stock.empty:
            st.info("Sorry, no books are currently in stock.")
            return

        st.subheader("Add Item to Cart")
        
        book_options = {row['id']: f"{row['name']} by {row['author']} (ID: {row['id']})" for index, row in books_in_stock.iterrows()}
        
        if not book_options:
            st.info("No books are available to add to cart.")
            return

        selected_option = st.selectbox("Select a book", list(book_options.values()))
        
        selected_id = list(book_options.keys())[list(book_options.values()).index(selected_option)]
        
        max_copies = books_in_stock[books_in_stock['id'] == selected_id]['copies'].iloc[0]
        
        quantity = st.number_input("Quantity", min_value=1, max_value=max_copies, step=1)
        
        if st.button("Add to Cart"):
            st.session_state.cart[selected_id] = st.session_state.cart.get(selected_id, 0) + quantity
            st.success(f"{quantity} copy(s) of '{books_in_stock[books_in_stock['id'] == selected_id]['name'].iloc[0]}' added to cart.")

        st.subheader("Cart Contents")
        if st.session_state.cart:
            cart_items = []
            total_quantity = 0
            for book_id, qty in st.session_state.cart.items():
                book = get_book_by_id(book_id)
                if book:
                    cart_items.append({"Book ID": book[0], "Name": book[1], "Quantity": qty})
                    total_quantity += qty
            
            st.dataframe(pd.DataFrame(cart_items), use_container_width=True)
            st.write(f"**Total Items:** {total_quantity}")

            # --- ACTION BUTTON (User Places Order) ---
            
            # Regular user places the order
            if st.button("✅ Place Order"):
                # Submit the cart contents as a pending order
                current_user = st.session_state.current_user 
                success, error_message = record_order_submission(st.session_state.cart, current_user)
                
                if success:
                    st.session_state.cart = {} # Clear the cart
                    
                    # --- DIALOGUE BOX EFFECT ---
                    st.balloons()
                    st.toast("🎉 ORDER PLACED!", icon="✅") 
                    st.success("Your order has been successfully submitted. An administrator will process it shortly.")
                    
                    st.rerun()
                else:
                     st.error(f"Could not place order: {error_message}")
        else:
            st.info("Your cart is empty.")


def run_app():
    """Determines whether to show the login screen or the main app."""
    if not st.session_state.logged_in:
        login_screen()
    else:
        main_app()
        # Add a logout button to the sidebar
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.session_state.cart = {}
            st.session_state.current_user = None 
            st.rerun()

if __name__ == '__main__':
    run_app()