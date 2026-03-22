import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Report an Incident | Nigehbaan',
  description:
    'Submit an anonymous report about child trafficking, exploitation, or a child in danger. All reports are encrypted and reviewed by trained personnel.',
};

export default function ReportLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
