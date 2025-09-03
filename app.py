from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

# ====================================================================
# Flask App Configuration
# ====================================================================

app = Flask(__name__)
# IMPORTANT: Use a strong, unique, and secret key for your application!
app.secret_key = 'your_super_secret_key_here'

# ====================================================================
# MySQL Database Configuration
# ====================================================================

# Configure the connection to your MySQL database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'srihari@05'
app.config['MYSQL_DB'] = 'book_hub'
# Initialize the MySQL extension with the Flask app
mysql = MySQL(app)

# ====================================================================
# Application Routes
# ====================================================================

@app.route('/')
def home():
    """
    The main landing page. If a user is logged in, they are redirected to the
    books page. Otherwise, the login/register page is shown.
    """
    if 'loggedin' in session:
        return redirect(url_for('books'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login attempts.
    - On POST: Validates the submitted username and password against the database.
    - On GET: Renders the index.html page (which contains the login form).
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        # Execute a query to find the user by username
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone() # Fetches the first matching record
        cursor.close()

        # Check if a user was found and if the password hash matches
        # The fetched data is a tuple: (id, username, hashed_password)
        if user and check_password_hash(user[2], password):
            # Set session variables to mark the user as logged in
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('books'))
        else:
            flash('Incorrect username/password!', 'danger')
            return redirect(url_for('home'))
    
    # This route will only be accessed via POST from the form,
    # but a GET request to /login would just redirect to home
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles new user registration.
    - On POST: Validates the form data, hashes the password, and inserts
    a new user into the database.
    - On GET: Renders the home page (which contains the registration form).
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Hash the password for secure storage
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cursor = mysql.connection.cursor()
        try:
            # Insert the new user into the 'users' table
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                             (username, hashed_password, email))
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            # Handle potential errors, such as a duplicate username
            flash(f'Error registering: {e}', 'danger')
            mysql.connection.rollback()
        finally:
            cursor.close()
    
    # Redirect to home for a GET request to /register
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    """
    Logs out the current user by clearing session variables.
    """
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/books')
def books():
    """
    Displays the list of books available, fetching data from the database.
    Requires the user to be logged in.
    """
    if 'loggedin' not in session:
        flash('Please login to view books.', 'warning')
        return redirect(url_for('home'))

    cursor = mysql.connection.cursor()
    # Fetch all books from the 'books' table
    cursor.execute("SELECT id, title, author, description, price, image_url FROM books")
    # Fetch all the results
    books_data = cursor.fetchall()
    cursor.close()
    
    return render_template('books.html', books=books_data)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    """
    Adds a book to the user's cart (stored in the session).
    """
    if 'loggedin' not in session:
        flash('Please login to add items to cart.', 'warning')
        return redirect(url_for('home'))

    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = {}

    cursor = mysql.connection.cursor()
    # Check if the book exists and is in stock
    cursor.execute("SELECT price, title, stock_quantity FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()
    cursor.close()

    if book and book[2] > 0: # book[2] is stock_quantity
        book_title = book[1]
        book_price = float(book[0])
        
        # Add or update the book in the cart dictionary
        book_id_str = str(book_id)
        if book_id_str in session['cart']:
            session['cart'][book_id_str]['quantity'] += 1
        else:
            session['cart'][book_id_str] = {'title': book_title, 'price': book_price, 'quantity': 1}
        
        # Mark the session as modified because a nested dictionary was changed
        session.modified = True
        flash(f'{book_title} added to cart!', 'success')
    else:
        flash('Book not found or out of stock.', 'danger')
    
    return redirect(url_for('books'))

@app.route('/view_cart')
def view_cart():
    """
    Displays the contents of the user's shopping cart by fetching
    full details from the database.
    """
    if 'loggedin' not in session:
        flash('Please login to view your cart.', 'warning')
        return redirect(url_for('home'))
    
    cart = session.get('cart', {})
    cart_items = []
    total_price = 0
    
    if cart:
        # Get book IDs from the cart keys
        book_ids = [int(book_id_str) for book_id_str in cart.keys()]
        
        # Fetch book details from the database
        cursor = mysql.connection.cursor()
        query = "SELECT id, title, author, price, image_url FROM books WHERE id IN (%s)"
        placeholders = ','.join(['%s'] * len(book_ids))
        cursor.execute(query % placeholders, tuple(book_ids))
        book_details_from_db = cursor.fetchall()
        cursor.close()
        
        # Create a dictionary for quick lookup of author and image_url
        book_details_map = {item[0]: {'title': item[1], 'author': item[2], 'price': item[3], 'image_url': item[4]} for item in book_details_from_db}

        # Build the final list of cart items by combining data
        for book_id_str, item_details_from_session in cart.items():
            book_id = int(book_id_str)
            db_details = book_details_map.get(book_id)
            
            if db_details:
                item_quantity = item_details_from_session.get('quantity', 0)
                item_price = db_details['price']
                item_total_price = item_price * item_quantity
                
                full_item = {
                    'id': book_id,
                    'title': db_details['title'],
                    'author': db_details['author'],
                    'price': item_price,
                    'image_url': db_details['image_url'],
                    'quantity': item_quantity,
                    'total_price': item_total_price
                }
                cart_items.append(full_item)
                total_price += item_total_price
            
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:book_id>')
def remove_from_cart(book_id):
    """
    Removes a single item from the cart.
    """
    if 'loggedin' not in session:
        flash('Please login.', 'warning')
        return redirect(url_for('home'))
    
    book_id_str = str(book_id)
    if 'cart' in session and book_id_str in session['cart']:
        book_title = session['cart'][book_id_str]['title']
        del session['cart'][book_id_str]
        session.modified = True
        flash(f'{book_title} removed from cart.', 'info')
    else:
        flash('Item not found in cart.', 'warning')
    return redirect(url_for('view_cart'))

@app.route('/update_cart_quantity/<int:book_id>/<string:action>')
def update_cart_quantity(book_id, action):
    """
    Updates the quantity of a book in the cart.
    'action' can be 'increase' or 'decrease'.
    """
    if 'loggedin' not in session:
        flash('Please login to update your cart.', 'warning')
        return redirect(url_for('home'))

    book_id_str = str(book_id)
    if 'cart' in session and book_id_str in session['cart']:
        cart = session['cart']
        if action == 'increase':
            cart[book_id_str]['quantity'] += 1
        elif action == 'decrease':
            cart[book_id_str]['quantity'] -= 1
            if cart[book_id_str]['quantity'] <= 0:
                del cart[book_id_str]
        
        session.modified = True
    
    return redirect(url_for('view_cart'))

@app.route('/checkout_page')
def checkout_page():
    """
    Renders the dummy checkout payment page.
    """
    if 'loggedin' not in session:
        flash('Please login to checkout.', 'warning')
        return redirect(url_for('home'))
    
    if not session.get('cart'):
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('books'))
    
    # Recalculate total price to display on the checkout page
    cart = session.get('cart', {})
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    
    return render_template('checkout.html', total_price=total_price)

@app.route('/checkout', methods=['POST'])
def checkout():
    """
    Processes the checkout form submission, updates stock, and returns a JSON response.
    """
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'Please log in.'}), 401
    
    if not session.get('cart'):
        return jsonify({'success': False, 'message': 'Your cart is empty.'}), 400

    # The HTML's JavaScript is now handling the form submission and redirect.
    # This route is now primarily responsible for stock updates.
    
    cursor = mysql.connection.cursor()
    try:
        # Loop through cart items and update the stock_quantity in the database
        for book_id_str, item in session['cart'].items():
            book_id = int(book_id_str)
            quantity = item['quantity']
            cursor.execute("UPDATE books SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s", (quantity, book_id, quantity))
        
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Order processed successfully.'})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': f'Error processing order: {e}'}), 500
    finally:
        cursor.close()

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    """
    Clears the user's shopping cart from the session.
    This route is called asynchronously by the front-end JavaScript.
    """
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'Please log in.'}), 401

    session.pop('cart', None)
    session.modified = True
    return jsonify({'success': True, 'message': 'Cart cleared successfully.'})

# ====================================================================
# Main entry point for the application
# ====================================================================

if __name__ == '__main__':
    app.run(debug=True)
