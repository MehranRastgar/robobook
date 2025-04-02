'use client';

import { useState } from 'react';
import axios from 'axios';

interface BookMetadata {
  title: string;
  author: string;
  isbn: string;
  language: string;
}

interface PDFUploaderProps {
  onUploadSuccess?: (bookId: number) => void;
  onUploadError?: (error: string) => void;
}

const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess, onUploadError }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [isbn, setIsbn] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [fileType, setFileType] = useState<'pdf' | 'txt' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      setFile(null);
      setFileType(null);
      return;
    }

    const fileType = selectedFile.type;
    if (fileType === 'application/pdf') {
      setFileType('pdf');
      setFile(selectedFile);
      setError(null);
    } else if (fileType === 'text/plain' || selectedFile.name.endsWith('.txt')) {
      setFileType('txt');
      setFile(selectedFile);
      setError(null);
    } else {
      setFile(null);
      setFileType(null);
      onUploadError?.('لطفاً یک فایل PDF یا TXT معتبر انتخاب کنید');
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file || !fileType) {
      onUploadError?.('لطفاً یک فایل انتخاب کنید');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('author', author);
      if (isbn) formData.append('isbn', isbn);

      const endpoint = fileType === 'pdf'
        ? '/api/books/import/pdf'
        : '/api/books/import/txt';

      const response = await axios.post(`http://127.0.0.1:5000${endpoint}`, formData);
      onUploadSuccess?.(response.data.book_id);
      
      // Reset form
      setFile(null);
      setTitle('');
      setAuthor('');
      setIsbn('');
      setFileType(null);
    } catch (error) {
      console.error('Error uploading file:', error);
      onUploadError?.(`خطا در آپلود ${fileType === 'pdf' ? 'PDF' : 'TXT'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">آپلود کتاب</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="book-file" className="block text-sm font-medium text-gray-700 mb-1">
            فایل کتاب (PDF یا TXT):
          </label>
          <input
            type="file"
            id="book-file"
            accept=".pdf,.txt"
            onChange={handleFileChange}
            disabled={isUploading}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
          {file && (
            <p className="mt-1 text-sm text-gray-600">
              فایل انتخاب شده: {file.name}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            عنوان:
          </label>
          <input
            type="text"
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            disabled={isUploading}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label htmlFor="author" className="block text-sm font-medium text-gray-700 mb-1">
            نویسنده:
          </label>
          <input
            type="text"
            id="author"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            required
            disabled={isUploading}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label htmlFor="isbn" className="block text-sm font-medium text-gray-700 mb-1">
            شابک (اختیاری):
          </label>
          <input
            type="text"
            id="isbn"
            value={isbn}
            onChange={(e) => setIsbn(e.target.value)}
            disabled={isUploading}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>

        {error && (
          <div className="text-red-500 text-sm mt-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isUploading || !file}
          className={`w-full py-2 px-4 rounded-md text-white font-medium ${
            isUploading || !file
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isUploading ? 'در حال آپلود...' : `آپلود ${fileType === 'pdf' ? 'PDF' : 'TXT'}`}
        </button>
      </form>
    </div>
  );
};

export default PDFUploader; 