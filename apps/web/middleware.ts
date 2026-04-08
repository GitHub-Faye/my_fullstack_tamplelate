import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Paths that don't require authentication
const publicPaths = ['/login', '/signup', '/recover-password', '/reset-password'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the path is public
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path));

  // Get token from cookies or localStorage (we'll check cookie first)
  const token = request.cookies.get('access_token')?.value;

  // If no token and trying to access protected route, redirect to login
  if (!token && !isPublicPath && pathname !== '/') {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // If has token and trying to access login/signup, redirect to dashboard
  if (token && isPublicPath) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.svg$).*)',
  ],
};
