import os
from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)

def create_tables():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            body VARCHAR(500) NOT NULL
        )
    """)
    mysql.connection.commit()

with app.app_context():
    create_tables()

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM notes")
    notes = cursor.fetchall()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
def add():
    note = request.form['note']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO notes (body) VALUES (%s)", (note,))
    mysql.connection.commit()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM notes WHERE id = %s", (id,))
    mysql.connection.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0')