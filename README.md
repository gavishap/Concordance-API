# Concordance Text Processing and Analysis API

## Description

This project is a Flask-based backend system designed for processing, storing, and analyzing textual documents. It features a RESTful API for uploading documents and storing their metadata in a MySQL database. The system offers functionalities for text analysis, including tokenization and tracking word occurrences, providing insights into document content.

## Features

- **REST API**: Facilitates document upload and processing.
- **MySQL Database Integration**: Manages data storage and retrieval.
- **Text Analysis**: Implements tokenization, tracking word occurrences.
- **Word Statistics**: Generates statistics and identifies frequent word pairs.

## Installation

### Prerequisites

- Python 3.x
- Flask
- MySQL
- NLTK (Natural Language Toolkit)

### Setup Instructions

1. **Clone the Repository**:
   ```bash
   [git clone https://github.com/yourusername/yourrepository.git](https://github.com/gavishap/Concordance-API.git)
   ```

2. **Install Dependencies**:
   ```bash
   pip install flask mysql-connector-python nltk pip install spacy
   ```
2.1 **Install Dependencies**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Set Up MySQL Database**:
   - Ensure MySQL is installed and running.
   - Create a database and user with appropriate privileges.

4. **Run the Flask Application**:
   ```bash
   python api.py
   ```

## Usage

1. **Uploading Documents**: Send a POST request to `/upload` with the document and metadata.
2. **Processing Text**: The API processes the uploaded document, tokenizing the text and storing word occurrences.
3. **Retrieving Data**: Use the API or direct database queries to analyze the text data.

## Contributing

Contributions are welcome! Please read the contributing guide for more information.

## License

[MIT License](LICENSE)
