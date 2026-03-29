// frontend/app/login/page.tsx
'use client';

import { useAuth } from '@/app/auth-context';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

export default function LoginPage() {
    const { supabase, user } = useAuth();
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    
    useEffect(() => {
        if (user) {
            router.push('/');
        }
    }, [user, router]);

    const handleEmailSignUp = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const { error } = await supabase.auth.signUp({ email, password });
            if (error) throw error;
            toast.success('Account created! (If enabled, check email to confirm)');
        } catch (error: any) {
            toast.error(error.message || 'Failed to sign up');
        } finally {
            setIsLoading(false);
        }
    };

    const handleEmailSignIn = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const { error } = await supabase.auth.signInWithPassword({ email, password });
            if (error) throw error;
            toast.success('Successfully logged in!');
            router.push('/');
        } catch (error: any) {
            toast.error(error.message || 'Failed to sign in');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex h-screen items-center justify-center bg-muted/40 p-4">
            <Card className="w-full max-w-sm shadow-lg border-muted">
                <CardHeader className="text-center space-y-2">
                    <CardTitle className="text-2xl font-bold tracking-tight">Sign in</CardTitle>
                    <CardDescription>
                        Welcome to Fintrack. Enter your credentials to access your secure workspace.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form className="space-y-4">
                        <div className="space-y-2 text-left">
                            <label className="text-sm font-medium leading-none text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70" htmlFor="email">
                                Email
                            </label>
                            <Input 
                                id="email"
                                type="email" 
                                placeholder="name@example.com" 
                                value={email} 
                                onChange={(e) => setEmail(e.target.value)} 
                                required 
                                disabled={isLoading}
                                className="w-full"
                            />
                        </div>
                        <div className="space-y-2 text-left">
                            <label className="text-sm font-medium leading-none text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70" htmlFor="password">
                                Password
                            </label>
                            <Input 
                                id="password"
                                type="password" 
                                placeholder="Enter your password" 
                                value={password} 
                                onChange={(e) => setPassword(e.target.value)} 
                                required 
                                disabled={isLoading}
                                className="w-full"
                            />
                        </div>
                        <div className="flex flex-col gap-3 pt-4">
                            <Button 
                                type="button" 
                                onClick={handleEmailSignIn} 
                                disabled={isLoading || !email || !password}
                                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                            >
                                {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                Sign In
                            </Button>
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t border-muted" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-background px-2 text-muted-foreground">
                                        or
                                    </span>
                                </div>
                            </div>
                            <Button 
                                type="button" 
                                variant="outline"
                                onClick={handleEmailSignUp} 
                                disabled={isLoading || !email || !password}
                                className="w-full"
                            >
                                Create Account
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}