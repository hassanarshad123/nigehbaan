'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { Phone, Scale, Home, Users, ExternalLink } from 'lucide-react';

interface ResourceCard {
  name: string;
  description: string;
  contact: string;
  url?: string;
}

const HELPLINES: ResourceCard[] = [
  {
    name: 'Child Protection & Welfare Bureau',
    description: 'Government helpline for child protection emergencies across Pakistan.',
    contact: '1099',
  },
  {
    name: 'Edhi Foundation',
    description: 'Emergency ambulance, rescue, and welfare services. 24/7 nationwide.',
    contact: '1098',
  },
  {
    name: 'Roshni Helpline',
    description: 'Counseling and referral service for children and women in distress.',
    contact: '0800-22444',
  },
  {
    name: 'Pakistan Bait-ul-Mal',
    description: 'Government social safety net for vulnerable populations.',
    contact: '0800-12345',
  },
  {
    name: 'Women Crisis Centre',
    description: 'Support for women and children facing violence or exploitation.',
    contact: '0800-22444',
  },
];

const LEGAL_AID: ResourceCard[] = [
  {
    name: 'Legal Aid Society',
    description: 'Free legal representation for underprivileged victims of trafficking and exploitation.',
    contact: '021-35837825',
    url: 'https://www.las.org.pk',
  },
  {
    name: 'AGHS Legal Aid Cell',
    description: 'Pro bono legal services for human rights cases, including child trafficking.',
    contact: '042-35761999',
  },
  {
    name: 'Digital Rights Foundation',
    description: 'Legal support for technology-facilitated crimes against children.',
    contact: '0800-39393',
    url: 'https://digitalrightsfoundation.pk',
  },
];

const SHELTER_HOMES: ResourceCard[] = [
  {
    name: 'Edhi Homes',
    description: 'Shelter and care for abandoned, orphaned, and at-risk children nationwide.',
    contact: '1098',
  },
  {
    name: 'SOS Children\'s Villages',
    description: 'Long-term family-based care for orphaned and abandoned children.',
    contact: '051-2604841',
    url: 'https://www.sos.org.pk',
  },
  {
    name: 'Dar-ul-Aman Shelter Homes',
    description: 'Government-run shelter homes for women and children in distress.',
    contact: 'Contact local district office',
  },
];

const NGO_CONTACTS: ResourceCard[] = [
  {
    name: 'SPARC (Society for the Protection of the Rights of the Child)',
    description: 'Research, advocacy, and direct services for child rights in Pakistan.',
    contact: '051-2278596',
    url: 'https://www.sparcpk.org',
  },
  {
    name: 'Sahil',
    description: 'NGO focused on child sexual abuse prevention, research, and data.',
    contact: '051-2890505',
    url: 'https://sahil.org',
  },
  {
    name: 'Group Development Pakistan',
    description: 'Community-based organization working on bonded labor and child labor.',
    contact: '042-35913308',
  },
  {
    name: 'Bachpan Bachao Andolan (Save Childhood Movement)',
    description: 'Grassroots campaigns against child labor and trafficking.',
    contact: 'Contact via website',
  },
];

interface ResourceSectionProps {
  title: string;
  icon: React.ReactNode;
  items: ResourceCard[];
  iconColor: string;
}

function ResourceSection({ title, icon, items, iconColor }: ResourceSectionProps) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <div style={{ color: iconColor }}>{icon}</div>
        <h2 className="text-lg font-semibold text-[#F8FAFC]">{title}</h2>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.name}
            className="rounded-lg border border-[#334155] bg-[#1E293B] p-4 hover:border-[#94A3B8] transition-default"
          >
            <h3 className="text-sm font-semibold text-[#F8FAFC] mb-1">{item.name}</h3>
            <p className="text-xs text-[#94A3B8] mb-3 line-clamp-2">{item.description}</p>
            <div className="flex items-center justify-between">
              <a
                href={`tel:${item.contact.replace(/[^0-9+]/g, '')}`}
                className="text-sm font-mono font-medium text-[#06B6D4] hover:underline"
              >
                {item.contact}
              </a>
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
  return (
    <div className="min-h-screen bg-[#0F172A]">
      <Header />

      <main className="mx-auto max-w-screen-xl px-4 pt-16 pb-8">
        {/* Page header */}
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
            <p className="text-sm font-semibold text-[#F8FAFC]">
              In an emergency, call immediately:
            </p>
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            <a href="tel:1099" className="font-mono font-bold text-[#EF4444] hover:underline">
              1099 — Child Protection
            </a>
            <a href="tel:1098" className="font-mono font-bold text-[#EF4444] hover:underline">
              1098 — Edhi
            </a>
            <a href="tel:080022444" className="font-mono font-bold text-[#EF4444] hover:underline">
              0800-22444 — Roshni
            </a>
          </div>
        </div>

        <ResourceSection
          title="Emergency Helplines"
          icon={<Phone className="h-5 w-5" />}
          items={HELPLINES}
          iconColor="#EF4444"
        />

        <ResourceSection
          title="Legal Aid"
          icon={<Scale className="h-5 w-5" />}
          items={LEGAL_AID}
          iconColor="#F59E0B"
        />

        <ResourceSection
          title="Shelter Homes"
          icon={<Home className="h-5 w-5" />}
          items={SHELTER_HOMES}
          iconColor="#10B981"
        />

        <ResourceSection
          title="NGO Contacts"
          icon={<Users className="h-5 w-5" />}
          items={NGO_CONTACTS}
          iconColor="#06B6D4"
        />
      </main>

      <Footer />
    </div>
  );
}
