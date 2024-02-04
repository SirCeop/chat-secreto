from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
from dotenv import load_dotenv 
import os 

load_dotenv ()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "token")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    room_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

chat_rooms = {}

with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_room')
def create_room():
    if 'username' not in session:
        return redirect(url_for('login'))

    room_id = str(uuid.uuid4())
    chat_rooms[room_id] = []
    return redirect(url_for('chat', room_id=room_id))

@app.route('/chat/<room_id>', methods=['GET', 'POST'])
def chat(room_id):
    if room_id not in chat_rooms:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('login'))

        username = session['username']
        message_content = request.form.get('message')

        new_message = Message(username=username, room_id=room_id, content=message_content)
        db.session.add(new_message)
        db.session.commit()

    messages = Message.query.filter_by(room_id=room_id).all()

    return render_template('chat.html', room_id=room_id, messages=messages)

@app.route('/submit_message/<room_id>', methods=['POST'])
def submit_message(room_id):
    if room_id not in chat_rooms:
        return redirect(url_for('index'))

    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    message_content = request.form.get('message')

    new_message = Message(username=username, room_id=room_id, content=message_content)
    db.session.add(new_message)
    db.session.commit()

    return redirect(url_for('chat', room_id=room_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('user_page'))
        else:
            return render_template('index.html', error='Nome de usuário ou senha incorretos. Tente novamente ou crie um novo.')

    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_repeat = request.form.get('password_repeat')

        if password != password_repeat:
            return render_template('signup.html', user_exists_error='As senhas não coincidem.')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', user_exists_error='Nome de usuário já existe. Por favor, escolha outro.')

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = username
        return redirect(url_for('user_page'))

    return render_template('signup.html', user_exists_error=None)


@app.route('/user_page', methods=['GET', 'POST'])
def user_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Verifica se há solicitação para fechar a sala
    close_room_id = request.args.get('close_room')
    if close_room_id:
        # Remove todas as mensagens associadas à sala fechada
        Message.query.filter_by(room_id=close_room_id).delete()
        db.session.commit()
        return redirect(url_for('user_page'))

    return render_template('user_page.html', username=username)


@app.route('/room', methods=['GET', 'POST'])
def room():
    if request.method == 'POST':
        sala_nome = request.form.get('sala')

        if sala_nome:
            # Criar uma nova sala e redirecionar para ela
            room_id = str(uuid.uuid4())
            chat_rooms[room_id] = []

            new_message = Message(username=session ['username'], room_id=room_id, content= "Sala Criada.")
            new_room = Message(room_id=room_id, username=session['username'], content='Sala criada.')
            db.session.add(new_room)
            db.session.commit()

            session.modified=True 
            return redirect(url_for('chat', room_id=room_id))

    return render_template('room.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
