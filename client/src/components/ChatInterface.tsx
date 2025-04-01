'use client';

import { useState, useRef, useEffect } from 'react';
import { Book, ApiResponse, AudioResponse } from '@/types/api';
import BookUploader from './PDFUploader';

interface Message {
    text: string;
    isUser: boolean;
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [voiceEffect, setVoiceEffect] = useState(0.5); // 0 = normal, 1 = maximum robotic
    const [showUploader, setShowUploader] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    channelCount: 1,
                    sampleRate: 44100
                }
            });

            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 128000
            });

            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start(1000);
            setIsRecording(true);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('خطا در دسترسی به میکروفون. لطفاً مجوز دسترسی را بررسی کنید.');
        }
    };

    const stopRecording = async () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);

            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            await sendAudioToServer(audioBlob);
            return audioBlob;
        }
        return null;
    };

    const sendAudioToServer = async (audioBlob: Blob) => {
        console.log('Starting audio upload...');
        setIsProcessing(true);
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('voice_effect', voiceEffect.toString());

        try {
            console.log('Sending request to /api/listen...');
            const response = await fetch('/api/listen', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                console.error('Server response not OK:', response.status);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Received response from server');
            const data: AudioResponse = await response.json();
            console.log('Parsed response data:', {
                hasRequestText: !!data.request_text,
                requestText: data.request_text,
                hasResponseText: !!data.response_text,
                responseText: data.response_text,
                hasResponseAudio: !!data.response_audio,
                audioFormat: data.audio_format,
                hasError: !!data.error,
                error: data.error
            });
            
            // Add user's transcribed message first
            if (data.request_text) {
                console.log('Adding transcribed message:', data.request_text);
                // Clean up the text by removing newlines and extra spaces
                const cleanText = data.request_text.replace(/\n/g, ' ').trim();
                const userMessage: Message = { text: cleanText, isUser: true };
                setMessages(prev => [...prev, userMessage]);

                // Then add the system's response
                if (data.response_text) {
                    console.log('Adding system response:', data.response_text);
                    const systemMessage: Message = { text: data.response_text, isUser: false };
                    setMessages(prev => [...prev, systemMessage]);

                    // Handle TTS response if available
                    if (data.response_audio && data.audio_format) {
                        console.log('Processing TTS audio response...');
                        const audioData = atob(data.response_audio);
                        const arrayBuffer = new ArrayBuffer(audioData.length);
                        const uint8Array = new Uint8Array(arrayBuffer);
                        for (let i = 0; i < audioData.length; i++) {
                            uint8Array[i] = audioData.charCodeAt(i);
                        }
                        const audioBlob = new Blob([arrayBuffer], { type: `audio/${data.audio_format}` });
                        
                        const audioUrl = URL.createObjectURL(audioBlob);
                        const audio = new Audio(audioUrl);
                        audio.onended = () => URL.revokeObjectURL(audioUrl);
                        console.log('Playing TTS audio...');
                        await audio.play();
                    }
                } else if (data.error) {
                    console.log('Received error from server:', data.error);
                    const errorMessage: Message = { text: data.error, isUser: false };
                    setMessages(prev => [...prev, errorMessage]);
                } else {
                    console.log('No response text received from server');
                    const errorMessage: Message = { 
                        text: 'متأسفانه نتوانستم پاسخ مناسب را دریافت کنم. لطفاً دوباره تلاش کنید.', 
                        isUser: false 
                    };
                    setMessages(prev => [...prev, errorMessage]);
                }
            } else {
                console.log('No text was transcribed');
                const errorMessage: Message = { 
                    text: 'متأسفانه نتوانستم صدای شما را تشخیص دهم. لطفاً دوباره تلاش کنید.', 
                    isUser: false 
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Error in sendAudioToServer:', error);
            const errorMessage: Message = { 
                text: 'خطا در ارسال صدا. لطفاً دوباره تلاش کنید.', 
                isUser: false 
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsProcessing(false);
            console.log('Audio processing completed');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() && !isRecording) return;

        try {
            console.log('Starting handleSubmit...');
            setIsProcessing(true);

            if (isRecording) {
                console.log('Stopping recording...');
                await stopRecording();
            } else {
                console.log('Sending text query:', inputText);
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        query: inputText,
                        voice_effect: voiceEffect 
                    }),
                });

                if (!response.ok) {
                    console.error('Query response not OK:', response.status);
                    throw new Error('Failed to process query');
                }

                console.log('Received query response');
                const data: ApiResponse = await response.json();
                console.log('Parsed query response:', {
                    hasResponse: !!data.response,
                    response: data.response,
                    hasError: !!data.error,
                    error: data.error,
                    hasAudio: !!data.audio,
                    audioFormat: data.audio_format
                });
                
                // Add messages to the chat
                setMessages(prev => [
                    ...prev,
                    { text: inputText, isUser: true },
                    { text: data.response || data.error || 'خطا در ارتباط با سرور. لطفاً دوباره تلاش کنید.', isUser: false },
                ]);

                // Handle TTS response if available
                if (data.audio && data.audio_format) {
                    console.log('Processing query TTS audio response...');
                    const audioData = atob(data.audio);
                    const arrayBuffer = new ArrayBuffer(audioData.length);
                    const uint8Array = new Uint8Array(arrayBuffer);
                    for (let i = 0; i < audioData.length; i++) {
                        uint8Array[i] = audioData.charCodeAt(i);
                    }
                    const audioBlob = new Blob([arrayBuffer], { type: `audio/${data.audio_format}` });
                    
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.onended = () => URL.revokeObjectURL(audioUrl);
                    console.log('Playing query TTS audio...');
                    await audio.play();
                }
            }

            setInputText('');
        } catch (error) {
            console.error('Error in handleSubmit:', error);
            setMessages(prev => [
                ...prev,
                { text: inputText || '🎤', isUser: true },
                { text: 'متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.', isUser: false },
            ]);
        } finally {
            setIsProcessing(false);
            console.log('Query processing completed');
        }
    };

    const handleUploadSuccess = (bookId: number) => {
        setMessages(prev => [
            ...prev,
            { text: 'کتاب با موفقیت آپلود شد.', isUser: false }
        ]);
        setShowUploader(false);
    };

    const handleUploadError = (error: string) => {
        setMessages(prev => [
            ...prev,
            { text: error, isUser: false }
        ]);
    };

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-gray-100 p-4">
            <div className="w-full max-w-4xl h-[90vh] max-h-[700px] bg-white rounded-xl shadow-lg flex flex-col overflow-hidden">
                {/* Header */}
                <div className="bg-blue-900 text-white px-5 py-4 text-center shadow-md">
                    <h1 className="text-xl font-semibold">روبوک - کتابخانه هوشمند</h1>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
                    {messages.map((message, index) => (
                        <div 
                            key={index} 
                            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                        >
                            <div 
                                className={`max-w-[85%] rounded-xl px-5 py-3 text-base leading-relaxed shadow-sm
                                    ${message.isUser 
                                        ? 'bg-blue-900 text-white' 
                                        : 'bg-white text-gray-900 border border-gray-200'
                                    }`}
                            >
                                {message.text}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Uploader */}
                {showUploader ? (
                    <div className="p-4 border-t">
                        <BookUploader
                            onUploadSuccess={handleUploadSuccess}
                            onUploadError={handleUploadError}
                        />
                    </div>
                ) : (
                    <div className="p-5 bg-white border-t border-gray-200">
                        <div className="flex justify-between items-center mb-4">
                            <button
                                onClick={() => setShowUploader(true)}
                                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                            >
                                آپلود کتاب
                            </button>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-600">تأثیر صدا:</span>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    value={voiceEffect}
                                    onChange={(e) => setVoiceEffect(parseFloat(e.target.value))}
                                    className="w-32"
                                />
                            </div>
                        </div>
                        <form onSubmit={handleSubmit} className="flex space-x-2">
                            <button
                                type="button"
                                onClick={isRecording ? stopRecording : startRecording}
                                className={`px-4 py-2 rounded-md ${
                                    isRecording
                                        ? 'bg-red-600 hover:bg-red-700'
                                        : 'bg-blue-600 hover:bg-blue-700'
                                } text-white`}
                            >
                                {isRecording ? 'توقف ضبط' : 'ضبط صدا'}
                            </button>
                            <input
                                type="text"
                                value={inputText}
                                onChange={(e) => setInputText(e.target.value)}
                                placeholder="پیام خود را بنویسید..."
                                className="text-black flex-1 p-2 border rounded-md"
                                disabled={isProcessing || isRecording}
                            />
                            <button
                                type="submit"
                                disabled={isProcessing || isRecording || (!inputText.trim() && !isRecording)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                            >
                                ارسال
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </div>
    );
} 