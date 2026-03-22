import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About | Nigehbaan',
  description:
    'Learn about Nigehbaan, an open-source geospatial intelligence platform for child protection in Pakistan. Our mission, methodology, data sources, and team.',
};

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
