import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();
        const audioFile = formData.get('audio') as File;

        if (!audioFile) {
            return NextResponse.json(
                { error: 'No audio file provided' },
                { status: 400 }
            );
        }

        const formDataToSend = new FormData();
        formDataToSend.append('audio', audioFile);

        const response = await fetch('http://127.0.0.1:5000/api/listen', {
            method: 'POST',
            body: formDataToSend,
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error processing audio:', error);
        return NextResponse.json(
            { error: 'Error processing audio' },
            { status: 500 }
        );
    }
} 