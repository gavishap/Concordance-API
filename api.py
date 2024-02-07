from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import re
import logging
import database  # Import the database module
import document
import word as word_function
DATABASE_NAME = "textretrivalsystem"
app = Flask(__name__)
from flask_cors import CORS

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print("Created upload folder")

# get all text from document
def file_content(file_path):
    arr = []
    try:
        with open(file_path, 'r',encoding='utf-8') as file:
            for line in file:
                words = line.split()
                arr.extend(words)
            return arr
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return None


    
# get all expressions
@app.route("/documents_list",methods=['GET'])
def fetch_all_documents():
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    res = []
    filename = request.args.get('filename')
    if filename:
        file_path = "./uploads/"+filename+".txt"
        res = file_content(file_path)
    
    else:
        res = document.fetch_all_documents(connection)
    
    return jsonify(res), 200

@app.route('/upload_document', methods=['POST'])
def document_upload():
    print("Received upload request")
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
    print(f"Metadata received: {metadata}")

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"File saved at {file_path}")

        # Connect to the database
        connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
        print("Connected to the database")

        # Save document metadata and get document ID
        doc_id = document.document_save_and_metadata(connection,file_path, metadata)
        print(f"Document ID received: {doc_id}")

        # Process the document text and store word occurrences
        database.text_processing(connection, doc_id, file_path)
        print("Processed the document text and stored word occurrences")

        # Close the database connection
        connection.close()
        print("Closed the database connection")
        
        return jsonify({"message": "File uploaded successfully", "document_id": doc_id}), 200

    logging.error("Unknown error occurred")
    return jsonify({"message": "Unknown error"}), 500



@app.route('/context', methods=['GET'])
def fetch_word_context():
    print("Received word context request")
    word = request.args.get('word')
    print(f"Request Params: {request.args}")
    if not word:
        print("Word parameter is missing in request")
        return jsonify({"error": "Word parameter is required"}), 400
    # Replace this line in your Flask endpoints
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    doc_id = request.args.get('doc_id')
    paragraph = request.args.get('paragraph')
    sentence = request.args.get('sentence')
    line_number = request.args.get('lineNumber')
    line_range = request.args.get('lineRange')
    print(f"Filters received: word={word}, doc_id={doc_id}, paragraph={paragraph}, sentence={sentence}, line_number={line_number}, line_range={line_range}")
    # Call a new function to get word context with filters
    contexts = word_function.retrieve_word_context(connection, word, doc_id, paragraph, sentence, line_number, line_range)
    response = []
    for context in contexts:
        word, sentence_no, para_no, doc_name = context
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc_name + '.txt')
        context_paragraph = database.get_surrounding_sentences(file_path, sentence_no, para_no)
        context_dict = {
            'word': word,
            'sentence_no': int(sentence_no),
            'paragraph_no': int(para_no),
            'doc_name': doc_name,
            'context_paragraph': context_paragraph
        }
        
        response.append(context_dict)
        
    response.sort(key=lambda x: (x['paragraph_no'], x['sentence_no']))
    print(f"Received contexts: {response}")
    return jsonify(response)


# 
@app.route('/word_group', methods=['POST'])
def save_group():
    data = request.json
    
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    result = word_function.word_group_creation(connection,(data['name'],))
    
    if result:
        return jsonify({"message": "Group saved successfully !!!"}), 200
    else:
        return jsonify({"message": "An error occured while saving group "}), 500


@app.route('/word_group/new_word', methods=['POST'])
def save_word_to_group():
    data = request.json
    
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    result = word_function.save_word_to_group_in_database(connection,(data['group_id'],data['word']))
    
    if result:
        return jsonify({"message": "Word saved to group successfully !!!"}), 200
    else:
        return jsonify({"message": "An error occured while saving word to  group "}), 500
    


# save expression to db
@app.route('/decleration', methods=['POST'])
def save_decleration():
    data = request.json
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    result = database.decleration_creation(connection,data['decleration'],data['words_decleration'])
    
    if result:
        return jsonify({"message": "Expression saved successfully !!!"}), 200
    else:
        return jsonify({"message": "An error occured while saving expression "}), 500



@app.route('/words', methods=['GET'])
def fetch_words():
    print("Received words request")
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    # Fetch filters from request arguments
    doc_id = request.args.get('doc_id')
    starting_letter = request.args.get('startingLetter')
    paragraph = request.args.get('paragraph')
    sentence = request.args.get('sentence')
    line_number = request.args.get('lineNumber')
    line_range = request.args.get('lineRange')
    print(f"Filters received: doc_id={doc_id}, starting_letter={starting_letter}, paragraph={paragraph}, sentence={sentence}, line_number={line_number}, line_range={line_range}")
    # Call a new function to get filtered words
    words = word_function.retrieve_filtered_words(connection, doc_id, starting_letter, paragraph, sentence, line_number, line_range)
    print(f"Received words: {words}")
    response = []
    for word in words:
        response.append(word[0])
    return jsonify(response)


# endpoint to generate statistics
@app.route("/statistics",methods=['GET'])
def statistics():
    file_path = request.args.get('filename')
    frequency = request.args.get('frequency')
    
    if not frequency:
        frequency = 10
    else:
        frequency = int(frequency)
    
    if not file_path:
        return jsonify({'message': 'no file received'}),400
    
    file_path = "./uploads/"+file_path+'.txt'
    
    try:
        with open(file_path, 'r',encoding='utf-8') as file:
            # Read the entire content of the file
            content = file.read()

            # Count the number of paragraphs (assumed to be separated by empty lines)
            paragraphs = re.split('\n+', content)
            num_paragraphs = len(paragraphs)

            # Count the number of sentences (assumed to be separated by '.', '!', or '?')
            sentences = [sentence.strip() for sentence in content.split('.') if sentence.strip()]
            sentences += [sentence.strip() for sentence in content.split('!') if sentence.strip()]
            sentences += [sentence.strip() for sentence in content.split('?') if sentence.strip()]
            num_sentences = len(sentences)

            # Count the number of words
            words = content.split()
            num_words = len(words)
            
            # get 10 most frequent words
            get_most_frequent_words = database.get_frequent_words(file_path,frequency)
            
            sentence_results, paragraph_results,total_letter_stats = word_function.count_words_and_characters(file_path)
            

            # Count the number of letters
            num_letters = sum(len(word) for word in words)
            
             # stats response
            statistics_data = {
                'paragraphs': num_paragraphs,
                'sentences': num_sentences,
                'words': num_words,
                'letters': num_letters
            }
            
            response = {
                'stats': statistics_data,
                'frequency': get_most_frequent_words,
                'sentence': sentence_results,
                'paragraph': paragraph_results,
                'total_letters_counts': total_letter_stats
            }

            # Print the results
            return jsonify(response), 200

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return jsonify({'message': 'Error processing file'}),400


# data mining
@app.route("/data_mining",methods=['GET'])
def data_mining():
    file_path = request.args.get('filename')
    if not file_path:
        return jsonify({'message': 'no file received'}),400
    
    file_path = "./uploads/"+file_path+'.txt'
    arr = database.mining(file_path)
    
    return jsonify(arr), 200
        


# get all expressions
@app.route("/declarations",methods=['GET'])
def fetch_all_declarations():
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    res = database.fetch_all_declarations(connection)
    
    return jsonify(res), 200



@app.route("/word_group",methods=['GET'])
def fetch_all_groups():
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    res = word_function.fetch_all_groups(connection)
    
    return jsonify(res), 200

# get all words of a particular group_id
@app.route("/word_group/words_list",methods=['GET'])
def fetch_all_words_groups():
    connection = database.connection_to_database("localhost", "root", "", DATABASE_NAME)
    groupe_id = request.args.get('group_id')
    res = word_function.fetch_all_words_in_group(connection,groupe_id)
    
    return jsonify(res), 200




if __name__ == "__main__":
    logging.basicConfig(level=print)
    app.run(debug=True)