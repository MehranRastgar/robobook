'use client';

import { useState } from 'react';
import axios from 'axios';

interface BookUploaderProps {
  onUploadSuccess?: (bookId: number) => void;
  onUploadError?: (error: string) => void;
}

const BookUploader: React.FC<BookUploaderProps> = ({ onUploadSuccess, onUploadError }) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [isbn, setIsbn] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [metadata, setMetadata] = useState<any>(null);
  const [fileType, setFileType] = useState<'pdf' | 'txt' | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) {
      setFile(null);
      setMetadata(null);
      setFileType(null);
      return;
    }

    const fileType = selectedFile.type;
    if (fileType === 'application/pdf') {
      setFileType('pdf');
      setFile(selectedFile);
      await extractMetadata(selectedFile, 'pdf');
    } else if (fileType === 'text/plain' || selectedFile.name.endsWith('.txt')) {
      setFileType('txt');
      setFile(selectedFile);
      await extractMetadata(selectedFile, 'txt');
    } else {
      setFile(null);
      setMetadata(null);
      setFileType(null);
      onUploadError?.('لطفاً یک فایل PDF یا TXT معتبر انتخاب کنید');
    }
  };

  const extractMetadata = async (file: File, type: 'pdf' | 'txt') => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = type === 'pdf' 
        ? '/api/books/import/pdf/metadata'
        : '/api/books/import/txt/metadata';

      const response = await axios.post(`http://127.0.0.1:5000`+endpoint, formData);
      setMetadata(response.data);
      
      if (response.data.title) setTitle(response.data.title);
      if (response.data.author) setAuthor(response.data.author);
    } catch (error) {
      console.error('Error extracting metadata:', error);
      onUploadError?.(`خطا در استخراج اطلاعات ${type === 'pdf' ? 'PDF' : 'TXT'}`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !fileType) {
      onUploadError?.('لطفاً یک فایل انتخاب کنید');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('author', author);
      if (isbn) formData.append('isbn', isbn);

      const endpoint = fileType === 'pdf'
        ? '/api/books/import/pdf'
        : '/api/books/import/txt';

      const response = await axios.post(`http://127.0.0.1:5000`+endpoint, formData);
      onUploadSuccess?.(response.data.book_id);
      
      // Reset form
      setFile(null);
      setTitle('');
      setAuthor('');
      setIsbn('');
      setMetadata(null);
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
        </div>

        {metadata && (
          <div className="bg-gray-50 p-4 rounded-md">
            <h3 className="text-lg font-semibold mb-2 text-gray-800">اطلاعات استخراج شده</h3>
            <p className="text-gray-600"><span className="font-medium">عنوان:</span> {metadata.title || 'یافت نشد'}</p>
            <p className="text-gray-600"><span className="font-medium">نویسنده:</span> {metadata.author || 'یافت نشد'}</p>
            {fileType === 'pdf' && (
              <p className="text-gray-600"><span className="font-medium">تعداد صفحات:</span> {metadata.pages || 'نامشخص'}</p>
            )}
            {fileType === 'txt' && (
              <p className="text-gray-600"><span className="font-medium">تعداد کلمات:</span> {metadata.word_count || 'نامشخص'}</p>
            )}
          </div>
        )}

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

export default BookUploader; 