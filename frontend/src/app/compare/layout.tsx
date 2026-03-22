import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Compare Districts | Nigehbaan',
  description:
    'Compare child trafficking vulnerability indicators across Pakistani districts side by side with radar charts and detailed breakdowns.',
};

export default function CompareLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
