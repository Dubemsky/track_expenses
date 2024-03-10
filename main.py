# imports
from flask import Flask, render_template, request, redirect, url_for,session
import psycopg2

app = Flask(__name__)
app.secret_key='pythonify'

# CONNECT TO THE DATABASE
def connect():
    return psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='12345',
        host='localhost',
        port='5432'
    )

# CREATE TABLE IF IT DOESN'T EXIST
def create_table():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users_details (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL, 
                    password VARCHAR(100) NOT NULL
                )
            """)
            conn.commit()

            # THIS CREATES THE USERS_ITEMS TABLE
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users_items (
                    item_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users_details(id),
                    item_name VARCHAR(100) NOT NULL,
                    item_price INTEGER,
                    date DATE,
                    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users_details(id)
                )
            """)
            conn.commit()

# ADD USERS DETAILS TO THE DATABASE
def insert_into_database(username, password):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users_details (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()

# FETCHES USERNAME FROM THE DATABASE
def username_in_database(name, password):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT * from users_details 
                        where username = %s""", (name,))
            user = cur.fetchone()  # This fetches the user

    # This checks if there is a user and the password matches
    if user and user[2] == password:
        return True
    else:
        return False
    
# THIS ADDS THE ITEMS TO THE DATABASE FOR THE USERS
def add_items_for_users(user_id, name, price, date):
    with connect() as conn:
        with conn.cursor() as cur:
            # ADDING THE USER ID ASWEL
            cur.execute(""" INSERT INTO users_items (user_id, item_name, item_price, date)
                        VALUES (%s, %s, %s, %s)""", (user_id, name, price, date))
            conn.commit()

# USED TO GET THE USER ID FROM THE DATABASE
def get_user_id(username):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users_details WHERE username = %s", (username,))
            result = cur.fetchone()
            if result is not None:
                return result[0]
            else:
                raise ValueError("User with username '{}' not found.".format(username))

# FETCHES ALL THE USERS ITEMS FROM THE DATABASE VIA USER ID
def get_items_from_table(user_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name,item_price,date FROM users_items WHERE user_id=%s",(user_id,))
            items=cur.fetchall()
            return items
        
#CALCULATES THE TOTAL MONEY SPENT
def get_total_money_spent(user_id):
    total=0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_price FROM users_items WHERE user_id=%s",(user_id,))
            prices=cur.fetchall()
            for price in prices:
                total += price[0]
            return total

    
# HANDLES THE LOGIN SECTION
@app.route('/', methods=['POST','GET'])
def login_function():
    error_message = None
    if request.method == 'POST':
        # Get the user's details
        name = request.form.get('username')
        password = request.form.get('password')

        # Checking if the username is in the database
        details = username_in_database(name, password)

        if details:
            # STORING CURRENT USER USING SESSION
            session['username'] = name
            return redirect(url_for('home_route_function'))
        else:
            error_message = "Invalid username or password. Please try again."

    return render_template('index.html', error_message=error_message)

# HANDLES THE SIGNUP SECTION
@app.route('/signup', methods=['GET', 'POST'])
def signup_function():
    success_message = None
    error_message = None

    if request.method == 'POST':
        # Get the user's details
        name = request.form.get('username')
        password = request.form.get('password')

        try:
            insert_into_database(name, password)
            success_message = "Signup successful!."
        
        except psycopg2.errors.UniqueViolation:
            # If a unique constraint violation occurs (i.e., username already exists), inform the user
            error_message = "Username already exists. Please choose a different username."

        except Exception as e:
            error_message = "An error occurred. Please try again later."

    return render_template('signup.html', success_message=success_message, error_message=error_message)


# HOME ROUTE AFTER USER LOGS IN
@app.route('/home', methods=['POST', 'GET'])
def home_route_function():
    if request.method == 'POST':
        name = session['username']
        user_id = get_user_id(name)
        item_name = request.form['item_name']
        price = request.form['price']
        date = request.form['date']

        # ADDING THE ITEMS TO THE DATABASE
        add_items_for_users(user_id, item_name, price, date)

        # Redirect to view-table route with username as a query parameter
        return redirect(url_for('home_route_function'))

    else:
        name = session.get('username')
        user_id=get_user_id(name)
        user_items=get_items_from_table(user_id)
        total_spent=get_total_money_spent(user_id)
        return render_template('home.html', name=name.upper(),user_items=user_items,total_spent=total_spent)


if __name__ == "__main__":
    # CREATING THE TABLE 
    create_table()
    app.run(debug=True)
