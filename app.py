from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = '\x9f\x83=0\xecRVY\xe02\x99p\xc6<\x8b\x18'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db' #this set up the path to our database
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 10) # keep the session on for 10 min
db = SQLAlchemy(app) 

# when accessing from the terminal, use the following to manually access the database:
# >>> .venv (activate it)
# >>> py
# >>> from app import app, db
# >>> app.app_context().push()
# >>> db.create_all()
# >>> from app import Person, Notes
# >>> person3 = Person(username='Student2', email='student2@email.com', password='password2')
# >>> person4 = Person(username='Student3', email='student3@email.com', password='password3')
# >>> db.session.add(person3)
# >>> db.session.add(person4)
# >>> db.session.commit()

# >>> Person.query.all()  <-- return the result in a list
# [Person('Purva', 'purva@gmail.com'), Person('Student', 'student@gmail.com'), Person('Student2', 'student2@email.com')
# Person('Student3', 'student3@email.com')]

# >>> Person.query.first() 
# Person('Purva', 'purva@gmail.com')

# >>> Person.qeury.filter_by(username='Purva').all()   <-- find all data with username 'Purva'
# [Person('Purva', 'purva@gmail.com') ]
# >>> Person.qeury.filter_by(username='Purva').first()   <-- find the first data with username 'Purva'
# Person('Purva', 'purva@gmail.com')

# >>> P1 = Person.qeury.filter_by(username='Purva').first()   <-- store the first data with username 'Purva' into P1
# >>> P1.id
# 1
# >>> P1.password
# 'password'

class Person(db.Model): # create a table using sqlalchemy
    __tablename__ = 'Person'
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(20), unique=True, nullable=False)
    email=db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    notes=db.relationship('Notes', backref='author', lazy=True)  # not creating another column, just a relationship

    def __repr__(self): # string representation of the table
        return f"Person('{self.username}', '{self.email}')"
    
class Notes(db.Model): # create a table using sqlalchemy
    __tablename__ = 'Notes'
    id = db.Column(db.Integer, primary_key=True) 
    title = db.Column(db.String(120), nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.now) # add the current date
    content = db.Column(db.Text, nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


@app.route('/') # the function will be executed if the web route has '/' or '/home' as extensions
@app.route('/home')
def home():
    pagename = 'Home'
    return render_template('home.html', pagename = pagename)  # render_template actually linking to the html
    # we take the pagename and use it in the html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        user_name=request.form['Username']
        email=request.form['Email']
        hashed_password=bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        # for added security when using bcrypt

        reg_details = (
            user_name,
            email,
            hashed_password
        )
        add_users(reg_details)
        flash('Registration successful! Please login now.')
        return redirect(url_for('login')) # redirect from the current page to this page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        if 'name' in session:
            flash('Your are already logged in!')
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    else:
        username=request.form['Username']
        password=request.form['Password']
        person = Person.query.filter_by(username = username).first()
        if not person or not bcrypt.check_password(person.password, password):
            flash('Please check your login details and try again', 'error')
            return render_template('login.html')
        else:
            log_details=(
                username,
                password
            )
            session['name']=username
            session.permanent=True
            flash('Logged in Successfully!')
            return redirect(url_for('home'))

@app.route('/notes')
def notes():
    pagename = 'Lecture Notes'
    query_notes_result = query_notes()
    return render_template('notes.html', pagename = pagename, query_notes_result=query_notes_result) 

@app.route('/add', methods = ['GET', 'POST']) # methods allow us to do something with the input
def add():
    if request.method == 'GET':
        pagename = 'Add Notes'
        return render_template('add.html', pagename=pagename)
    else: # render this if the method is POST
        pagename = 'Success'
        note_details = (
            request.form['Note_ID'],
            request.form['Title'],
            request.form['Content'],
            request.form['Your_ID']
        )
        add_notes(note_details)
        return render_template('add_success.html', pagename=pagename)

# helps add the notes that we got from the form into the database    
def add_notes(note_details):
    note = Notes(id=note_details[0], title=note_details[1], content=note_details[2], person_id=note_details[3])
    db.session.add(note)
    db.session.commit()

def query_notes():
    query_notes = Notes.query.all()
    return query_notes

def add_users(reg_details):
    user = Person(username=reg_details[0], email=reg_details[1], password=reg_details[2])
    db.session.add(user)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)