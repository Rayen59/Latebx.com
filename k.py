import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, template_folder='.')
app.secret_key = "cyber_ops_secret_key"

# Configuration du dossier de stockage absolu pour Termux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de données temporaire en mémoire
posts_db = [
    {
        "id": "init-1",
        "type": "text",
        "filename": None,
        "description": "System online. LaTeX support active. Try writing $E=mc^2$ or $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$",
        "avatar_seed": "op_alpha"
    }
]

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    # Charge le fichier z.html présent dans le même dossier
    return render_template('z.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    search_query = request.args.get('search', '').lower()
    if search_query:
        filtered = [p for p in posts_db if p['description'] and search_query in p['description'].lower()]
    else:
        filtered = posts_db.copy()
    return jsonify(filtered[::-1])

@app.route('/api/posts', methods=['POST'])
def create_post():
    description = request.form.get('description', '')
    file = request.files.get('media')
    
    post_type = "text"
    filename = None
    
    if file and file.filename != '':
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if ext in ['.mp4', '.webm', '.mov', '.3gp']:
            post_type = 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            post_type = 'image'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac']:
            post_type = 'audio'

    if not filename and not description.strip():
        return jsonify({"error": "Cannot broadcast an empty payload"}), 400

    new_post = {
        "id": str(uuid.uuid4())[:8],
        "type": post_type,
        "filename": filename,
        "description": description,
        "avatar_seed": str(uuid.uuid4())[:4]
    }
    posts_db.append(new_post)
    return jsonify(new_post)

@app.route('/api/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    global posts_db
    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post:
        if post['filename']:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], post['filename']))
            except Exception:
                pass
        posts_db = [p for p in posts_db if p['id'] != post_id]
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/posts/<post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()
    post = next((p for p in posts_db if p['id'] == post_id), None)
    if post:
        post['description'] = data.get('description', post['description'])
        return jsonify(post)
    return jsonify({"error": "Not found"}), 404

@app.route('/uploads/<filename>')
def serve_file(filename):
    response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    response.headers["Accept-Ranges"] = "bytes"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
      
