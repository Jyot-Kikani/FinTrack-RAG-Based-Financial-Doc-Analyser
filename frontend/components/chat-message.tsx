// frontend/components/chat-message.tsx
'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Bot, User, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from './ui/button';
import { motion } from 'framer-motion';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const [hasCopied, setHasCopied] = useState(false);
  const isUser = role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setHasCopied(true);
    setTimeout(() => setHasCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn('flex items-start space-x-4', isUser ? 'justify-end' : '')}
    >
      {!isUser && (
        <div className="shrink-0 h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
          <Bot className="h-5 w-5" />
        </div>
      )}
      <div className={cn('px-4 py-2 rounded-lg max-w-2xl relative group', isUser ? 'bg-blue-500 text-white' : 'bg-muted')}>
        <div className="prose dark:prose-invert prose-p:leading-relaxed prose-pre:p-0">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>

        {!isUser && (
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" onClick={handleCopy}>
              {hasCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        )}
      </div>
      {isUser && (
        <div className="shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center">
          <User className="h-5 w-5" />
        </div>
      )}
    </motion.div>
  );
}
