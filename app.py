from flask import Flask, render_template, request,session,redirect
import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
    database="library_management"
)
cursor=db.cursor()

app=Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    return render_template('login.html')
@app.route('/login', methods=['POST'])
def login():
    username=request.form['username']
    password=request.form['password']
    role=request.form['role']
    if role=='admin':
        cursor.execute("SELECT * FROM admin_login WHERE username=%s AND password=%s",(username,password))
        admin=cursor.fetchone()
        if admin:
            session['username'] = username
            session['role'] = role
            return render_template('admin.html')
    elif role=='student':
        cursor.execute("SELECT * FROM student_login WHERE username=%s AND password=%s",(username,password))
        student=cursor.fetchone()
        if student:
            session['username'] = username
            session['role'] = role
            return render_template('student.html')  
    return render_template('login.html', error='Invalid credentials! Please try again.')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin')
def home_admin():
    return render_template('admin.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':




        title = request.form['title']
        author = request.form['author']
        quantity = request.form['quantity']
        location = request.form['location']
        cursor.execute("INSERT INTO books (title, author, quantity, location) VALUES (%s, %s, %s, %s)", (title, author, quantity, location))
        db.commit()
        return render_template('add.html', success='Book added successfully!')
    return render_template('add.html')

@app.route('/view_books')
def view_books():
    

    cursor.execute("SELECT title, author, SUM(quantity), location FROM books GROUP BY title, author, location")
    books = cursor.fetchall()

    return render_template('view_books.html', books=books)

@app.route('/search_books')
def search_books():
    query = request.args.get('query')
    cursor.execute("SELECT title, author, SUM(quantity), location FROM books WHERE title LIKE %s GROUP BY title, author, location", (f'%{query}%',))
    books = cursor.fetchall()
    return render_template('view_books.html', books=books)

@app.route('/search_names')
def search_names():
    query = request.args.get('query')
    cursor.execute("SELECT book_title, student_name, trade_name, quantity, issue_date FROM issued_books WHERE student_name LIKE %s ORDER BY issue_date DESC", (f'%{query}%',))
    issued_records = cursor.fetchall()
    

    return render_template('issued.html', issued_books=issued_records, now=datetime.now())

@app.route('/delete_book/<string:book_title>')
def delete_book(book_title):
    try:
       
        query = "DELETE FROM books WHERE UPPER(title) = UPPER(%s)"
        cursor.execute(query, (book_title,))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    
    return redirect('/view_books')





cursor = db.cursor(buffered=True) 

@app.route('/issue_page/<string:title>')
def issue_page(title):
    cursor.execute("SELECT title, quantity FROM books WHERE title = %s", (title,))
    book = cursor.fetchone()
    return render_template('issue_form.html', book=book)

@app.route('/process_issue', methods=['POST'])
def process_issue():
    title = request.form['title']
    student = request.form['student']
    trade = request.form['trade']
    qty = int(request.form['quantity'])

    try:
        cursor.execute("UPDATE books SET quantity = quantity - %s WHERE title = %s", (qty, title))
        cursor.execute("""
            INSERT INTO issued_books (book_title, student_name, trade_name, quantity, issue_date) 
            VALUES (%s, %s, %s, %s, %s)
        """, (title, student, trade, qty, datetime.now()))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    return redirect('/view_books')



@app.route('/view_issued')
def view_issued():
    
    cursor.execute("SELECT book_title, student_name, trade_name, quantity, issue_date FROM issued_books ORDER BY issue_date DESC")
    issued_records = cursor.fetchall()
    

    return render_template('issued.html', issued_books=issued_records, now=datetime.now())



@app.route('/return_book/<string:title>/<string:student>')
def return_book(title, student):
    # Fetch the issued record details to display on the confirmation page
    cursor.execute("SELECT book_title, student_name, trade_name, quantity FROM issued_books WHERE book_title=%s AND student_name=%s", (title, student))
    item = cursor.fetchone()
    if item:
        return render_template('confirm_return.html', item=item)
    return redirect('/view_issued')

@app.route('/process_return', methods=['POST'])
def process_return():
    title = request.form['title']
    student = request.form['student']
    return_qty = int(request.form['return_qty'])
    
    try:
        # 1. Add the returned copies back to the books inventory
        cursor.execute("UPDATE books SET quantity = quantity + %s WHERE title = %s", (return_qty, title))
        
        # 2. Update or delete the issued record
        cursor.execute("SELECT quantity FROM issued_books WHERE book_title=%s AND student_name=%s", (title, student))
        record = cursor.fetchone()
        
        if record:
            current_qty = record[0]
            if return_qty >= current_qty:
                # If they return everything, delete the record
                cursor.execute("DELETE FROM issued_books WHERE book_title=%s AND student_name=%s", (title, student))
            else:
                # If it's a partial return, subtract the quantity
                cursor.execute("UPDATE issued_books SET quantity = quantity - %s WHERE book_title=%s AND student_name=%s", (return_qty, title, student))
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        
    return redirect('/view_issued')

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        cursor.execute("INSERT INTO admin_login (username, admin_name, password, role) VALUES (%s, %s, %s, %s)", (username, name, password, role))
        db.commit()
        return render_template('register.html', success='Registered successfully!')
    return render_template('register.html')


@app.route('/manage_users')
def manage_users():
    cursor.execute("SELECT * FROM admin_login")
    users = cursor.fetchall()
    return render_template('manage_users.html', users=users)


@app.route('/delete_user/<string:user_id>')
def delete_user(user_id):
    try:
       
        query = "DELETE FROM admin_login WHERE id = %s"
        cursor.execute(query, (user_id,))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    
    return redirect('/manage_users')

@app.route('/renew_book/<string:title>/<string:student>')
def renew_book(title, student):
    try:
        
        new_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
       
        query = "UPDATE issued_books SET issue_date = %s WHERE book_title = %s AND student_name = %s"
        cursor.execute(query, (new_date, title, student))
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    
    return redirect('/view_issued')

@app.route('/edit_issued/<string:title>/<string:student>', methods=['GET', 'POST'])
def edit_issued(title, student):
    if request.method == 'POST':
       
        new_title = request.form['book_title']
        new_student = request.form['student_name']
        new_trade = request.form['trade_name']
        new_qty = request.form['quantity']

       
        query = """
            UPDATE issued_books 
            SET book_title=%s, student_name=%s, trade_name=%s, quantity=%s 
            WHERE book_title=%s AND student_name=%s
        """
        cursor.execute(query, (new_title, new_student, new_trade, new_qty, title, student))
        db.commit()
        return redirect('/view_issued')

    
    cursor.execute("SELECT * FROM issued_books WHERE book_title=%s AND student_name=%s", (title, student))
    record = cursor.fetchone()
    
   
    return render_template('edit_issued.html', item=record)

@app.route('/edit_book_detail/<string:title>', methods=['GET', 'POST'])
def edit_book_detail(title):
    if request.method == 'POST':
        new_title = request.form['title']
        new_author = request.form['author']
        new_qty = request.form['quantity']
        new_loc = request.form['location']

        
        query = "UPDATE books SET title=%s, author=%s, quantity=%s, location=%s WHERE title=%s"
        cursor.execute(query, (new_title, new_author, new_qty, new_loc, title))
        db.commit()
        return redirect('/view_books')

    
    cursor.execute("SELECT title, author, quantity, location FROM books WHERE title=%s", (title,))
    book = cursor.fetchone()
    return render_template('edit_book_detail.html', book=book)






if __name__ == '__main__':
    app.run(debug=True, port=8000)