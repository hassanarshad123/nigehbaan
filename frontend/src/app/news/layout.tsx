import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'News | Nigehbaan',
  description: 'Latest news articles related to child trafficking and protection in Pakistan.',
};

export default function NewsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
