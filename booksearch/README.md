# Public Domain Book Search

A web application for searching and reading public domain books from the US-PD-Books dataset.

## Features

- Search books by title, author, and year
- View book details including page count and publication year
- Direct links to read books from Internet Archive
- Responsive design with modern UI

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies (if using the React frontend):
```bash
npm install react axios @types/react @types/axios
```

3. Start the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5000` by default.

## API Endpoints

### Search Books
```
GET /api/books/search

Query Parameters:
- title (optional): Search by book title
- author (optional): Search by author name
- year (optional): Search by publication year
- limit (optional): Maximum number of results (default: 10)

Response:
{
    "status": "success",
    "count": number,
    "books": [
        {
            "title": string,
            "author": string,
            "year": number,
            "page_count": number,
            "ocaid": string,
            "full_text_url": string
        }
    ]
}
```

### Get Book Details
```
GET /api/books/<ocaid>

Response:
{
    "status": "success",
    "book": {
        "title": string,
        "author": string,
        "year": number,
        "page_count": number,
        "ocaid": string,
        "full_text_url": string
    }
}
```

## Dataset

This application uses the US-PD-Books dataset from Hugging Face, which contains over 650,000 English books from the Internet Archive that are presumed to be in the public domain in the US.

## Development

The project structure is:
```
booksearch/
├── app.py              # Flask server
├── dataset_loader.py   # Dataset handling
├── BookSearch.tsx      # React frontend
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 