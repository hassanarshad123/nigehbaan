import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard | Nigehbaan',
  description:
    'Analytics dashboard with interactive charts, trend analysis, and KPI summaries across Pakistan child trafficking data from 32+ sources.',
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
