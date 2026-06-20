import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.secret_key = "cyber_ops_secret_key"

# Initialisation de SocketIO pour le temps réel global
socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

posts_db = [
    {
        "id": "init-1",
        "type": "text",
        "filename": None,
        "description": "Système Réseau Synchrone Actif. Support LaTeX : $E=mc^2$",
        "avatar_seed": "ops"
    }
]

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('z.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts_db[::-1])

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ÉVÉNEMENTS WEBSOCKET EN TEMPS RÉEL ---

@socketio.on('new_post')
def handle_new_post(data):
    # Réception du texte envoyé en temps réel
    description = data.get('description', '')
    
    if not description.strip():
        return

    new_post = {
        "id": str(uuid.uuid4())[:8],
        "type": "text",
        "filename": None, # Pour les fichiers bruts via WS, HTTP est préférable, restons simples sur le texte/LaTeX immédiat
        "description": description,
        "avatar_seed": str(uuid.uuid4())[:4]
    }
    posts_db.append(new_post)
    
    # On envoie le post à TOUT LE MONDE instantanément
    emit('broadcast_post', new_post, broadcast=True)

@socketio.on('delete_post')
def handle_delete(data):
    global posts_db
    post_id = data.get('id')
    posts_db = [p for p in posts_db if p['id'] != post_id]
    # On ordonne à TOUS les navigateurs de supprimer ce post de leur écran
    emit('broadcast_delete', {"id": post_id}, broadcast=True)

@socketio.on('edit_post')
def handle_edit(data):
    post_id = data.get('id')
    new_text = data.get('description')
    
    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post:
        post['description'] = new_text
        # On met à jour l'écran de TOUT LE MONDE en direct
        emit('broadcast_edit', {"id": post_id, "description": new_text}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
