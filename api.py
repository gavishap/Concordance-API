from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
import database  # Import the database module
DATABASE_NAME = "concordance"
app = Flask(__name__)
from flask_cors import CORS

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    logging.info("Created upload folder")


@app.route('/upload', methods=['POST'])
def upload_document():
    logging.info("Received upload request")
    if 'file' not in request.files:
        logging.error("No file part in request")
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file in request")
        return jsonify({"message": "No selected file"}), 400

    metadata = {
        'name': request.form.get('name', 'Unknown'),
        'location': request.form.get('location', 'Unknown'),
        'author': request.form.get('author', 'Unknown'),
        'date': request.form.get('date', 'Unknown'),
        'source': request.form.get('source', 'Unknown')
    }
    logging.info(f"Metadata received: {metadata}")

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logging.info(f"File saved at {file_path}")

        # Connect to the database
        connection = database.create_server_connection("localhost", "root", "password", DATABASE_NAME)
        logging.info("Connected to the database")

        # Save document metadata and get document ID
        doc_id = database.save_document_and_metadata(connection,file_path, metadata)
        logging.info(f"Document ID received: {doc_id}")

        # Process the document text and store word occurrences
        database.process_text(connection, doc_id, file_path)
        logging.info("Processed the document text and stored word occurrences")

        # Close the database connection
        connection.close()
        logging.info("Closed the database connection")
        
        return jsonify({"message": "File uploaded successfully", "document_id": doc_id}), 200

    logging.error("Unknown error occurred")
    return jsonify({"message": "Unknown error"}), 500

@app.route('/words', methods=['GET'])
def get_words():
    print("Received words request")
    connection = database.create_server_connection("localhost", "root", "password", DATABASE_NAME)
    # Fetch filters from request arguments
    doc_id = request.args.get('doc_id')
    starting_letter = request.args.get('startingLetter')
    paragraph = request.args.get('paragraph')
    sentence = request.args.get('sentence')
    line_number = request.args.get('lineNumber')
    line_range = request.args.get('lineRange')
    print(f"Filters received: doc_id={doc_id}, starting_letter={starting_letter}, paragraph={paragraph}, sentence={sentence}, line_number={line_number}, line_range={line_range}")
    # Call a new function to get filtered words
    words = database.get_filtered_words(connection, doc_id, starting_letter, paragraph, sentence, line_number, line_range)
    print(f"Received words: {words}")
    response = []
    for word in words:
        response.append(word[0])
    return jsonify(response)




@app.route('/word-context', methods=['GET'])
def get_word_context():
    print("Received word context request")
    word = request.args.get('word')
    print(f"Request Params: {request.args}")
    if not word:
        print("Word parameter is missing in request")
        return jsonify({"error": "Word parameter is required"}), 400
    # Replace this line in your Flask endpoints
    connection = database.create_server_connection("localhost", "root", "password", DATABASE_NAME)
    doc_id = request.args.get('doc_id')
    paragraph = request.args.get('paragraph')
    sentence = request.args.get('sentence')
    line_number = request.args.get('lineNumber')
    line_range = request.args.get('lineRange')
    print(f"Filters received: word={word}, doc_id={doc_id}, paragraph={paragraph}, sentence={sentence}, line_number={line_number}, line_range={line_range}")
    # Call a new function to get word context with filters
    contexts = database.get_word_contexts(connection, word, doc_id, paragraph, sentence, line_number, line_range)
    response = []
    for context in contexts:
        word, sentence_no, para_no, doc_name = context
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc_name + '.txt')
        context_paragraph = database.get_surrounding_sentences(file_path, sentence_no, para_no)
        context_dict = {
            'word': word,
            'sentence_no': sentence_no,
            'paragraph_no': para_no,
            'doc_name': doc_name,
            'context_paragraph': context_paragraph
        }
        response.append(context_dict)
    print(f"Received contexts: {response}")
    return jsonify(response)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
