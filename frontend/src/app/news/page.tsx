'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { cn } from '@/lib/utils';
import { fetchNewsArticles, fetchNewsSources } from '@/lib/api';
import type { NewsArticleListItem } from '@/lib/api';
import {
  Newspaper,
  Calendar,
  MapPin,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Filter,
} from 'lucide-react';

const PAGE_SIZE = 20;

export default function NewsPage() {
  const { data: sourceList } = useQuery({
    queryKey: ['news-sources'],
    queryFn: fetchNewsSources,
  });
  const SOURCES = [
    { value: '', label: 'All Sources' },
    ...(sourceList ?? []).map((s) => ({ value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) })),
  ];
  const [source, setSource] = useState('');
  const [relevantOnly, setRelevantOnly] = useState(false);
  const [page, setPage] = useState(1);

  const { data: articles, isLoading, error } = useQuery({
    queryKey: ['news', source, relevantOnly, page],
    queryFn: () =>
      fetchNewsArticles({
        sourceName: source || undefined,
        isTraffickingRelevant: relevantOnly ? true : undefined,
        page,
        limit: PAGE_SIZE,
      }),
  });

  const hasMore = articles && articles.length === PAGE_SIZE;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Newspaper className="h-6 w-6 text-[#06B6D4]" />
            <h1 className="text-2xl font-bold text-[#F8FAFC]">News Monitor</h1>
          </div>
          <p className="text-sm text-[#94A3B8]">
            News articles scraped from Pakistani media outlets, analyzed for child trafficking relevance.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="flex items-center gap-1.5 text-xs text-[#94A3B8]">
            <Filter className="h-3.5 w-3.5" />
            Filters
          </div>

          <select
            value={source}
            onChange={(e) => { setSource(e.target.value); setPage(1); }}
            className="rounded-md border border-[#334155] bg-[#0F172A] px-3 py-1.5 text-sm text-[#F8FAFC] outline-none border-glow-focus"
          >
            {SOURCES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <label className="flex items-center gap-2 text-sm text-[#94A3B8] cursor-pointer">
            <input
              type="checkbox"
              checked={relevantOnly}
              onChange={(e) => { setRelevantOnly(e.target.checked); setPage(1); }}
              className="rounded border-[#334155] bg-[#0F172A]"
            />
            Trafficking-relevant only
          </label>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
                <div className="skeleton h-4 w-3/4 mb-3" />
                <div className="skeleton h-3 w-full mb-2" />
                <div className="skeleton h-3 w-2/3" />
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 px-4 py-6 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-[#EF4444] mb-2" />
            <p className="text-sm text-[#EF4444]">
              Failed to load news articles. Please try again later.
            </p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && articles && articles.length === 0 && (
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-12 text-center">
            <Newspaper className="mx-auto h-10 w-10 text-[#94A3B8] mb-3" />
            <p className="text-sm text-[#94A3B8]">No news articles found for the selected filters.</p>
          </div>
        )}

        {/* Articles grid */}
        {articles && articles.length > 0 && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {articles.map((article: NewsArticleListItem) => (
              <Link
                key={article.id}
                href={`/news/${article.id}`}
                className="block rounded-lg border border-[#334155] bg-[#1E293B] p-4 hover:border-[#94A3B8] transition-default"
              >
                {/* Source & relevance */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-[#06B6D4] uppercase tracking-wider">
                    {article.sourceName ?? 'Unknown'}
                  </span>
                  {article.isTraffickingRelevant && (
                    <span className="rounded-full bg-[#EF4444]/10 px-2 py-0.5 text-xs font-medium text-[#EF4444]">
                      Trafficking Related
                    </span>
                  )}
                </div>

                {/* Title */}
                <h3 className="text-sm font-semibold text-[#F8FAFC] mb-2 line-clamp-2">
                  {article.title ?? 'Untitled'}
                </h3>

                {/* Snippet */}
                {article.snippet && (
                  <p className="text-xs text-[#94A3B8] mb-3 line-clamp-3">
                    {article.snippet}
                  </p>
                )}

                {/* Meta */}
                <div className="flex items-center gap-3 text-xs text-[#94A3B8]">
                  {article.publishedDate && (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(article.publishedDate).toLocaleDateString()}
                    </span>
                  )}
                  {article.extractedLocations && article.extractedLocations.length > 0 && (
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {article.extractedLocations.length} location(s)
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Pagination */}
        {articles && (articles.length > 0 || page > 1) && (
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className={cn(
                'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-default',
                page <= 1
                  ? 'text-[#334155] cursor-not-allowed'
                  : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
              )}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <span className="text-sm text-[#94A3B8]">Page {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className={cn(
                'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm transition-default',
                !hasMore
                  ? 'text-[#334155] cursor-not-allowed'
                  : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]',
              )}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
