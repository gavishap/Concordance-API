##Document Processing and Analysis API
#Description
This project is a Flask-based backend system designed for processing, storing, and analyzing textual documents. It provides a RESTful API for uploading documents, storing their metadata in a MySQL database, and analyzing text data. The system tokenizes the text, identifies unique words, and stores word occurrences with detailed context (sentence, paragraph, and position).

#Features
REST API for document upload and processing.
Integration with MySQL for data storage and retrieval.
Text analysis including tokenization and word occurrence tracking.
Advanced queries for word statistics and frequent word pair identification.
#Installation
#Prerequisites
Python 3.x
Flask
MySQL
NLTK (Natural Language Toolkit)
#Setup
Clone the repository:

git clone https://github.com/yourusername/yourrepository.git
#Navigate to the project directory:


#Install required Python packages:
pip install flask mysql-connector-python nltk
#Download NLTK data:

import nltk
nltk.download('punkt')
Usage
#To start the Flask server:

python api.py
Use the /upload endpoint to upload documents. The API expects multipart/form-data with file and metadata (name, location, author, date, source).

#Database Configuration
The database.py script handles database configuration, including creating tables and establishing connections. Ensure MySQL server is running and modify credentials in database.py as needed.

#API Reference
POST /upload: Endpoint for uploading documents and processing text.
#Contributing
Contributions to the project are welcome. Please follow standard coding practices and submit pull requests for any proposed changes.

#License
This project is open-source and available under the MIT License.
