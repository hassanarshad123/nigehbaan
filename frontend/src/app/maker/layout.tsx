import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Maker | Nigehbaan',
  description:
    'Meet Hassan Arshad — the founder of Nigehbaan and Zensbot. A sophomore at Habib University building technology for child protection in Pakistan.',
};

export default function MakerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
