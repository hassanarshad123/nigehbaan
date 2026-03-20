import { NextResponse } from 'next/server';

// i18n middleware disabled — no [locale] route segment exists yet.
// Re-enable when adding multi-language support with a [locale] layout.
export function middleware() {
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)'],
};
