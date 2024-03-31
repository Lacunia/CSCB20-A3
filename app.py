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


class Person(db.Model): # create a table using sqlalchemy
    __tablename__ = 'Person'
    utorid = db.Column(db.String(20), primary_key=True) 
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(1), nullable=False)
    grades = db.relationship('Grades', backref='person', lazy=True, uselist=False) # ensures one-to-one relationship

    def __init__(self, utorid, name, email, password, role, **kwargs):
        super().__init__(utorid=utorid, name=name, email=email, password=password, role=role, **kwargs)
        self.grades = Grades(utorid=utorid)

    def __repr__(self): # string representation of the table
        return f"Person('{self.utorid}', '{self.name}', '{self.role})"
    
class Grades(db.Model): # create a table using sqlalchemy
    __tablename__ = 'Grades'
    id = db.Column(db.Integer, primary_key=True)
    utorid = db.Column(db.String(20), db.ForeignKey('Person.utorid'), nullable=False) 
    assignment_1 = db.Column(db.Float)
    assignment_2 =db.Column(db.Float)
    assignment_3  = db.Column(db.Float)
    midterm = db.Column(db.Float)
    final = db.Column(db.Float)

    def __repr__(self):
        return f"Post('{self.utorid}')"


@app.route('/') # the function will be executed if the web route has '/' or '/home' as extensions
@app.route('/index')
def index():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
    
    # # Retrieve user's role
    # user_id = session.get('user_id')
    # user = db_session.query(User).filter(User.id == user_id).first()

    # # Check user's role and render different templates accordingly
    # if user:
    #     if user.role == 'admin':
    #         return render_template('index_admin.html')
    #     elif user.role == 'user':
    #         return render_template('index_user.html')
    #     else:
    #         return render_template('index_unknown.html')  # Handle unknown role
    # else:
    #     return render_template('index_unknown.html')  # Handle user not found
    
    return render_template('index.html')  # render_template actually linking to the html
    # we take the pagename and use it in the html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        utorid=request.form['Utorid']
        name=request.form['Name']
        email=request.form['Email']
        role=request.form['Role']
        hashed_password=bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        # for added security when using bcrypt

        reg_details = (
            utorid,
            name,
            email,
            hashed_password,
            role
        )
        add_users(reg_details)
        flash('Registration successful! Please login now.')
        return redirect(url_for('login')) # redirect from the current page to this page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        if 'name' in session:
            flash('You are already logged in!')
            return redirect(url_for('index'))
        else:
            return render_template('login.html')
    else:
        utorid=request.form['Utorid']
        password=request.form['Password']
        person = Person.query.filter_by(utorid = utorid).first()
        if not person or not bcrypt.check_password(person.password, password):
            flash('Please check your login details and try again', 'error')
            return render_template('login.html', login_status=False)
        else:
            # log_details=(
            #     utorid,
            #     password
            # )
            session['user_id'] = person.utorid
            session.permanent=True
            login_status=True
            flash('Logged in Successfully!')
            return redirect(url_for('index'), login_status=True)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/CourseTeam')
def CourseTeam():
    return render_template('CourseTeam.html')

@app.route('/lecture')
def lecture():
    return render_template('lecture.html')

@app.route('/lab')
def lab():
    return render_template('lab.html')

@app.route('/assignment')
def assignment():
    return render_template('assignment.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/grades')
def grades():
    return render_template('grades.html')
# def notes():
#     query_notes_result = query_notes()
#     return render_template('notes.html', query_notes_result=query_notes_result) 

@app.route('/manage', methods = ['GET', 'POST']) # methods allow us to do something with the input
# helps instructors change/add a student's grade for an assignment 
def manage():
    if request.method == 'GET':
        return render_template('manage.html')
    else: # render this if the method is POST
        grade_details = (
            request.form['Utorid'],
            request.form['Assignment'],
            request.form['Grade']
        )
        add_grades(grade_details)
        flash("Student's grade changed successfully!")
        return render_template('manage.html')

# change a student's grade for a specific assignment (into the db)    
def add_grades(grade_details):
    student = Grades.query.filter_by(utorid = grade_details[0])
    setattr(student, grade_details[1], grade_details[2])
    db.session.commit()

# get a student's grades (so we can display it in a table)
def query_grades(utorid):
    query_grade = Grades.query.filter_by(utorid = utorid).first()
    return query_grade

# add the register user into our db
def add_users(reg_details):
    user = Person(utorid=reg_details[0], name=reg_details[1], email=reg_details[2], password=reg_details[3], role=reg_details[4])
    db.session.add(user)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)