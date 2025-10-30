// frontend/app/page.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { PDFUploader } from '@/components/pdf-uploader';
import { WelcomeScreen } from '@/components/welcome-screen';
import { ChatMessage, ChatMessageProps } from '@/components/chat-message';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import TextareaAutosize from 'react-textarea-autosize';
import { ThemeToggle } from '@/components/theme-toggle';

// --- PRE-MADE PROMPTS ---
const examplePrompts = [
  'Summarize the key financial highlights of the report.',
  'What are the main risks mentioned for the company?',
  'Provide an overview of the revenue and net income for the last fiscal year.',
  'Compare the total assets to total liabilities.',
];

export default function Home() {
  const [pdfProcessed, setPdfProcessed] = useState(false);
  const [messages, setMessages] = useState<ChatMessageProps[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatContainerRef.current?.scrollTo(0, chatContainerRef.current.scrollHeight);
  }, [messages, isThinking]);

  const handleUploadSuccess = () => {
    setPdfProcessed(true);
    setMessages([]);
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: ChatMessageProps = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);
    setIsThinking(true);

    const apiChatHistory = messages.map((msg) => ({ type: msg.role, content: msg.content }));

    try {
      const response = await axios.post('http://127.0.0.1:8000/chat/', {
        question: message,
        chat_history: apiChatHistory,
      });
      const assistantMessage: ChatMessageProps = { role: 'assistant', content: response.data.answer };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      toast.error('Error', { description: 'Failed to get a response from the assistant.' });
      setMessages((prev) => prev.slice(0, -1)); // Remove the user's message on failure
    } finally {
      setIsThinking(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
    setInputValue('');
  };

  const handlePromptClick = (prompt: string) => {
    setInputValue(prompt);
    sendMessage(prompt);
    setInputValue('');
  };

  return (
    <div className="flex h-screen bg-muted/40">
      <aside className="w-1/3 max-w-sm p-4 border-r bg-background">
        <div className="flex flex-col h-full">
          <p className="text-2xl font-bold mb-4">Fintrack</p>
          <ThemeToggle />
          <PDFUploader onUploadSuccess={handleUploadSuccess} />
        </div>
      </aside>

      <main className="flex-1 flex flex-col p-4 h-screen">
        {!pdfProcessed ? (
          <WelcomeScreen />
        ) : (
          <div className="flex flex-col h-full">
            <div ref={chatContainerRef} className="flex-1 space-y-6 overflow-y-auto p-4 rounded-lg bg-background border mb-4">
              {messages.length > 0 ? (
                messages.map((msg, index) => <ChatMessage key={index} role={msg.role} content={msg.content} />)
              ) : (
                // --- RENDER PRE-MADE PROMPTS ---
                <div className="flex flex-col items-center justify-center h-full">
                  <p className="text-muted-foreground mb-4">Start the analysis with a pre-made prompt or ask your own question below.</p>
                  {(() => {
                    const longest = Math.max(1, ...examplePrompts.map((p) => p.length));
                    const baseWidth = 220;
                    const computedMaxWidth = Math.min(720, baseWidth + longest * 6); // px, caps at 720
                    const colsClass = examplePrompts.length <= 2 ? 'grid-cols-1' : 'grid-cols-2';

                    return (
                      <div
                        className={`grid ${colsClass} gap-4 w-full`}
                        style={{ maxWidth: `${computedMaxWidth}px` }}
                      >
                        {examplePrompts.map((prompt) => (
                          <Button
                            key={prompt}
                            variant="outline"
                            onClick={() => handlePromptClick(prompt)}
                            className="whitespace-normal break-words text-left p-6"
                          >
                            <span className="whitespace-normal break-words">{prompt}</span>
                          </Button>
                        ))}
                      </div>
                    );
                  })()}
                </div>
              )}
              {isThinking && <ChatMessage role="assistant" content="Thinking..." />}
            </div>

            <div className="mt-auto">
              {/* --- AUTO-RESIZING TEXTAREA FORM --- */}
              <form onSubmit={handleSubmit} className="flex items-center space-x-2">
                <TextareaAutosize
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask a question about the document..."
                  className="flex-1 resize-none border rounded-md p-2 text-sm"
                  minRows={1}
                  maxRows={5}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  disabled={isThinking}
                />
                <Button type="submit" disabled={isThinking || !inputValue.trim()}>
                  {isThinking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                </Button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}