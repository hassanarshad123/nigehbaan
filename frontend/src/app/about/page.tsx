'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import {
  Target,
  FlaskConical,
  Database,
  Users,
  Shield,
  Globe,
  Newspaper,
  Scale,
  FileText,
} from 'lucide-react';

const DATA_SOURCES = [
  { name: 'Media Reports', description: 'Monitored from 50+ Urdu and English media outlets', icon: <Newspaper className="h-5 w-5" /> },
  { name: 'Court Records', description: 'High Court and Supreme Court judgments on trafficking cases', icon: <Scale className="h-5 w-5" /> },
  { name: 'NGO Assessments', description: 'Sahil, SPARC, and other child-rights organizations', icon: <Users className="h-5 w-5" /> },
  { name: 'Government Data', description: 'FIR records, CPWB reports, and population statistics', icon: <FileText className="h-5 w-5" /> },
  { name: 'Satellite Imagery', description: 'Brick kiln detection via remote sensing analysis', icon: <Globe className="h-5 w-5" /> },
  { name: 'Citizen Reports', description: 'Anonymous tips and community-submitted observations', icon: <Shield className="h-5 w-5" /> },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-lg px-4 pt-16 pb-8">
        {/* Hero */}
        <div className="mb-12 text-center">
          <p className="font-urdu text-3xl text-[#06B6D4] mb-2">نگہبان</p>
          <h1 className="text-3xl font-bold text-[#F8FAFC] mb-3">
            About Nigehbaan
          </h1>
          <p className="text-lg text-[#94A3B8]">
            Guardian — Open-source geospatial intelligence for child protection
          </p>
        </div>

        {/* Mission */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Target className="h-5 w-5 text-[#06B6D4]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">Mission</h2>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            <p className="text-sm text-[#94A3B8] leading-relaxed">
              Nigehbaan (&ldquo;guardian&rdquo; in Urdu) is an open-source geospatial
              intelligence platform designed to shine a light on child trafficking
              patterns across Pakistan. By aggregating data from media reports,
              court records, NGO assessments, and citizen reports, Nigehbaan
              empowers researchers, journalists, law enforcement, and civil
              society to identify at-risk areas and advocate for policy change.
            </p>
            <p className="text-sm text-[#94A3B8] leading-relaxed mt-4">
              Pakistan faces an acute child protection crisis. An estimated 12
              million children are engaged in hazardous labor, with thousands
              trafficked annually for forced labor in brick kilns, domestic
              servitude, begging rings, and sexual exploitation. Despite
              legislative frameworks, conviction rates remain below 5%.
              Nigehbaan aims to bridge the data gap that hinders effective
              intervention.
            </p>
          </div>
        </section>

        {/* Methodology */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <FlaskConical className="h-5 w-5 text-[#10B981]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">Methodology</h2>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            <div className="space-y-4 text-sm text-[#94A3B8] leading-relaxed">
              <p>
                Nigehbaan follows a structured data pipeline:
              </p>
              <ol className="list-decimal list-inside space-y-2 ml-2">
                <li>
                  <strong className="text-[#F8FAFC]">Collection:</strong>{' '}
                  Automated scrapers and manual digitization gather data from
                  media, court records, and NGO publications.
                </li>
                <li>
                  <strong className="text-[#F8FAFC]">Geocoding:</strong>{' '}
                  Locations are resolved to district-level administrative
                  boundaries using Pakistan Bureau of Statistics PCODEs.
                </li>
                <li>
                  <strong className="text-[#F8FAFC]">Classification:</strong>{' '}
                  Incidents are categorized by type, victim demographics, and
                  source reliability using a standardized taxonomy.
                </li>
                <li>
                  <strong className="text-[#F8FAFC]">Validation:</strong>{' '}
                  Cross-referencing between multiple sources to reduce
                  duplication and improve accuracy.
                </li>
                <li>
                  <strong className="text-[#F8FAFC]">Analysis:</strong>{' '}
                  Geospatial analysis, trend detection, and vulnerability
                  scoring at the district level.
                </li>
              </ol>
            </div>
          </div>
        </section>

        {/* Data Sources */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Database className="h-5 w-5 text-[#F59E0B]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">Data Sources</h2>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {DATA_SOURCES.map((source) => (
              <div
                key={source.name}
                className="rounded-lg border border-[#334155] bg-[#1E293B] p-4"
              >
                <div className="flex items-center gap-2 mb-2 text-[#06B6D4]">
                  {source.icon}
                  <h3 className="text-sm font-semibold text-[#F8FAFC]">
                    {source.name}
                  </h3>
                </div>
                <p className="text-xs text-[#94A3B8]">{source.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Team */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-5 w-5 text-[#EC4899]" />
            <h2 className="text-xl font-semibold text-[#F8FAFC]">Team</h2>
          </div>
          <div className="rounded-lg border border-[#334155] bg-[#1E293B] p-6">
            <p className="text-sm text-[#94A3B8] leading-relaxed">
              Nigehbaan is developed and maintained by a multidisciplinary team
              of data scientists, GIS analysts, child protection researchers,
              and software engineers committed to using technology for social
              good. The project is fully open source and welcomes contributions
              from the community.
            </p>
            <p className="text-sm text-[#94A3B8] leading-relaxed mt-4">
              Built with support from the open-source community. If you&apos;re a
              developer, researcher, or domain expert interested in contributing,
              please reach out through our GitHub repository.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
