// frontend/components/welcome-screen.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText } from 'lucide-react';

export function WelcomeScreen() {
  return (
    <div className="flex items-center justify-center h-full">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <CardTitle className="flex items-center justify-center space-x-2">
            <FileText className="h-6 w-6" />
            <span>Financial Reports Analyzer</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Please upload and process a financial report PDF in the sidebar to begin your analysis.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}