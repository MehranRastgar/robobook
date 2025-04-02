'use client';

import { useState } from 'react';
import BookUploader from '@/components/PDFUploader';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const handleUploadSuccess = (bookId: number) => {
    // Redirect to the reader page for the uploaded book
    router.push(`/reader/${bookId}`);
  };

  const handleUploadError = (error: string) => {
    setError(error);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 text-center">آپلود کتاب</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <BookUploader
          onUploadSuccess={handleUploadSuccess}
          onUploadError={handleUploadError}
        />
      </div>
    </div>
  );
} 