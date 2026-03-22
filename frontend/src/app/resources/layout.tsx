import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Resources | Nigehbaan',
  description:
    'Emergency helplines, legal aid, shelter homes, and NGO contacts for child protection in Pakistan. Includes Child Protection Bureau (1099), Edhi (1098), and more.',
};

export default function ResourcesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
