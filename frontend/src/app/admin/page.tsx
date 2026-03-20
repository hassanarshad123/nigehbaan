'use client';

import React from 'react';
import { Footer } from '@/components/layout/Footer';
import { cn, formatNumber } from '@/lib/utils';
import {
  ShieldCheck,
  FileWarning,
  Database,
  Activity,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
} from 'lucide-react';

// Mock data for admin dashboard
const PENDING_REPORTS = [
  { id: 'RPT-001', type: 'suspicious_activity', district: 'Lahore', date: '2024-03-15', status: 'under_review' },
  { id: 'RPT-002', type: 'missing_child', district: 'Karachi', date: '2024-03-14', status: 'submitted' },
  { id: 'RPT-003', type: 'bonded_labor', district: 'Faisalabad', date: '2024-03-14', status: 'submitted' },
  { id: 'RPT-004', type: 'begging_ring', district: 'Islamabad', date: '2024-03-13', status: 'under_review' },
  { id: 'RPT-005', type: 'child_marriage', district: 'Multan', date: '2024-03-13', status: 'submitted' },
];

const DATA_SOURCES_HEALTH = [
  { name: 'Media Scraper', status: 'healthy', lastSync: '2 min ago', records: 24680 },
  { name: 'Court Records API', status: 'healthy', lastSync: '15 min ago', records: 3420 },
  { name: 'SAHIL Dataset', status: 'healthy', lastSync: '1 hr ago', records: 8900 },
  { name: 'Satellite Kiln Detection', status: 'degraded', lastSync: '6 hrs ago', records: 4231 },
  { name: 'PBS Census Data', status: 'healthy', lastSync: '24 hrs ago', records: 154 },
  { name: 'Public Reports', status: 'healthy', lastSync: '1 min ago', records: 1425 },
];

const STATUS_ICON: Record<string, React.ReactNode> = {
  healthy: <CheckCircle2 className="h-4 w-4 text-[#10B981]" />,
  degraded: <AlertTriangle className="h-4 w-4 text-[#F59E0B]" />,
  down: <XCircle className="h-4 w-4 text-[#EF4444]" />,
};

const REPORT_STATUS_STYLES: Record<string, string> = {
  submitted: 'bg-[#06B6D4]/10 text-[#06B6D4]',
  under_review: 'bg-[#F59E0B]/10 text-[#F59E0B]',
  verified: 'bg-[#10B981]/10 text-[#10B981]',
  rejected: 'bg-[#EF4444]/10 text-[#EF4444]',
};

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <main className="mx-auto max-w-screen-xl px-4 pt-6 pb-8">
        {/* Header */}
        <div className="flex items-center gap-2 mb-6">
          <ShieldCheck className="h-5 w-5 text-[#06B6D4]" />
          <h1 className="text-2xl font-bold text-[#F8FAFC]">Admin Dashboard</h1>
        </div>

        {/* System stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#F59E0B]">
              <FileWarning className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Pending Reports</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">23</p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#10B981]">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Verified Today</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">8</p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#06B6D4]">
              <Database className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">Total Records</span>
            </div>
            <p className="text-2xl font-bold text-[#F8FAFC]">{formatNumber(42816)}</p>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <div className="flex items-center gap-2 mb-2 text-[#EC4899]">
              <Activity className="h-4 w-4" />
              <span className="text-xs text-[#94A3B8]">System Health</span>
            </div>
            <p className="text-2xl font-bold text-[#10B981]">98%</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Report moderation */}
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-4 flex items-center gap-2">
              <FileWarning className="h-4 w-4 text-[#F59E0B]" />
              Report Moderation Queue
            </h2>
            <div className="space-y-2">
              {PENDING_REPORTS.map((report) => (
                <div
                  key={report.id}
                  className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between rounded-md bg-[#0F172A] px-3 py-2.5"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-[#06B6D4]">{report.id}</span>
                    <span className="text-xs text-[#F8FAFC] capitalize">
                      {report.type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-[#94A3B8]">{report.district}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#94A3B8] tabular-nums">{report.date}</span>
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                        REPORT_STATUS_STYLES[report.status],
                      )}
                    >
                      {report.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Data source health */}
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
            <h2 className="text-sm font-semibold text-[#F8FAFC] mb-4 flex items-center gap-2">
              <Database className="h-4 w-4 text-[#06B6D4]" />
              Data Source Health
            </h2>
            <div className="space-y-2">
              {DATA_SOURCES_HEALTH.map((source) => (
                <div
                  key={source.name}
                  className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between rounded-md bg-[#0F172A] px-3 py-2.5"
                >
                  <div className="flex items-center gap-2">
                    {STATUS_ICON[source.status]}
                    <span className="text-xs text-[#F8FAFC]">{source.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[#94A3B8] tabular-nums">
                      {formatNumber(source.records)} records
                    </span>
                    <span className="flex items-center gap-1 text-xs text-[#94A3B8]">
                      <Clock className="h-3 w-3" />
                      {source.lastSync}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
