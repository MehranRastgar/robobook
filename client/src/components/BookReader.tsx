import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Select, MenuItem, FormControl, InputLabel, Button, CircularProgress, SelectChangeEvent, IconButton, Stack } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';

interface Book {
  id: number;
  title: string;
  author: string;
  chapters?: Array<{
    id: number;
    chapter_number: number;
    title: string;
    content: string;
  }>;
  text_content?: string;
  processed_chunks?: Array<{
    original_text: string;
    translated_text: string;
    start: number;
    end: number;
  }>;
  total_pages?: number;
}

interface PageContent {
  content: string;
  page_number: number;
  total_pages: number;
  translated_content?: string;
}

const BookReader: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageContent, setPageContent] = useState<PageContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);

  // Fetch all books from the database
  useEffect(() => {
    const fetchBooks = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://127.0.0.1:5000/api/books');
        if (!response.ok) {
          throw new Error('Failed to fetch books');
        }
        const data = await response.json();
        setBooks(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch books');
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  }, []);

  // Process book when selected
  useEffect(() => {
    const processBook = async () => {
      if (!selectedBook) return;

      try {
        setLoading(true);
        const response = await fetch(`http://127.0.0.1:5000/api/books/${selectedBook.id}/process`, {
          method: 'POST'
        });
        if (!response.ok) {
          throw new Error('Failed to process book');
        }
        const data = await response.json();
        setSelectedBook(prev => prev ? { ...prev, total_pages: data.total_pages } : null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to process book');
      } finally {
        setLoading(false);
      }
    };

    // Only process if the book hasn't been processed yet
    if (selectedBook && !selectedBook.total_pages) {
      processBook();
    }
  }, [selectedBook?.id]); // Only run when book ID changes

  // Fetch page content when page changes
  useEffect(() => {
    const fetchPageContent = async () => {
      if (!selectedBook || !selectedBook.total_pages) return;

      try {
        setLoading(true);
        const response = await fetch(`http://127.0.0.1:5000/api/books/${selectedBook.id}/page/${currentPage}`);
        if (!response.ok) {
          throw new Error('Failed to fetch page content');
        }
        const data = await response.json();
        setPageContent(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch page content');
      } finally {
        setLoading(false);
      }
    };

    fetchPageContent();
  }, [selectedBook?.id, currentPage]); // Only run when book ID or page number changes

  const handleBookChange = (event: SelectChangeEvent<number>) => {
    const bookId = Number(event.target.value);
    const book = books.find(b => b.id === bookId);
    if (book) {
      setSelectedBook(book);
      setCurrentPage(1);
      setPageContent(null);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (selectedBook && newPage >= 1 && newPage <= (selectedBook.total_pages || 1)) {
      setCurrentPage(newPage);
    }
  };

  const handlePlayPause = async () => {
    if (!selectedBook) return;

    if (isPlaying && audio) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:5000/api/books/${selectedBook.id}/tts/${currentPage}`);
      if (!response.ok) {
        throw new Error('Failed to fetch audio');
      }
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      const newAudio = new Audio(audioUrl);
      newAudio.onended = () => setIsPlaying(false);
      newAudio.play();
      setAudio(newAudio);
      setIsPlaying(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to play audio');
    } finally {
      setLoading(false);
    }
  };

  const handleTranslate = async () => {
    if (!selectedBook || !pageContent) return;

    try {
      setIsTranslating(true);
      const response = await fetch(`http://127.0.0.1:5000/api/books/${selectedBook.id}/translate/${currentPage}`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to translate page');
      }
      
      const data = await response.json();
      setPageContent(prev => prev ? { ...prev, translated_content: data.translated_content } : null);
      setShowTranslation(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to translate page');
    } finally {
      setIsTranslating(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        خواندن کتاب
      </Typography>

      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>انتخاب کتاب</InputLabel>
        <Select
          value={selectedBook?.id || ''}
          onChange={handleBookChange}
          label="انتخاب کتاب"
        >
          {books.map((book) => (
            <MenuItem key={book.id} value={book.id}>
              {book.title} - {book.author}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {selectedBook && (
        <>
          <Typography variant="h5" gutterBottom>
            {selectedBook.title}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom>
            نویسنده: {selectedBook.author}
          </Typography>

          {pageContent && (
            <>
              <Paper elevation={3} sx={{ p: 3, minHeight: 400, mb: 3 }}>
                <Typography variant="body1" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
                  {showTranslation ? pageContent.translated_content : pageContent.content}
                </Typography>
              </Paper>

              <Stack direction="row" spacing={2} justifyContent="center" alignItems="center">
                <IconButton 
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                >
                  <NavigateNextIcon />
                </IconButton>

                <Typography variant="body1">
                  صفحه {pageContent.page_number} از {pageContent.total_pages}
                </Typography>

                <IconButton 
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= pageContent.total_pages}
                >
                  <NavigateBeforeIcon />
                </IconButton>

                <IconButton onClick={handlePlayPause} color="primary">
                  {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
                </IconButton>

                <Button
                  variant="contained"
                  color="secondary"
                  onClick={handleTranslate}
                  disabled={isTranslating || showTranslation}
                  startIcon={isTranslating ? <CircularProgress size={20} /> : null}
                >
                  {isTranslating ? 'در حال ترجمه...' : 'ترجمه به فارسی'}
                </Button>

                {showTranslation && (
                  <Button
                    variant="outlined"
                    color="secondary"
                    onClick={() => setShowTranslation(false)}
                  >
                    نمایش متن اصلی
                  </Button>
                )}
              </Stack>
            </>
          )}
        </>
      )}
    </Container>
  );
};

export default BookReader; 