import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Data Sources | Nigehbaan',
  description:
    'Monitor and manage 32+ data scrapers collecting child trafficking intelligence from media, courts, NGOs, and government sources across Pakistan.',
};

export default function ScrapersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
