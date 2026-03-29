// frontend/app/page.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { PDFUploader } from '@/components/pdf-uploader';
import { WelcomeScreen } from '@/components/welcome-screen';
import { ChatMessage, ChatMessageProps } from '@/components/chat-message';
import { Button } from '@/components/ui/button';
import { Send, Loader2, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/app/auth-context';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import TextareaAutosize from 'react-textarea-autosize';
import { ThemeToggle } from '@/components/theme-toggle';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText } from 'lucide-react';

// --- PRE-MADE PROMPTS ---
const examplePrompts = [
  'Summarize the key financial highlights of the report.',
  'What are the main risks mentioned for the company?',
  'Provide an overview of the revenue and net income for the last fiscal year.',
  'Compare the total assets to total liabilities.',
];

export default function Home() {
  const { user, isLoading, supabase } = useAuth();
  const router = useRouter();
  const [pdfProcessed, setPdfProcessed] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [messages, setMessages] = useState<ChatMessageProps[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    async function loadPastHistory() {
      if (user) {
        const { data, error } = await supabase
          .from('chat_histories')
          .select('question, answer')
          .eq('user_id', user.id)
          .order('created_at', { ascending: true });
          
        if (data && data.length > 0) {
          const pastMessages: ChatMessageProps[] = [];
          data.forEach((row) => {
            pastMessages.push({ role: 'user', content: row.question });
            pastMessages.push({ role: 'assistant', content: row.answer });
          });
          setMessages(pastMessages);
          setPdfProcessed(true); // Automatically hide welcome screen if they already have data
        }
      }
    }
    loadPastHistory();
  }, [user, supabase]);

  useEffect(() => {
    async function loadFiles() {
      if (user) {
        const { data, error } = await supabase.storage.from('financial_reports').list(user.id);
        if (data && !error) {
          // Filter out the `.emptyFolderPlaceholder` typically created in storage
          setUploadedFiles(data.filter(f => f.name !== '.emptyFolderPlaceholder'));
        }
      }
    }
    loadFiles();
  }, [user, supabase, pdfProcessed]);

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
      const response = await api.post('/chat/', {
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

  if (isLoading || !user) {
    return <div className="flex h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>;
  }

  return (
    <div className="flex h-screen bg-muted/40">
      <aside className="w-1/3 max-w-sm p-4 border-r bg-background flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <div>
            <p className="text-2xl font-bold tracking-tight">Fintrack</p>
            <p className="text-sm text-muted-foreground">From RAG to Riches</p>
          </div>
          <ThemeToggle />
        </div>

        <Card className="mb-6 shadow-sm">
          <CardHeader className="p-4">
            <CardTitle className="text-sm font-medium text-muted-foreground">Authenticated as</CardTitle>
            <CardDescription className="text-foreground font-medium truncate">
              {user.email}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <Button variant="outline" className="w-full text-muted-foreground hover:text-foreground" onClick={() => supabase.auth.signOut()}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </CardContent>
        </Card>

        <Card className="mb-6 shadow-sm flex-1 overflow-hidden flex flex-col max-h-[40vh]">
          <CardHeader className="p-4 pb-2 shrink-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Your Documents</CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0 flex-1 overflow-y-auto space-y-2">
            {uploadedFiles.length === 0 ? (
              <p className="text-xs text-muted-foreground">No documents uploaded yet.</p>
            ) : (
              uploadedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center space-x-2 text-sm p-2 rounded-md bg-muted/50 border border-muted">
                  <FileText className="h-4 w-4 text-primary shrink-0" />
                  <span className="truncate font-medium">{file.name}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <div className="mt-auto shrink-0">
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