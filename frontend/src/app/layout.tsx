import type { Metadata, Viewport } from 'next';
import { Inter, Noto_Nastaliq_Urdu } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/app/providers';
import { IntlProvider } from '@/components/layout/IntlProvider';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const nastaliq = Noto_Nastaliq_Urdu({
  subsets: ['arabic'],
  variable: '--font-urdu',
  weight: ['400', '700'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Nigehbaan — Pakistan Child Trafficking Intelligence',
  description:
    'Open-source geospatial intelligence platform tracking child trafficking patterns across Pakistan.',
  keywords: [
    'child trafficking',
    'Pakistan',
    'intelligence',
    'geospatial',
    'child protection',
    'Nigehbaan',
  ],
  openGraph: {
    title: 'Nigehbaan — Pakistan Child Trafficking Intelligence',
    description: 'Open-source geospatial intelligence platform tracking child trafficking patterns across Pakistan.',
    type: 'website',
    locale: 'en_US',
    siteName: 'Nigehbaan',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  viewportFit: 'cover',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${nastaliq.variable}`}>
      <body className="font-sans bg-[#0F172A] text-[#F8FAFC] antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:rounded-md focus:bg-[#06B6D4] focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-[#0F172A]"
        >
          Skip to content
        </a>
        <QueryProvider>
          <IntlProvider>
            <ThemeProvider>
              <ErrorBoundary>
                {children}
              </ErrorBoundary>
            </ThemeProvider>
          </IntlProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
