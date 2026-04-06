import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { LoginForm } from '@/features/auth/components/LoginForm';

export default function LoginPage() {
  return (
    <Card className="w-full">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl text-center">Welcome back</CardTitle>
        <CardDescription className="text-center">
          Enter your credentials to sign in to your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm />
        
        <div className="mt-4 flex items-center justify-between text-sm">
          <Link 
            href="/recover-password" 
            className="text-muted-foreground hover:text-primary"
          >
            Forgot password?
          </Link>
          <Link 
            href="/signup" 
            className="text-primary hover:underline"
          >
            Create account
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
