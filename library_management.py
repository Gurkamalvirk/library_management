from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize SQLite database and pre-populate with sample books
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  author TEXT NOT NULL, 
                  total_copies INTEGER NOT NULL, 
                  available_copies INTEGER NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS borrowings 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  book_id INTEGER, 
                  user_name TEXT NOT NULL, 
                  borrow_date TEXT NOT NULL, 
                  due_date TEXT NOT NULL, 
                  return_date TEXT, 
                  FOREIGN KEY(book_id) REFERENCES books(id))''')
    
    # Check if books table is empty
    c.execute('SELECT COUNT(*) FROM books')
    if c.fetchone()[0] == 0:
        # Pre-populate with sample books
        sample_books = [
            ("To Kill a Mockingbird", "Harper Lee", 5, 5),
            ("1984", "George Orwell", 3, 3),
            ("Pride and Prejudice", "Jane Austen", 4, 4),
            ("The Great Gatsby", "F. Scott Fitzgerald", 2, 2),
            ("The Catcher in the Rye", "J.D. Salinger", 3, 3),
            ("Lord of the Rings", "J.R.R. Tolkien", 6, 6),
            ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", 5, 5),
            ("The Hobbit", "J.R.R. Tolkien", 4, 4),
            ("Animal Farm", "George Orwell", 3, 3),
            ("Brave New World", "Aldous Huxley", 2, 2),
        ]
        c.executemany('INSERT INTO books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)', 
                      sample_books)
    
    conn.commit()
    conn.close()

# Home route to display all books
@app.route('/')
def index():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    conn.close()
    return render_template('index.html', books=books)

# Add a new book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        total_copies = int(request.form['total_copies'])
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('INSERT INTO books (title, author, total_copies, available_copies) VALUES (?, ?, ?, ?)',
                  (title, author, total_copies, total_copies))
        conn.commit()
        conn.close()
        flash('Book added successfully!')
        return redirect(url_for('index'))
    return render_template('add_book.html')

# Update a book
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        total_copies = int(request.form['total_copies'])
        
        # Get current available copies
        c.execute('SELECT available_copies FROM books WHERE id = ?', (id,))
        current_available = c.fetchone()[0]
        # Adjust available copies based on new total
        available_copies = min(current_available, total_copies)
        
        c.execute('UPDATE books SET title = ?, author = ?, total_copies = ?, available_copies = ? WHERE id = ?',
                  (title, author, total_copies, available_copies, id))
        conn.commit()
        conn.close()
        flash('Book updated successfully!')
        return redirect(url_for('index'))
    
    c.execute('SELECT * FROM books WHERE id = ?', (id,))
    book = c.fetchone()
    conn.close()
    return render_template('update_book.html', book=book)

# Delete a book
@app.route('/delete/<int:id>')
def delete_book(id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (id,))
    c.execute('DELETE FROM borrowings WHERE book_id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Book deleted successfully!')
    return redirect(url_for('index'))

# Borrow a book
@app.route('/borrow/<int:id>', methods=['GET', 'POST'])
def borrow_book(id):
    if request.method == 'POST':
        user_name = request.form['user_name']
        borrow_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('SELECT available_copies FROM books WHERE id = ?', (id,))
        available_copies = c.fetchone()[0]
        
        if available_copies > 0:
            c.execute('INSERT INTO borrowings (book_id, user_name, borrow_date, due_date) VALUES (?, ?, ?, ?)',
                      (id, user_name, borrow_date, due_date))
            c.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id = ?', (id,))
            conn.commit()
            flash('Book borrowed successfully!')
        else:
            flash('No copies available to borrow!')
        conn.close()
        return redirect(url_for('index'))
    
    return render_template('borrow_book.html', book_id=id)

# Return a book
@app.route('/return/<int:id>')
def return_book(id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    return_date = datetime.now().strftime('%Y-%m-%d')
    
    # Find the first non-returned borrowing for this book
    c.execute('SELECT id FROM borrowings WHERE book_id = ? AND return_date IS NULL LIMIT 1', (id,))
    borrowing = c.fetchone()
    
    if borrowing:
        c.execute('UPDATE borrowings SET return_date = ? WHERE id = ?', (return_date, borrowing[0]))
        c.execute('UPDATE books SET available_copies = available_copies + 1 WHERE id = ?', (id,))
        conn.commit()
        flash('Book returned successfully!')
    else:
        flash('No borrowing record found!')
    
    conn.close()
    return redirect(url_for('index'))

# View borrowing history
@app.route('/history')
def borrowing_history():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('''SELECT b.title, bor.user_name, bor.borrow_date, bor.due_date, bor.return_date 
                 FROM borrowings bor 
                 JOIN books b ON bor.book_id = b.id''')
    borrowings = c.fetchall()
    conn.close()
    return render_template('history.html', borrowings=borrowings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)