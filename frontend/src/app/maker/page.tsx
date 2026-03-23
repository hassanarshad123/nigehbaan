'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import {
  Shield,
  Scale,
  BookOpen,
  PhoneCall,
  ExternalLink,
  Github,
  Linkedin,
  Globe,
  GraduationCap,
  MapPin,
  Heart,
  Wrench,
} from 'lucide-react';

/* ── Product & social data ── */

const PRODUCTS = [
  {
    nameKey: 'nigehbaan' as const,
    descKey: 'nigehbaanDesc' as const,
    url: 'https://nigehbaan.vercel.app',
    icon: <Shield className="h-5 w-5" />,
    color: '#06B6D4',
    highlight: true,
  },
  {
    nameKey: 'qanoonai' as const,
    descKey: 'qanoonaiDesc' as const,
    url: 'https://qanoonai.com',
    icon: <Scale className="h-5 w-5" />,
    color: '#10B981',
    highlight: false,
  },
  {
    nameKey: 'ictlms' as const,
    descKey: 'ictlmsDesc' as const,
    url: null,
    icon: <BookOpen className="h-5 w-5" />,
    color: '#F59E0B',
    highlight: false,
  },
  {
    nameKey: 'zenscall' as const,
    descKey: 'zenscallDesc' as const,
    url: 'https://zenscall.com',
    icon: <PhoneCall className="h-5 w-5" />,
    color: '#EC4899',
    highlight: false,
  },
];

const SOCIALS = [
  {
    labelKey: 'github' as const,
    url: 'https://github.com/hassanarshad123',
    icon: <Github className="h-4 w-4" />,
  },
  {
    labelKey: 'linkedin' as const,
    url: 'https://linkedin.com/in/hassanarshad',
    icon: <Linkedin className="h-4 w-4" />,
  },
  {
    labelKey: 'zensbot' as const,
    url: 'https://zensbot.com',
    icon: <Globe className="h-4 w-4" />,
  },
];

export default function MakerPage() {
  const t = useTranslations('maker');

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-lg px-4 pt-16 pb-8">
        {/* ── Hero: side-by-side ── */}
        <section className="mb-12">
          <div className="flex flex-col items-center gap-8 md:flex-row md:items-start">
            {/* Avatar */}
            <div className="shrink-0">
              <img
                src="https://avatars.githubusercontent.com/u/196851987?v=4"
                alt="Hassan Arshad"
                width={160}
                height={160}
                className="rounded-full border-2 border-[#06B6D4]/50 shadow-lg shadow-[#06B6D4]/10"
              />
            </div>

            {/* Bio */}
            <div className="text-center md:text-left">
              <h1 className="text-3xl font-bold text-[#F8FAFC] mb-1">
                {t('name')}
              </h1>
              <p className="text-lg text-[#06B6D4] mb-3">{t('subtitle')}</p>

              <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-5 text-sm text-[#94A3B8]">
                <span className="flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4 text-[#10B981]" />
                  {t('university')}
                </span>
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-[#F59E0B]" />
                  {t('location')}
                </span>
              </div>

              <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6 space-y-3">
                <p className="text-sm text-[#94A3B8] leading-relaxed">
                  {t('bioLine1')}
                </p>
                <p className="text-sm text-[#94A3B8] leading-relaxed">
                  {t('bioLine2')}
                </p>
                <p className="text-sm text-[#94A3B8] leading-relaxed italic">
                  {t('bioLine3')}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Products grid ── */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Wrench className="h-5 w-5 text-[#06B6D4]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">
              {t('productsTitle')}
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {PRODUCTS.map((product) => (
              <div
                key={product.nameKey}
                className={
                  product.highlight
                    ? 'rounded-lg border border-[#06B6D4]/40 bg-[#1E293B] p-5 shadow-md shadow-[#06B6D4]/5'
                    : 'rounded-lg border border-[#334155] bg-[#1E293B] p-5 hover:border-[#94A3B8] transition-default'
                }
              >
                <div className="flex items-center gap-2 mb-2">
                  <span style={{ color: product.color }}>{product.icon}</span>
                  <h3 className="text-sm font-semibold text-[#F8FAFC]">
                    {t(product.nameKey)}
                  </h3>
                </div>
                <p className="text-xs text-[#94A3B8] leading-relaxed mb-3">
                  {t(product.descKey)}
                </p>
                {product.url && (
                  <a
                    href={product.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-[#06B6D4] hover:text-[#F8FAFC] transition-default"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {t('visit')}
                  </a>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ── Social links ── */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Heart className="h-5 w-5 text-[#EC4899]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">
              {t('connectTitle')}
            </h2>
          </div>

          <div className="flex flex-wrap gap-3">
            {SOCIALS.map((social) => (
              <a
                key={social.labelKey}
                href={social.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-2.5 text-sm text-[#94A3B8] hover:text-[#F8FAFC] hover:border-[#94A3B8] transition-default"
              >
                {social.icon}
                {t(social.labelKey)}
              </a>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
