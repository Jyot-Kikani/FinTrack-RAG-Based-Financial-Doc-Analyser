// frontend/components/chat-message.tsx
import { cn } from '@/lib/utils';
import { Bot, User } from 'lucide-react';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={cn('flex items-start space-x-4', isUser ? 'justify-end' : '')}>
      {!isUser && (
        <div className="shrink-0 h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
          <Bot className="h-5 w-5" />
        </div>
      )}
      <div className={cn('px-4 py-2 rounded-lg max-w-xl', isUser ? 'bg-blue-500 text-white' : 'bg-muted')}>
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
      {isUser && (
        <div className="shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center">
          <User className="h-5 w-5" />
        </div>
      )}
    </div>
  );
}