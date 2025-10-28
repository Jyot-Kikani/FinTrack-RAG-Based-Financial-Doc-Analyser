// frontend/components/pdf-uploader.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { UploadCloud, FileText, Loader2 } from 'lucide-react';
// import { useToast } from '@/components/ui/use-toast';
import { toast } from "sonner";
import axios from 'axios';

interface PDFUploaderProps {
  onUploadSuccess: () => void;
}

export function PDFUploader({ onUploadSuccess }: PDFUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  // const { toast } = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleProcess = async () => {
    if (!selectedFile) {
      toast.error('No file selected', {
        description: 'Please choose a PDF file to process.',
      });
      return;
    }

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // IMPORTANT: Update this URL to match your backend's URL
      const response = await axios.post('http://127.0.0.1:8000/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000, // 10 minutes timeout for large files
      });

      if (response.status === 200) {
        toast.success('Success!', {
          description: `"${selectedFile.name}" processed successfully.`,
        });
        onUploadSuccess();
      }
    } catch (error: any) {
      console.error('Error processing document:', error);
      toast.error('Error', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload PDF</CardTitle>
        <CardDescription>Process a document to begin the chat.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-2">
          <UploadCloud className="h-5 w-5 text-muted-foreground" />
          <Input id="pdf-upload" type="file" accept=".pdf" onChange={handleFileChange} disabled={isProcessing} />
        </div>

        {selectedFile && !isProcessing && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground p-2 bg-muted rounded-md">
            <FileText className="h-4 w-4" />
            <span>{selectedFile.name}</span>
          </div>
        )}

        <Button onClick={handleProcess} disabled={isProcessing || !selectedFile} className="w-full">
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Process Document'
          )}
        </Button>
      </CardContent>
    </Card>
  );
}