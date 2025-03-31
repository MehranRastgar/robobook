export interface Book {
    id: number;
    title: string;
    author: string;
    shelf_location: string;
    description?: string;
    isbn?: string;
    price?: number;
    stock?: number;
}

export interface ApiResponse {
    response?: string;
    error?: string;
    books?: Book[];
    audio?: string;
    audio_format?: string;
}

export interface AudioResponse {
    request_text: string;
    response_text: string;
    response_audio?: string;
    audio_format?: string;
    error?: string;
} 