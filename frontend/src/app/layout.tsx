import type { Metadata, Viewport } from 'next';
import { Inter, Noto_Nastaliq_Urdu } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/app/providers';
import { IntlProvider } from '@/components/layout/IntlProvider';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { ReportFAB } from '@/components/layout/ReportFAB';
import { EmergencyBanner } from '@/components/layout/EmergencyBanner';

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
  title: 'Nigehbaan — Pakistan Child Trafficking Intelligence Platform',
  description:
    'Unified data intelligence platform aggregating 90+ sources on child trafficking in Pakistan. Interactive maps, trend analysis, and public reporting.',
  keywords: [
    'child trafficking',
    'Pakistan',
    'intelligence',
    'geospatial',
    'child protection',
    'Nigehbaan',
    'data platform',
    'trend analysis',
    'interactive maps',
  ],
  metadataBase: new URL('https://nigehbaan.vercel.app'),
  openGraph: {
    title: 'Nigehbaan — Pakistan Child Trafficking Intelligence Platform',
    description:
      'Unified data intelligence platform aggregating 90+ sources on child trafficking in Pakistan. Interactive maps, trend analysis, and public reporting.',
    type: 'website',
    locale: 'en_US',
    siteName: 'Nigehbaan',
    url: 'https://nigehbaan.vercel.app',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Nigehbaan — Pakistan Child Trafficking Intelligence Platform',
    description:
      'Unified data intelligence platform aggregating 90+ sources on child trafficking in Pakistan.',
  },
  robots: {
    index: true,
    follow: true,
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
    <html lang="en" dir="ltr" className={`dark ${inter.variable} ${nastaliq.variable}`} suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#06B6D4" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        {/* Inline script to set dir/lang before first paint, avoiding RTL flash */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var l=localStorage.getItem('nigehbaan-locale');if(l==='ur'){document.documentElement.dir='rtl';document.documentElement.lang='ur';}}catch(e){}})();`,
          }}
        />
      </head>
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
                <EmergencyBanner />
                <main id="main-content">
                  {children}
                </main>
                <ReportFAB />
              </ErrorBoundary>
            </ThemeProvider>
          </IntlProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
