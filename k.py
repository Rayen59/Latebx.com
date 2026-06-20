import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.secret_key = "cyber_ops_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")

# Base de données temporaire en mémoire
posts_db = [
    {
        "id": "init-1",
        "type": "text",
        "description": "Système Réseau Synchrone Sécurisé Actif. Chaque nœud contrôle ses propres transmissions.",
        "avatar_seed": "ops",
        "user_token": "system"  # Protégé
    }
]

@app.route('/')
def index():
    return render_template('z.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    # On renvoie les posts sans le token secret pour éviter qu'un hacker le lise dans l'API
    public_posts = []
    for p in posts_db:
        public_posts.append({
            "id": p["id"],
            "type": p["type"],
            "description": p["description"],
            "avatar_seed": p["avatar_seed"]
        })
    return jsonify(public_posts[::-1])

# --- COMMUNICATIONS SÉCURISÉES VIA WEBSOCKET ---

@socketio.on('new_post')
def handle_new_post(data):
    description = data.get('description', '')
    user_token = data.get('user_token') # Clé unique de l'utilisateur
    
    if not description.strip() or not user_token:
        return

    new_post = {
        "id": str(uuid.uuid4())[:8],
        "type": "text",
        "description": description,
        "avatar_seed": user_token[:4], # L'avatar dépend de son token unique
        "user_token": user_token # Sauvegardé secrètement sur le serveur
    }
    posts_db.append(new_post)
    
    # On diffuse le post à tout le monde (sans le user_token privé)
    broadcast_data = {
        "id": new_post["id"],
        "type": new_post["type"],
        "description": new_post["description"],
        "avatar_seed": new_post["avatar_seed"]
    }
    emit('broadcast_post', broadcast_data, broadcast=True)

@socketio.on('delete_post')
def handle_delete(data):
    global posts_db
    post_id = data.get('id')
    user_token = data.get('user_token')
    
    # RECHERCHE ET VÉRIFICATION DE SÉCURITÉ CRITIQUE
    post = next((p for p in posts_db if p['id'] == post_id), None)
    
    if post and post['user_token'] == user_token:
        posts_db = [p for p in posts_db if p['id'] != post_id]
        emit('broadcast_delete', {"id": post_id}, broadcast=True)
    else:
        # Tentative de suppression frauduleuse bloquée
        emit('security_alert', {"error": "Action non autorisée sur ce nœud."}, room=request.sid)

@socketio.on('edit_post')
def handle_edit(data):
    post_id = data.get('id')
    new_text = data.get('description')
    user_token = data.get('user_token')
    
    # VÉRIFICATION DE SÉCURITÉ CRITIQUE
    post = next((p for p in posts_db if p['id'] == post_id), None)
    
    if post and post['user_token'] == user_token:
        post['description'] = new_text
        emit('broadcast_edit', {"id": post_id, "description": new_text}, broadcast=True)
    else:
        emit('security_alert', {"error": "Modification interdite. Signature invalide."}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
