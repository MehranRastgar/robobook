import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main className="min-h-screen  bg-gray-50">
      <div className="container mx-auto py-8 max-h-screen scroll-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          روبوک - کتابخانه هوشمند
        </h1>
        <ChatInterface />
      </div>
    </main>
  );
}
