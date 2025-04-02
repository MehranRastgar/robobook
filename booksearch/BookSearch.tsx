import React, { useState } from 'react';
import axios from 'axios';

interface Book {
  title: string;
  author: string;
  year: number;
  page_count: number;
  ocaid: string;
  full_text_url: string;
}

const BookSearch: React.FC = () => {
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [year, setYear] = useState('');
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const searchBooks = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (title) params.append('title', title);
      if (author) params.append('author', author);
      if (year) params.append('year', year);
      
      const response = await axios.get(`/api/books/search?${params.toString()}`);
      setBooks(response.data.books);
    } catch (error) {
      setError('Error searching books. Please try again.');
      console.error('Error searching books:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Public Domain Book Search</h1>
      
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="border p-2 rounded"
        />
        <input
          type="text"
          placeholder="Author"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          className="border p-2 rounded"
        />
        <input
          type="number"
          placeholder="Year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
          className="border p-2 rounded"
        />
        <button
          onClick={searchBooks}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-blue-300"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {books.map((book) => (
          <div key={book.ocaid} className="border p-4 rounded shadow hover:shadow-md transition-shadow">
            <h2 className="text-xl font-bold mb-2">{book.title}</h2>
            <p className="text-gray-600">Author: {book.author}</p>
            <p className="text-gray-600">Year: {book.year}</p>
            <p className="text-gray-600">Pages: {book.page_count}</p>
            <a
              href={book.full_text_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-block bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            >
              Read Book
            </a>
          </div>
        ))}
      </div>
      
      {books.length === 0 && !loading && !error && (
        <div className="text-center text-gray-500 mt-8">
          No books found. Try adjusting your search criteria.
        </div>
      )}
    </div>
  );
};

export default BookSearch; 