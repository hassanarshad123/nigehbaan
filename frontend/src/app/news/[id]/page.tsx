'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { fetchNewsArticle } from '@/lib/api';
import {
  ArrowLeft,
  Calendar,
  ExternalLink,
  MapPin,
  Loader2,
  AlertTriangle,
} from 'lucide-react';

export default function NewsDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const { data: article, isLoading, error } = useQuery({
    queryKey: ['news-article', id],
    queryFn: () => fetchNewsArticle(id),
    enabled: !isNaN(id),
  });

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-3xl px-4 pt-16 pb-8">
        <div className="mb-6">
          <Link
            href="/news"
            className="inline-flex items-center gap-1.5 text-sm text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to News
          </Link>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-[#06B6D4]" />
          </div>
        )}

        {error && !isLoading && (
          <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 px-4 py-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-[#EF4444] mb-2" />
            <p className="text-sm text-[#EF4444]">Article not found or failed to load.</p>
          </div>
        )}

        {article && !isLoading && (
          <article>
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-xs font-medium text-[#06B6D4] uppercase tracking-wider">
                  {article.sourceName ?? 'Unknown Source'}
                </span>
                {article.isTraffickingRelevant && (
                  <span className="rounded-full bg-[#EF4444]/10 px-2 py-0.5 text-[10px] font-medium text-[#EF4444]">
                    Trafficking Related
                  </span>
                )}
                {article.relevanceScore != null && (
                  <span className="text-[10px] text-[#94A3B8]">
                    Score: {(article.relevanceScore * 100).toFixed(0)}%
                  </span>
                )}
              </div>

              <h1 className="text-2xl font-bold text-[#F8FAFC] mb-3">
                {article.title ?? 'Untitled Article'}
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#94A3B8]">
                {article.publishedDate && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {new Date(article.publishedDate).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </span>
                )}
                {article.url && (
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[#06B6D4] hover:underline"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Original Source
                  </a>
                )}
              </div>
            </div>

            {/* Full text */}
            <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6 mb-6">
              {article.fullText ? (
                <p className="text-sm text-[#94A3B8] leading-relaxed whitespace-pre-wrap">
                  {article.fullText}
                </p>
              ) : (
                <p className="text-sm text-[#94A3B8] italic">Full text not available.</p>
              )}
            </div>

            {/* Extracted data */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {article.extractedLocations && article.extractedLocations.length > 0 && (
                <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
                  <h3 className="text-xs font-semibold text-[#F8FAFC] mb-2 flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-[#10B981]" />
                    Extracted Locations
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {(article.extractedLocations as string[]).map((loc, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-[#10B981]/10 px-2 py-0.5 text-[10px] text-[#10B981]"
                      >
                        {String(loc)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {article.extractedEntities && article.extractedEntities.length > 0 && (
                <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-4">
                  <h3 className="text-xs font-semibold text-[#F8FAFC] mb-2">
                    Extracted Entities
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {(article.extractedEntities as string[]).map((ent, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-[#06B6D4]/10 px-2 py-0.5 text-[10px] text-[#06B6D4]"
                      >
                        {String(ent)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </article>
        )}
      </main>

      <Footer />
    </div>
  );
}
