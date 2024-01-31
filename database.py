import mysql.connector
from mysql.connector import Error
import os
import re
import nltk
import logging
nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize
# Global database name
DATABASE_NAME = "concordance"
logging.basicConfig(filename='database.log', level=logging.DEBUG)
def create_server_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name  # Add this line
        )
        print("MySQL Database connection successful")
        logging.info("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")

    return connection

def create_database(connection, db_name):
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created successfully.")
        logging.info(f"Database '{db_name}' created successfully.")
        
        cursor.execute(f"USE {db_name}")  # Switch to the new database

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Documents (
            doc_id INTEGER AUTO_INCREMENT PRIMARY KEY, 
            name TEXT,
            location TEXT,
            author TEXT,
            date DATE,
            source TEXT  
        );
        """)
        print("Table Documents created successfully")
        logging.info("Table Documents created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Words (
        word_id INTEGER AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(255) UNIQUE
        );
        """)
        print("Table Words created successfully")
        logging.info("Table Words created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS WordOccurrences (
        doc_id INTEGER,
        word_id INTEGER,
        sentence_no INTEGER, 
        para_no INTEGER,
        word_position INTEGER,
        PRIMARY KEY (doc_id, word_id, sentence_no, word_position),
        FOREIGN KEY (doc_id) REFERENCES Documents(doc_id),
        FOREIGN KEY (word_id) REFERENCES Words(word_id)
        );
        """)
        print("Table WordOccurrences created successfully")
        logging.info("Table WordOccurrences created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS WordGroups (
            group_id INTEGER PRIMARY KEY,
            name TEXT 
        );
        """)
        print("Table WordGroups created successfully")
        logging.info("Table WordGroups created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS WordGroupAssociations (
            word_id INTEGER,
            group_id INTEGER,
            PRIMARY KEY (word_id, group_id),
            FOREIGN KEY (word_id) REFERENCES Words(word_id),
            FOREIGN KEY (group_id) REFERENCES WordGroups(group_id)
        );
        """)
        print("Table WordGroupAssociations created successfully")
        logging.info("Table WordGroupAssociations created successfully")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Expressions (
            expr_id INTEGER PRIMARY KEY,
            expression TEXT
        );
        """)
        print("Table Expressions created successfully")
        logging.info("Table Expressions created successfully")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")




def execute_query(connection, query, params=None):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        print("Query successful")
        logging.info("Query successful")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")
    finally:
        if cursor:
            cursor.close()


def read_query(connection, query, params=None):
    result = None
    cursor = None
    try:
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")
    finally:
        if cursor :
            cursor.close()
    return result







def upload_document(connection, file_path, metadata):
    # Check if the file exists
    if not os.path.isfile(file_path):
        print("File not found.")
        logging.error("File not found.")
        return
    
    # Read the file and extract text (assuming the file is not too large to fit in memory)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        logging.error(f"Error reading file: {e}")
        return
    
    # Prepare the metadata
    name = metadata.get('name', 'Unknown')
    location = metadata.get('location', 'Unknown')
    author = metadata.get('author', 'Unknown')
    date = metadata.get('date', '0000-00-00')  # Default date in case none is provided
    source = metadata.get('source', 'Unknown')

    # Prepare the SQL query to insert metadata
    insert_query = """
    INSERT INTO Documents (name, location, author, date, source)
    VALUES (%s, %s, %s, %s, %s);
    """
    
    # Execute the query to insert the document metadata
    execute_query(connection, insert_query, (name, location, author, date, source))

def save_document_and_metadata(connection,file_path, metadata):
    # Create the database if it doesn't exist
    create_database(connection, DATABASE_NAME)
    try:
        upload_document(connection, file_path, metadata)
        doc_id_query = "SELECT LAST_INSERT_ID();"
        doc_id_result = read_query(connection,doc_id_query)
        doc_id = doc_id_result[0][0] if doc_id_result else None
    except Exception as e:
        print(f"Error saving document and metadata: {e}")
        logging.error(f"Error saving document and metadata: {e}")
        return None
    return doc_id
   




def process_text(connection, document_id, file_path):
    # Read the file and extract text
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        logging.error(f"Error reading file: {e}")
        return

    # Split the text into paragraphs
    paragraphs = re.split('\n+', text_content)

    for para_no, paragraph in enumerate(paragraphs, start=1):
        # Tokenize the paragraph into sentences
        sentences = sent_tokenize(paragraph)

        for sentence_no, sentence in enumerate(sentences, start=1):
            # Tokenize the sentence into words
            words = word_tokenize(sentence.lower())

            for word_position, word in enumerate(words, start=1):
                # Skip non-alphabetic words
                if not word.isalpha():
                    continue

                # Insert the word into the Words table
                insert_word_query = """
                INSERT INTO Words (word)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE word_id=LAST_INSERT_ID(word_id);
                """
                execute_query(connection,insert_word_query, (word,))

                # Fetch the word_id of the inserted/selected word
                word_id_result = read_query(connection,"SELECT LAST_INSERT_ID();", [])
                if word_id_result and len(word_id_result) > 0:
                    word_id = word_id_result[0][0]

                    # Insert the word occurrence
                    insert_occurrence_query = """
                    INSERT INTO WordOccurrences (doc_id, word_id, sentence_no, para_no, word_position)
                    VALUES (%s, %s, %s, %s, %s);
                    """
                    execute_query(connection,insert_occurrence_query, (document_id, word_id, sentence_no, para_no, word_position))
                else:
                    # Handle the case where word_id is not successfully retrieved
                    print(f"Failed to retrieve word_id for word: {word}")
                    logging.error(f"Failed to retrieve word_id for word: {word}")


        # Increment sentence and paragraph numbers
        sentence_no += 1
        if "\n\n" in sentence:
            para_no += 1

    print(f"Processed and stored words from document {document_id}")
    logging.info(f"Processed and stored words from document {document_id}")


def find_word_occurrences(connection, word):
    # SQL query to find word occurrences along with context information
    query = """
    SELECT d.name, d.author, wo.sentence_no, wo.para_no, wo.chapter_no
    FROM Words w
    JOIN WordOccurrences wo ON w.word_id = wo.word_id
    JOIN Documents d ON wo.doc_id = d.doc_id
    WHERE w.word = %s;
    """

    # Execute the query
    occurrences = read_query(connection, query, (word,))

    if not occurrences:
        print(f"No occurrences found for the word: {word}")
        logging.info(f"No occurrences found for the word: {word}")
        return []

    # Print or return the list of occurrences
    for occurrence in occurrences:
        print(f"Document: {occurrence[0]}, Author: {occurrence[1]}, Sentence: {occurrence[2]}, Paragraph: {occurrence[3]}, Chapter: {occurrence[4]}")

    return occurrences


def create_word_group(connection, group_name):
    # SQL query to insert a new word group
    insert_query = """
    INSERT INTO WordGroups (name)
    VALUES (%s);
    """

    # Execute the query
    try:
        execute_query(connection, insert_query, (group_name,))
        print(f"Word group '{group_name}' created successfully.")
        logging.info(f"Word group '{group_name}' created successfully.")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")


# Function to add words to a word group
def add_word_to_group(connection, word, group_name):
    # Find the word_id
    word_id_query = "SELECT word_id FROM Words WHERE word = %s;"
    word_id_result = read_query(connection, word_id_query, (word,))
    word_id = word_id_result[0][0] if word_id_result else None

    # Find the group_id
    group_id_query = "SELECT group_id FROM WordGroups WHERE name = %s;"
    group_id_result = read_query(connection, group_id_query, (group_name,))
    group_id = group_id_result[0][0] if group_id_result else None

    if word_id and group_id:
        # Link the word to the group
        insert_query = """
        INSERT INTO WordGroupAssociations (word_id, group_id)
        VALUES (%s, %s);
        """
        execute_query(connection, insert_query, (word_id, group_id))
        print(f"Word '{word}' added to group '{group_name}' successfully.")
        logging.info(f"Word '{word}' added to group '{group_name}' successfully.")
    else:
        print("Word or group not found.")
        logging.error("Word or group not found.")

# Function to create a new expression
def create_expression(connection, expression):
    insert_query = """
    INSERT INTO Expressions (expression)
    VALUES (%s);
    """
    execute_query(connection, insert_query, (expression,))
    print(f"Expression '{expression}' created successfully.")
    logging.info(f"Expression '{expression}' created successfully.")

def get_document_statistics(connection, document_id):
    # Query to count the total number of word occurrences in the document
    total_words_query = """
    SELECT COUNT(*)
    FROM WordOccurrences
    WHERE doc_id = %s;
    """

    # Query to count the number of unique words in the document
    unique_words_query = """
    SELECT COUNT(DISTINCT word_id)
    FROM WordOccurrences
    WHERE doc_id = %s;
    """

    # Query to get the frequency of each word in the document
    word_frequency_query = """
    SELECT w.word, COUNT(*)
    FROM WordOccurrences wo
    JOIN Words w ON wo.word_id = w.word_id
    WHERE wo.doc_id = %s
    GROUP BY w.word
    ORDER BY COUNT(*) DESC;
    """

    try:
        # Execute the total words query
        total_words = read_query(connection, total_words_query, (document_id,))[0][0]

        # Execute the unique words query
        unique_words = read_query(connection, unique_words_query, (document_id,))[0][0]

        # Execute the word frequency query
        word_frequencies = read_query(connection, word_frequency_query, (document_id,))

        # Print the statistics
        print(f"Total words in document {document_id}: {total_words}")
        logging.info(f"Total words in document {document_id}: {total_words}")
        print(f"Unique words in document {document_id}: {unique_words}")
        logging.info(f"Unique words in document {document_id}: {unique_words}")
        print(f"Word frequencies in document {document_id}:")
        logging.info(f"Word frequencies in document {document_id}:")
        for word, count in word_frequencies:
            print(f"    {word}: {count}")
            logging.info(f"    {word}: {count}")

        return total_words, unique_words, word_frequencies

    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")
        return None

def get_words(connection, doc_id=None):
    query = "SELECT DISTINCT word FROM Words"
    if doc_id:
        query += " JOIN WordOccurrences ON Words.word_id = WordOccurrences.word_id WHERE WordOccurrences.doc_id = %s"
        return read_query(connection, query, [doc_id])
    else:
        return read_query(connection, query)



def get_word_context(connection, word, doc_id=None):
    query = """
    SELECT d.name, d.author, wo.sentence_no, wo.para_no
    FROM Words
    JOIN WordOccurrences wo ON Words.word_id = wo.word_id
    JOIN Documents d ON wo.doc_id = d.doc_id
    WHERE Words.word = %s
    """
    params = [word]
    if doc_id:
        query += " AND wo.doc_id = %s"
        params.append(doc_id)
    return read_query(connection, query, params)

# Data Mining - simplified version of the Apriori algorithm to identify pairs of words that frequently occur together
def find_frequent_word_pairs(connection, document_id, min_frequency):
    # Fetch word occurrences for the document
    query = """
    SELECT w.word, wo.sentence_no
    FROM WordOccurrences wo
    JOIN Words w ON wo.word_id = w.word_id
    WHERE wo.doc_id = %s
    ORDER BY wo.sentence_no, wo.word_id;
    """
    word_occurrences = read_query(connection, query, (document_id,))

    # Count pairs of words in the same sentence
    word_pairs = {}
    for i in range(len(word_occurrences) - 1):
        current_word, current_sentence = word_occurrences[i]
        next_word, next_sentence = word_occurrences[i + 1]

        # Check if the next word is in the same sentence
        if current_sentence == next_sentence:
            pair = (current_word, next_word)
            word_pairs[pair] = word_pairs.get(pair, 0) + 1

    # Filter pairs by minimum frequency
    frequent_pairs = {pair: count for pair, count in word_pairs.items() if count >= min_frequency}

    # Return the frequent pairs
    return frequent_pairs

def get_filtered_words(connection, doc_id=None, starting_letter=None, paragraph=None, sentence=None, line_number=None, line_range=None):
    print("get_filtered_words called with parameters:", locals())
    query = """
    SELECT DISTINCT Words.word
    FROM Words
    JOIN WordOccurrences ON Words.word_id = WordOccurrences.word_id
    """
    params = []

    if doc_id:
        query += " JOIN Documents ON WordOccurrences.doc_id = Documents.doc_id WHERE Documents.doc_id = %s"
        params.append(doc_id)
        print("Filtering by doc_id:", doc_id)

    if starting_letter:
        query += " AND Words.word LIKE %s"
        params.append(starting_letter + '%')
        print("Filtering by starting_letter:", starting_letter)

    if paragraph:
        query += " AND WordOccurrences.para_no = %s"
        params.append(paragraph)
        print("Filtering by paragraph:", paragraph)

    if sentence:
        query += " AND WordOccurrences.sentence_no = %s"
        params.append(sentence)
        print("Filtering by sentence:", sentence)

    if line_number:
        # Assuming line_number corresponds to a specific word_position
        query += " AND WordOccurrences.word_position = %s"
        params.append(line_number)
        print("Filtering by line_number:", line_number)

    if line_range:
        # Assuming line_range is a string like '5-10'
        start, end = line_range.split('-')
        query += " AND WordOccurrences.word_position BETWEEN %s AND %s"
        params.extend([start, end])
        print("Filtering by line_range:", line_range)

    print("Executing query:", query)
    print("With parameters:", params)
    return read_query(connection, query, params)

def get_word_contexts(connection, word, doc_id=None, paragraph=None, sentence=None, line_number=None, line_range=None):
    print("get_word_contexts called with parameters:", locals())
    query = """
    SELECT Words.word, WordOccurrences.sentence_no, WordOccurrences.para_no, Documents.name
    FROM Words
    JOIN WordOccurrences ON Words.word_id = WordOccurrences.word_id
    JOIN Documents ON WordOccurrences.doc_id = Documents.doc_id
    WHERE Words.word = %s
    """
    params = [word]
    print("Filtering by word:", word)

    if doc_id:
        query += " AND Documents.doc_id = %s"
        params.append(doc_id)
        print("Filtering by doc_id:", doc_id)

    if paragraph:
        query += " AND WordOccurrences.para_no = %s"
        params.append(paragraph)
        print("Filtering by paragraph:", paragraph)

    if sentence:
        query += " AND WordOccurrences.sentence_no = %s"
        params.append(sentence)
        print("Filtering by sentence:", sentence)

    if line_number:
        query += " AND WordOccurrences.word_position = %s"
        params.append(line_number)
        print("Filtering by line_number:", line_number)

    if line_range:
        start, end = line_range.split('-')
        query += " AND WordOccurrences.word_position BETWEEN %s AND %s"
        params.extend([start, end])
        print("Filtering by line_range:", line_range)

    print("Executing query:", query)
    print("With parameters:", params)
    return read_query(connection, query, params)


def get_surrounding_sentences(file_path, sentence_no, para_no):
    # Read the file and tokenize the text into paragraphs and then sentences
    with open(file_path, 'r') as file:
        text = file.read()
    paragraphs = text.split('\n\n')
    
    # Ensure para_no is within the range of paragraphs
    para_no = max(0, min(para_no - 1, len(paragraphs) - 1))
    
    # Tokenize the selected paragraph into sentences
    sentences = sent_tokenize(paragraphs[para_no])
    
    # Adjust sentence_no to be zero-based and within the range of sentences in the paragraph
    sentence_no = max(0, min(sentence_no - 1, len(sentences) - 1))
    
    # Initialize context sentences list
    context_sentences = []
    
    # If the target sentence is the first in its paragraph, include sentences from the previous paragraph
    if sentence_no == 0 and para_no > 0:
        previous_paragraph_sentences = sent_tokenize(paragraphs[para_no - 1])
        context_sentences.extend(previous_paragraph_sentences[-2:])
    
    # Calculate the range of sentences to include from the current paragraph
    start_index = max(0, sentence_no - 2)
    end_index = min(len(sentences), sentence_no + 3)  # +3 to include the target, and up to 2 sentences after
    
    # Extend the context sentences list with sentences from the current paragraph
    context_sentences.extend(sentences[start_index:end_index])
    
    # If the target sentence is the last in its paragraph, include sentences from the next paragraph
    if sentence_no == len(sentences) - 1 and para_no < len(paragraphs) - 1:
        next_paragraph_sentences = sent_tokenize(paragraphs[para_no + 1])
        context_sentences.extend(next_paragraph_sentences[:2])
    
    # Join the context sentences to form the context paragraph
    context_paragraph = ' '.join(context_sentences)
    
    return context_paragraph
# Replace with your MySQL server information
host = "localhost"
user = "root"  # It's recommended to use a less privileged user in production
password = "password"  # Enter your MySQL root password here

