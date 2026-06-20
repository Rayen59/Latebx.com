import os
import uuid
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='.')
app.secret_key = "cyber_ops_secret_key"

# Configuration robuste pour Render (Force le mode Polling si WebSocket est bloqué)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

posts_db = [
    {
        "id": "init-1",
        "description": "Système Réseau Synchrone RIA Opérationnel. Les commentaires et le support LaTeX sont actifs.",
        "avatar_seed": "ops",
        "user_token": "system",
        "comments": []
    }
]

@app.route('/')
def index():
    return render_template('z.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts_db[::-1])

# --- COMMUNICATIONS SYNCHRONES MONDIALES ---

@socketio.on('new_post')
def handle_new_post(data):
    description = data.get('description', '')
    user_token = data.get('user_token')
    if not description.strip() or not user_token: return

    new_post = {
        "id": str(uuid.uuid4())[:8],
        "description": description,
        "avatar_seed": user_token[:4],
        "user_token": user_token,
        "comments": []
    }
    posts_db.append(new_post)
    emit('broadcast_post', new_post, broadcast=True)

@socketio.on('delete_post')
def handle_delete(data):
    global posts_db
    post_id = data.get('id')
    user_token = data.get('user_token')
    
    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post and post['user_token'] == user_token:
        posts_db = [p for p in posts_db if p['id'] != post_id]
        emit('broadcast_delete', {"id": post_id}, broadcast=True)

@socketio.on('edit_post')
def handle_edit(data):
    post_id = data.get('id')
    new_text = data.get('description')
    user_token = data.get('user_token')
    
    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post and post['user_token'] == user_token:
        post['description'] = new_text
        emit('broadcast_edit', {"id": post_id, "description": new_text}, broadcast=True)

@socketio.on('new_comment')
def handle_new_comment(data):
    post_id = data.get('post_id')
    comment_text = data.get('text', '')
    user_token = data.get('user_token')
    if not comment_text.strip() or not user_token: return

    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post:
        comment_data = {
            "id": str(uuid.uuid4())[:6],
            "text": comment_text,
            "avatar_seed": user_token[:4]
        }
        post['comments'].append(comment_data)
        # On envoie le commentaire à tout le monde instantanément
        emit('broadcast_comment', {"post_id": post_id, "comment": comment_data}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
