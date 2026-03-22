'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { Phone, Scale, Home, Users, ExternalLink, Loader2 } from 'lucide-react';
import { fetchResources, type ResourceItem } from '@/lib/api';

// Fallback data used when the API is unavailable
const FALLBACK_RESOURCES: ResourceItem[] = [
  { id: 1, category: 'helpline', name: 'Child Protection & Welfare Bureau', description: 'Government helpline for child protection emergencies across Pakistan.', contact: '1099', url: null, sortOrder: 1 },
  { id: 2, category: 'helpline', name: 'Edhi Foundation', description: 'Emergency ambulance, rescue, and welfare services. 24/7 nationwide.', contact: '1098', url: null, sortOrder: 2 },
  { id: 3, category: 'helpline', name: 'Roshni Helpline', description: 'Counseling and referral service for children and women in distress.', contact: '0800-22444', url: null, sortOrder: 3 },
  { id: 4, category: 'helpline', name: 'Pakistan Bait-ul-Mal', description: 'Government social safety net for vulnerable populations.', contact: '0800-12345', url: null, sortOrder: 4 },
  { id: 5, category: 'legal_aid', name: 'Legal Aid Society', description: 'Free legal representation for underprivileged victims of trafficking and exploitation.', contact: '021-35837825', url: 'https://www.las.org.pk', sortOrder: 1 },
  { id: 6, category: 'legal_aid', name: 'AGHS Legal Aid Cell', description: 'Pro bono legal services for human rights cases, including child trafficking.', contact: '042-35761999', url: null, sortOrder: 2 },
  { id: 7, category: 'legal_aid', name: 'Digital Rights Foundation', description: 'Legal support for technology-facilitated crimes against children.', contact: '0800-39393', url: 'https://digitalrightsfoundation.pk', sortOrder: 3 },
  { id: 8, category: 'shelter', name: 'Edhi Homes', description: 'Shelter and care for abandoned, orphaned, and at-risk children nationwide.', contact: '1098', url: null, sortOrder: 1 },
  { id: 9, category: 'shelter', name: "SOS Children's Villages", description: 'Long-term family-based care for orphaned and abandoned children.', contact: '051-2604841', url: 'https://www.sos.org.pk', sortOrder: 2 },
  { id: 10, category: 'shelter', name: 'Dar-ul-Aman Shelter Homes', description: 'Government-run shelter homes for women and children in distress.', contact: 'Contact local district office', url: null, sortOrder: 3 },
  { id: 11, category: 'ngo', name: 'SPARC', description: 'Research, advocacy, and direct services for child rights in Pakistan.', contact: '051-2278596', url: 'https://www.sparcpk.org', sortOrder: 1 },
  { id: 12, category: 'ngo', name: 'Sahil', description: 'NGO focused on child sexual abuse prevention, research, and data.', contact: '051-2890505', url: 'https://sahil.org', sortOrder: 2 },
  { id: 13, category: 'ngo', name: 'Group Development Pakistan', description: 'Community-based organization working on bonded labor and child labor.', contact: '042-35913308', url: null, sortOrder: 3 },
  { id: 14, category: 'ngo', name: 'Bachpan Bachao Andolan', description: 'Grassroots campaigns against child labor and trafficking.', contact: 'Contact via website', url: null, sortOrder: 4 },
];

interface SectionConfig {
  category: string;
  title: string;
  icon: React.ReactNode;
  iconColor: string;
}

const SECTIONS: SectionConfig[] = [
  { category: 'helpline', title: 'Emergency Helplines', icon: <Phone className="h-5 w-5" />, iconColor: '#EF4444' },
  { category: 'legal_aid', title: 'Legal Aid', icon: <Scale className="h-5 w-5" />, iconColor: '#F59E0B' },
  { category: 'shelter', title: 'Shelter Homes', icon: <Home className="h-5 w-5" />, iconColor: '#10B981' },
  { category: 'ngo', title: 'NGO Contacts', icon: <Users className="h-5 w-5" />, iconColor: '#06B6D4' },
];

function ResourceSection({ config, items }: { config: SectionConfig; items: ResourceItem[] }) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <div style={{ color: config.iconColor }}>{config.icon}</div>
        <h2 className="text-lg font-semibold text-[#F8FAFC]">{config.title}</h2>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 hover:border-[#94A3B8] transition-default"
          >
            <h3 className="text-sm font-semibold text-[#F8FAFC] mb-1">{item.name}</h3>
            {item.description && (
              <p className="text-xs text-[#94A3B8] mb-3 line-clamp-2">{item.description}</p>
            )}
            <div className="flex items-center justify-between">
              {item.contact && (
                <a
                  href={`tel:${item.contact.replace(/[^0-9+]/g, '')}`}
                  className="text-sm font-mono font-medium text-[#06B6D4] hover:underline"
                >
                  {item.contact}
                </a>
              )}
              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#94A3B8] hover:text-[#F8FAFC] transition-default"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function ResourcesPage() {
  const { data: apiResources, isLoading } = useQuery({
    queryKey: ['resources'],
    queryFn: () => fetchResources(),
  });

  // Use API data if available, fall back to hardcoded data
  const resources = apiResources && apiResources.length > 0 ? apiResources : FALLBACK_RESOURCES;

  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#F8FAFC] mb-1">
            Resources & Helplines
          </h1>
          <p className="text-sm text-[#94A3B8]">
            Emergency contacts, legal aid, shelter homes, and NGO support for child protection in Pakistan.
          </p>
        </div>

        {/* Emergency banner */}
        <div className="rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/5 p-4 mb-8">
          <div className="flex items-center gap-2 mb-2">
            <Phone className="h-5 w-5 text-[#EF4444]" />
            <p className="text-sm font-semibold text-[#F8FAFC]">In an emergency, call immediately:</p>
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <a href="tel:1099" className="font-mono font-bold text-[#EF4444] hover:underline">1099 — Child Protection</a>
            <a href="tel:1098" className="font-mono font-bold text-[#EF4444] hover:underline">1098 — Edhi</a>
            <a href="tel:080022444" className="font-mono font-bold text-[#EF4444] hover:underline">0800-22444 — Roshni</a>
          </div>
        </div>

        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-[#94A3B8]" />
          </div>
        ) : (
          SECTIONS.map((config) => {
            const items = resources.filter((r) => r.category === config.category);
            if (items.length === 0) return null;
            return <ResourceSection key={config.category} config={config} items={items} />;
          })
        )}
      </main>

      <Footer />
    </div>
  );
}
