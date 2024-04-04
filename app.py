from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt, check_password_hash

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = '\x9f\x83=0\xecRVY\xe02\x99p\xc6<\x8b\x18'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///login.db' #this set up the path to our database
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 10) # keep the session on for 10 min
db = SQLAlchemy(app) 


class Person(db.Model): # create a table using sqlalchemy
    __tablename__ = 'Person'
    utorid = db.Column(db.String(20), primary_key=True) 
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(7), nullable=False)
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
    role = get_role()
    return render_template('index.html', role=role)  # render_template actually linking to the html
    # we take the pagename and use it in the html

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        utorid=request.form['utorid']
        name=request.form['name']
        email=request.form['email']
        role=request.form['role']
        hashed_password=bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
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

# add the register user into our db
def add_users(reg_details):
    user = Person(utorid=reg_details[0], name=reg_details[1], email=reg_details[2], password=reg_details[3], role=reg_details[4])
    db.session.add(user)
    db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        if 'user' in session:
            flash('You are already logged in!')
            return redirect(url_for('index'))
        else:
            return render_template('login.html')
    else:
        name=request.form['name']
        password=request.form['password']
        person = Person.query.filter_by(name = name).first()
        if not person or not bcrypt.check_password_hash(person.password, password):
            flash('Please check your login details and try again', 'error') #'error' is optional
            return render_template('login.html')
        else:
            # log_details=(
            #     utorid,
            #     password
            # )
            session['user'] = name
            session.permanent=True  # closing the browser will not log out
            flash('Logged in Successfully!')
            return redirect(url_for('index'))

# unsure if the logout function is correct
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/calendar')
def calendar():
    role = get_role()
    return render_template('calendar.html', role=role)

@app.route('/CourseTeam')
def CourseTeam():
    role = get_role()
    return render_template('CourseTeam.html', role=role)

@app.route('/lecture')
def lecture():
    role = get_role()
    return render_template('lecture.html', role=role)

@app.route('/lab')
def lab():
    role = get_role()
    return render_template('lab.html', role=role)

@app.route('/assignment')
def assignment():
    role = get_role()
    return render_template('assignment.html', role=role)

@app.route('/resources')
def resources():
    role = get_role()
    return render_template('resources.html', role=role)

@app.route('/feedback')
def feedback():
    role = get_role()
    return render_template('feedback.html', role=role)

@app.route('/grades')
def grades():
    grades_result = None

    if "user" in session:
        name = session.get("user")
        user = Person.query.filter_by(name = name).first()
        utorid = user.utorid
        grades_result = query_grades(utorid)
    
    role = get_role()
    return render_template('grades.html', grades = grades_result, role=role)

# get a student's grades (so we can display it in a table)
def query_grades(utorid):
    query_grade = Grades.query.filter_by(utorid = utorid).first()
    return query_grade 

@app.route('/manage', methods = ['GET', 'POST']) # methods allow us to do something with the input
# helps instructors change/add a student's grade for an assignment 
def manage():
    if request.method == 'GET':
        role = get_role()
        return render_template('manage.html', role=role)
    else: # render this if the method is POST
        grade_details = (
            request.form['Utorid'],
            request.form['Assignment'],
            request.form['Grade']
        )
        add_grades(grade_details)
        flash("Student's grade changed successfully!")
        role = get_role()
        return render_template('manage.html', role=role)

# change a student's grade for a specific assignment (into the db)    
def add_grades(grade_details):
    student = Grades.query.filter_by(utorid = grade_details[0])
    setattr(student, grade_details[1], grade_details[2])
    db.session.commit()


# get the role of the user
def get_role():
    role = None

    # # Retrieve user's role
    if 'user' in session:
        username = session.get('user')
        user = Person.query.filter_by(name = username).first()
        role = user.role
    return role

if __name__ == '__main__':
    app.run(debug=True)