// frontend/src/app/page.tsx
'use client';

import { useState } from 'react';
import { PDFUploader } from '@/components/pdf-uploader';
import { WelcomeScreen } from '@/components/welcome-screen';
import { ChatMessage, ChatMessageProps } from '@/components/chat-message';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { Toaster } from '@/components/ui/sonner';
import { toast } from "sonner";
import axios from 'axios';

export default function Home() {
  const [pdfProcessed, setPdfProcessed] = useState(false);
  const [messages, setMessages] = useState<ChatMessageProps[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  // const { toast } = useToast();

  const handleUploadSuccess = () => {
    setPdfProcessed(true);
    setMessages([]); // Clear previous chat on new document
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: ChatMessageProps = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsThinking(true);

    const apiChatHistory = messages.map((msg) => ({
      type: msg.role,
      content: msg.content,
    }));

    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/chat/',
        {
          question: inputValue,
          chat_history: apiChatHistory,
        },
        { timeout: 600000 }
      );

      const assistantMessage: ChatMessageProps = {
        role: 'assistant',
        content: response.data.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Error sending message:', error);
      toast.error('Error', {
        description: 'Failed to get a response from the assistant.',
      });
      // Optionally remove the user's message if the API call fails
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="flex h-screen bg-muted/40">
      {/* Sidebar */}
      <aside className="w-1/3 max-w-sm p-4 border-r">
        <div className="flex flex-col h-full">
          <h1 className="text-2xl font-bold mb-4">Analyzer 📈</h1>
          <PDFUploader onUploadSuccess={handleUploadSuccess} />
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col p-4">
        {!pdfProcessed ? (
          <WelcomeScreen />
        ) : (
          <div className="flex flex-col h-full">
            {/* Chat History */}
            <div className="flex-1 space-y-6 overflow-y-auto p-4 rounded-lg bg-background">
              {messages.map((msg, index) => (
                <ChatMessage key={index} role={msg.role} content={msg.content} />
              ))}
              {isThinking && <ChatMessage role="assistant" content="..." />}
            </div>

            {/* Chat Input */}
            <div className="mt-4">
              <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question about the document..."
                  className="flex-1"
                  disabled={isThinking}
                />
                <Button type="submit" disabled={isThinking || !inputValue.trim()}>
                  {isThinking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </div>
        )}
      </main>
      <Toaster />
    </div>
  );
}