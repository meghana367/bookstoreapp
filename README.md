# 📚 Simple Bookstore Management Application
This is a complete, role-based Bookstore Management System built using Python and the Streamlit library. It utilizes an embedded SQLite database for data persistence, requiring no external database server setup.

The application implements full CRUD (Create, Read, Update, Delete) for book inventory, handles user registration, and manages a two-stage ordering process (User Places Order, Admin Processes Checkout).

# ✨ Features
**The application is split into two primary roles:** Admin (Inventory/Order Processing) and Regular User (Browsing/Placing Orders).

## General Features
**User Registration & Login:** New users can register and log in with their credentials.

**Role-Based Access:** Functionality is strictly segregated based on user role.

**View Books:** All users can view the list of available books.

## 💼 Admin Features (Username: library, Password: 1234)
**Manage Books (CRUD):** Admins can add new books, update existing book details (name, author, copies), and delete books from the system.

**View Orders:** A dedicated interface to view all pending orders placed by users.

**Process Checkout:** Admins perform the actual "checkout," which decrements the book stock and changes the order status from "Pending" to "Completed."

**View Users:** Lists all registered users and their roles (Admin/Regular User).

**Books Out of Stock:** Provides a focused list of all books with exactly 0 copies remaining.

**Inventory Alerts:** A prominent notification appears on the admin's homepage if any book's stock falls to 5 copies or less.

## 🛍️ User Features
**Cart & Order:** Users can add available books to their cart.

**Place Order:** Clicking "Place Order" submits the cart contents to the database with a 'Pending' status. The user receives an immediate confirmation message.

**Order Status:** A separate view that allows the user to track the status (Pending or Completed) of all their placed orders.

# 🚀 Installation and Setup
This application is designed for easy local execution.

## Prerequisites
You need Python 3.8+ installed on your system.

## 1. Clone the Repository

git clone [YOUR_GITHUB_REPO_LINK]
cd [your-repo-name]

## 2. Install Dependencies
Install the required Python packages using the provided requirements.txt file.

pip install -r requirements.txt

## 3. Run the Application
Start the Streamlit application from your terminal:

streamlit run bookstoreapp.py

The application will automatically open in your default web browser (usually at http://localhost:8501).

## 💾 Database and Credentials
The application creates and uses a local bookstore.db file in the project root.
| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `Admin` | `12345` | Hardcoded Admin account for management access. |
| **User** | (New Account) | (New Password) | Register a new account via the Register tab. |

**Database Note:** Since the database is SQLite, if you delete the bookstore.db file and rerun the app, all existing data (users, books, orders) will be reset.

# ☁️ Deployment
This project is ready for simple deployment via Streamlit Community Cloud or similar Python hosting services (like Render or Heroku). Ensure the following files are pushed to your GitHub repository:

bookstoreapp.py

requirements.txt

bookstore.db (for initial data/structure)

.gitignore (optional, but recommended)

# 🤝 Contributing
This application was created as a demonstration project. If you have suggestions or wish to contribute enhancements, please feel free to fork the repository and submit a pull request!

**Thank you for checking out the Simple Bookstore App!**
