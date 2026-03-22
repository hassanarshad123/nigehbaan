import { NextResponse, type NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

/**
 * Middleware that protects admin routes with a server-side session check.
 * Unauthenticated requests to /admin/* are redirected to the sign-in page.
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect all /admin routes at the server level
  if (pathname.startsWith('/admin')) {
    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    });

    if (!token) {
      const signInUrl = new URL('/api/auth/signin', request.url);
      signInUrl.searchParams.set('callbackUrl', pathname);
      return NextResponse.redirect(signInUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
