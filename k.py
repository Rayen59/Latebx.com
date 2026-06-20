import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__, template_folder='.')
app.secret_key = "cyber_ops_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Post d'initialisation par défaut
posts_db = [
    {
        "id": "init-1",
        "type": "text",
        "filename": None,
        "description": "Système Opérationnel. Support LaTeX actif. Exemple : $E=mc^2$ ou $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$",
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
        
        if ext in ['.mp4', '.webm', '.mov']:
            post_type = 'video'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            post_type = 'image'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            post_type = 'audio'

    if not filename and not description.strip():
        return jsonify({"error": "Payload vide"}), 400

    new_post = {
        "id": str(uuid.uuid4())[:8],
        "type": post_type,
        "filename": filename,
        "description": description,
        "avatar_seed": str(uuid.uuid4())[:4]
    }
    posts_db.append(new_post)
    return jsonify(new_post)

@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
