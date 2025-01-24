import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError

load_dotenv()

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databasetest.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

# Initialisation des extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Vue de connexion
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modèles de base de données
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    messages = db.relationship('Discussion', backref='conversation', lazy=True)

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)

# Formulaires Flask-WTF
class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    email = StringField(validators=[
        InputRequired(), Length(min=6, max=50)], render_kw={"placeholder": "Email"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

# Routes Flask
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat_interface'))  # Rediriger vers la page de chat si déjà connecté
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            # Récupérer la première conversation de l'utilisateur
            first_conversation = Conversation.query.filter_by(user_id=user.id).first()
            if first_conversation:
                app.logger.debug(f"Redirecting to chat_conversation with conversation_id={first_conversation.id}")
                return redirect(url_for('chat_conversation', conversation_id=first_conversation.id))
            else:
                flash('No conversations found for this user.', 'warning')
                return redirect(url_for('chat_interface'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/chat/interface')
@login_required
def chat_interface():
    conversations = Conversation.query.filter_by(user_id=current_user.id).all()
    if conversations:
        first_conversation = conversations[0]
        return render_template('chat-conversation.html', conversations=conversations, conversation=first_conversation)
    else:
        flash('No conversations found for this user.', 'warning')
        return render_template('conversations.html', conversations=conversations)

@app.route('/chat/conversation/<int:conversation_id>')
@login_required
def chat_conversation(conversation_id):
    app.logger.debug(f"Loading chat_conversation with conversation_id={conversation_id}")
    conversation = Conversation.query.get_or_404(conversation_id)
    conversations = Conversation.query.filter_by(user_id=current_user.id).all()
    return render_template('chat-conversation.html', conversation=conversation, conversations=conversations)

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    try:
        from chat import chatbot  # Importation différée pour éviter les importations circulaires

        # Get message and conversation ID
        message = str(request.form['messageText'])
        conversation_id = request.form.get('conversationId', type=int)

        app.logger.debug(f"Received message: {message}")

        # If conversation does not exist, create a new one
        if not conversation_id:
            title = ' '.join(message.split()[:3])
            new_conversation = Conversation(user_id=current_user.id, title=title)
            db.session.add(new_conversation)
            db.session.commit()
            conversation_id = new_conversation.id

        # Save user message
        user_message = Discussion(conversation_id=conversation_id, content=message, is_user=True)
        db.session.add(user_message)
        db.session.commit()

        # Generate chatbot response
        bot_response = chatbot(message)
        if not bot_response:
            bot_response = "Sorry, the system encountered an issue. Please try again later."

        # Save chatbot response
        bot_message = Discussion(conversation_id=conversation_id, content=bot_response, is_user=False)
        db.session.add(bot_message)
        db.session.commit()

        app.logger.debug(f"Bot response: {bot_response}")
        print("Bot response:", bot_response)

        return jsonify({'status': 'OK', 'answer': bot_response, 'conversationId': conversation_id})

    except Exception as e:
        app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify({'status': 'ERROR', 'answer': f'Sorry, there was an error processing your request: {str(e)}'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)