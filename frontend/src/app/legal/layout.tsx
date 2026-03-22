import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Legal Intelligence | Nigehbaan',
  description:
    'Search and analyze Pakistan court judgments related to child trafficking, exploitation, and bonded labor. Filter by court, year, PPC section, and verdict.',
};

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
