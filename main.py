from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_login import LoginManager, login_required, UserMixin,login_user, logout_user
from flask import flash

app = Flask(__name__)
app.template_folder = "something"
app.secret_key = '000d88cd9d90036ebdd237eb6b0db00'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/query'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Note(db.Model):
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)

class Accounts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
  
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return Accounts.query.get(int(user_id))

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        account = Accounts.query.filter_by(username=username).first()
        if account and account.password==password:
            login_user(account)
            session['loggedin'] = True
            session['id'] = account.id
            session['username'] = account.username
            msg = 'Logged in successfully!'
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect username or password.'
            return render_template('login.html',msg=msg)
    return render_template('login.html')

@app.route('/logout')
@app.route('/dashboard/logout')
@app.route('/query/logout')
@login_required
def logout():
    logout_user()
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']  
        existing_user = Accounts.query.filter_by(username=username).first()
        if existing_user:
            msg = 'Username already exists. Please choose a different username.'
            return redirect(url_for('register'))
        else:
            new_user = Accounts(username=username, password=password, email=email)
            db.session.add(new_user)
            db.session.commit()
            msg = 'Registration successful. You can now login.'
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)

@app.route('/query', methods=['GET', 'POST'])
@login_required
def query():
    account_id=session.get('id')
    if request.method == 'POST':
        content = request.form['comments']
        note = Note(content=content,account_id=account_id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('query.html')

@app.route('/dashboard')
@login_required
def dashboard():
    account_id=session.get('id')
    print(account_id)
    page = request.args.get('page', 1, type=int)
    notes_per_page = 7
    notes_pagination = Note.query.filter_by(account_id=account_id).order_by(desc(Note.id)).paginate(page=page, per_page=notes_per_page, error_out=False)
    notes = notes_pagination.items
    return render_template('dashboard.html', notes=notes, notes_pagination=notes_pagination)

@app.route('/delete_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.account_id != session.get('id'):
        flash("You can't delete notes that don't belong to you.", 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update_note/<int:note_id>', methods=['GET', 'POST'])
@login_required
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.account_id != session.get('id'):
        flash("You can't update notes that don't belong to you.", 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        new_content = request.form['new_content']
        note.content = new_content
        db.session.commit()
        flash('Note updated successfully.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('update_note.html', note=note)
 
if __name__ == '__main__': 
    app.run(debug=True)
