from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import database  # Import the database module

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    metadata = {
        'name': request.form.get('name', 'Unknown'),
        'location': request.form.get('location', 'Unknown'),
        'author': request.form.get('author', 'Unknown'),
        'date': request.form.get('date', 'Unknown'),
        'source': request.form.get('source', 'Unknown')
    }

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Connect to the database
        connection = database.create_server_connection("localhost", "root", "password")

        # Save document metadata and get document ID
        doc_id = database.save_document_and_metadata(connection,file_path, metadata)

        # Process the document text and store word occurrences
        database.process_text(connection, doc_id, file_path)

        # Close the database connection
        connection.close()
        
        return jsonify({"message": "File uploaded successfully", "document_id": doc_id}), 200

    return jsonify({"message": "Unknown error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
