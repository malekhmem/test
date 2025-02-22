import logging
import torch
from flask import Blueprint, render_template, jsonify, request
from model import tokenizer, model, generation_config
from utils import clean_output, log_memory_usage
from flask_login import login_required, current_user
from app import db, User, Conversation, Discussion

chat = Blueprint('chat', __name__)

@chat.route('/interface')
@login_required
def chat_interface():
    user_id = current_user.id
    conversations = Conversation.query.filter_by(user_id=user_id).all()
    return render_template('chat_conversation.html', conversations=conversations)

@chat.route('/load_conversation/<int:conversation_id>')
@login_required
def load_conversation(conversation_id):
    messages = Discussion.query.filter_by(conversation_id=conversation_id).all()
    message_list = [{'content': message.content, 'isUser': message.is_user} for message in messages]
    return jsonify({'status': 'OK', 'messages': message_list})

@chat.route('/save_message', methods=['POST'])
@login_required
def save_message():
    data = request.form
    conversation_id = data.get('conversationId')
    message_text = data.get('messageText')

    if not conversation_id or not message_text:
        return jsonify({'status': 'ERROR', 'message': 'Missing conversation ID or message text'})

    new_message = Discussion(
        conversation_id=conversation_id,
        content=message_text,
        is_user=True  
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({'status': 'OK', 'message': 'Message saved successfully'})

def chat_with_model(input_text):
    log_memory_usage()
    try:
        # Ajouter un prompt personnalisé si nécessaire
        input_str = f"[INST] You are ActiaBot, a friendly coding assistant. {input_text} [/INST]"
        logging.info(f"Input string for generation: {input_str}")
       
        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = tokenizer(input_str, return_tensors="pt").to(device)
        outputs = model.generate(**inputs, generation_config=generation_config)
        raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
       
        # Nettoyage de la sortie
        cleaned_output = clean_output(raw_output.replace(input_str, '').strip())
        logging.info(f"Generated response: {cleaned_output}")
       
        torch.cuda.empty_cache()  # Libérer la mémoire GPU après la génération
        log_memory_usage()
       
        return cleaned_output
    except Exception as e:
        logging.error(f"Error during generation: {e}", exc_info=True)
        return "An error occurred during text generation."