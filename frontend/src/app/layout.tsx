import type { Metadata, Viewport } from 'next';
import { Inter, Noto_Nastaliq_Urdu } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/layout/ThemeProvider';
import { QueryProvider } from '@/app/providers';
import { IntlProvider } from '@/components/layout/IntlProvider';

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
        <QueryProvider>
          <IntlProvider>
            <ThemeProvider>{children}</ThemeProvider>
          </IntlProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
