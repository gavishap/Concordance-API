import mysql.connector
from mysql.connector import Error
import os
import re
import nltk
import logging
from collections import Counter
import re
import spacy
nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize
from itertools import combinations
nlp = spacy.load("en_core_web_sm")

# Global database name
DATABASE_NAME = "textretrivalsystem"  # Changed from "concordance"
logging.basicConfig(filename='database.log', level=logging.DEBUG)

def new_database(connection, db_name):

    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created successfully.")
        logging.info(f"Database '{db_name}' created successfully.")
        
        cursor.execute(f"USE {db_name}")  # Switch to the new database

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_list (
            doc_id INTEGER AUTO_INCREMENT PRIMARY KEY, 
            name TEXT,
            location TEXT,
            author TEXT,
            date DATE,
            source TEXT  
        );
        """)
        print("Table document_list created successfully")
        logging.info("Table document_list created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Words (
        word_id INTEGER AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(255) UNIQUE
        );
        """)
        print("Table Words created successfully")
        logging.info("Table Words created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS occurrences (
        doc_id INTEGER,
        word_id INTEGER,
        sentence_no INTEGER, 
        para_no INTEGER,
        word_position INTEGER,
        PRIMARY KEY (doc_id, word_id, sentence_no, word_position),
        FOREIGN KEY (doc_id) REFERENCES document_list(doc_id),
        FOREIGN KEY (word_id) REFERENCES Words(word_id)
        );
        """)
        print("Table occurrences created successfully")
        logging.info("Table occurrences created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups_of_words (
            group_id INTEGER PRIMARY KEY,
            name TEXT 
        );
        """)
        print("Table groups_of_words created successfully")
        logging.info("Table groups_of_words created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_associationed (
            word_id INTEGER,
            group_id INTEGER,
            PRIMARY KEY (word_id, group_id),
            FOREIGN KEY (word_id) REFERENCES Words(word_id),
            FOREIGN KEY (group_id) REFERENCES groups_of_words(group_id)
        );
        """)
        print("Table word_associationed created successfully")
        logging.info("Table word_associationed created successfully")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS declerations (
            decleration_id INTEGER PRIMARY KEY,
            decleration TEXT
        );
        """)
        print("Table declerations created successfully")
        logging.info("Table declerations created successfully")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")

    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created successfully.")
        logging.info(f"Database '{db_name}' created successfully.")
        
        cursor.execute(f"USE {db_name}")  # Switch to the new database

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_list (
            doc_id INTEGER AUTO_INCREMENT PRIMARY KEY, 
            name TEXT,
            location TEXT,
            author TEXT,
            date DATE,
            source TEXT  
        );
        """)
        print("Table document_list created successfully")
        logging.info("Table document_list created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Words (
        word_id INTEGER AUTO_INCREMENT PRIMARY KEY,
        word VARCHAR(255) UNIQUE
        );
        """)
        print("Table Words created successfully")
        logging.info("Table Words created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS occurrences (
        doc_id INTEGER,
        word_id INTEGER,
        sentence_no INTEGER, 
        para_no INTEGER,
        word_position INTEGER,
        PRIMARY KEY (doc_id, word_id, sentence_no, word_position),
        FOREIGN KEY (doc_id) REFERENCES document_list(doc_id),
        FOREIGN KEY (word_id) REFERENCES Words(word_id)
        );
        """)
        print("Table occurrences created successfully")
        logging.info("Table occurrences created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups_of_words (
            group_id INTEGER PRIMARY KEY,
            name TEXT 
        );
        """)
        print("Table groups_of_words created successfully")
        logging.info("Table groups_of_words created successfully")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_associationed (
            word_id INTEGER,
            group_id INTEGER,
            PRIMARY KEY (word_id, group_id),
            FOREIGN KEY (word_id) REFERENCES Words(word_id),
            FOREIGN KEY (group_id) REFERENCES groups_of_words(group_id)
        );
        """)
        print("Table word_associationed created successfully")
        logging.info("Table word_associationed created successfully")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS declerations (
            decleration_id INTEGER PRIMARY KEY,
            decleration TEXT
        );
        """)
        print("Table declerations created successfully")
        logging.info("Table declerations created successfully")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")


def connection_to_database(host_name, user_name, user_password, db_name):
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


def query_reading(connection, query, params=None):
    result = None
    cursor_reading = None
    try:
        cursor_reading = connection.cursor()
        if params:
            cursor_reading.execute(query, params)
        else:
            cursor_reading.execute(query)
        result = cursor_reading.fetchall()
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")
    finally:
        if cursor_reading:
            cursor_reading.close()
    return result


def query_execution(connection, query, params=None):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")
        logging.error(f"Error: '{err}'")
    finally:
        if cursor:
            cursor.close()


def text_processing(connection, document_id, file_path):
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
                query_execution(connection, insert_word_query, (word,))

                # Fetch the word_id of the inserted/selected word
                word_id_result = query_reading(connection, "SELECT LAST_INSERT_ID();", [])
                if word_id_result and len(word_id_result) > 0:
                    word_id = word_id_result[0][0]

                    # Insert the word occurrence
                    insert_occurrence_query = """
                    INSERT INTO occurrences (doc_id, word_id, sentence_no, para_no, word_position)
                    VALUES (%s, %s, %s, %s, %s);
                    """
                    query_execution(connection, insert_occurrence_query, (document_id, word_id, sentence_no, para_no, word_position))
                else:
                    # Handle the case where word_id is not successfully retrieved
                    print(f"Failed to retrieve word_id for word: {word}")
                    logging.error(f"Failed to retrieve word_id for word: {word}")

        # Increment sentence and paragraph numbers
        sentence_no += 1
        if re.search("\n+", sentence):
            para_no += 1

    print(f"Processed and stored words from document {document_id}")
    logging.info(f"Processed and stored words from document {document_id}")


# Function to create a new expression
def decleration_creation(connection, decleration, words_decleration):
    cursor = connection.cursor()
    query_string = "INSERT INTO declerations (decleration, words_decleration) VALUES ('{}','{}')".format(decleration, words_decleration)
    print(query_string)
    cursor.execute(""+ query_string + "")
    connection.commit()
    print("Query successful")
    print(f"Expression '{ decleration, words_decleration}' created successfully.")
    logging.info(f"Expression '{ decleration, words_decleration}' created successfully.")


def get_frequent_words(file_path, num):
    frequent_words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read the entire content of the file
            content = file.read()

            # Split the content into words using regular expression
            words = re.findall(r'\b\w+\b', content.lower())  # Convert to lowercase for case-insensitive counting

            # Define words to exclude from counting
            exclude_words = { 'by', 'with', 'were', 'that', 'as', 'for', 'on', 'is', 'it', 'from', 'at', 'an', 'be', 'which', 'this', 'also', 'are', 'has', 'had', 'have', 'been', 'or', 'not', 'but', 'its', 'their', 'they', 'them', 'we', 'our','the', 'in', 'and', 'of', 'to', 'a', 'us', 'was' 'me', 'my', 'mine', 'us', 'you', 'your', 'he', 'she', 'his', 'her', 'him', 'i', 'we', 'ours', 'ourselves', 'yours', 'their', 'theirs', 'themselves', 'what', 'who', 'whom', 'whose', 'which', 'where', 'yourself', 'yourselves', 'himself', 'herself', 'itself', 'themselves', 'they', 'them', 'when', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'than', 'too', 'very', 'can', 'will', 'just', 'now', 'ain', 'are', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'could', 'has', 'is', 'should', 'was', 'would'}

            # Filter out the excluded words
            filtered_words = [word for word in words if word not in exclude_words]

            # Count the occurrences of each word
            word_counts = Counter(filtered_words)

            # Get the most frequent words and their occurrences
            most_common_words = word_counts.most_common(num)
            for word, count in most_common_words:
                frequent_words.append({"word": word, "count": count})
                
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        
    return frequent_words

def fetch_all_declarations(connection):
    arr = []
    
    try:
        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Execute a SELECT query to fetch all data from the table
        cursor.execute("SELECT * FROM declerations where decleration is not null AND words_decleration is not null")

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        for row in rows:
            arr.append({
                "id": row[0],
                "name": row[1],
                "words": row[2]
            })

    except mysql.connector.Error as error:
        print("Error while fetching data from the MySQL database:", error)

    finally:
        # Close the cursor and the connection
        cursor.close()
        connection.close()
        
    return arr


# Implement data mining
def mining(file_path):
    context = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()
            doc = nlp(text_content)

            for ent in doc.ents:
                context.append({
                    'text': ent.text,
                    'type': ent.label_
                })
    except Exception as e:
        print(f"Error reading file: {e}")
        logging.error(f"Error reading file: {e}")
        return
    
    # Process the text using spaCy
    
    return context
