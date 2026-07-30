'use client';

import { SPONSORSHIP_FAQ } from '@/lib/data/sponsorship-data';
import { Accordion, type AccordionItem } from '@/components/ui/Accordion';

interface SponsorshipFAQProps {
  className?: string;
}

export function SponsorshipFAQ({ className }: SponsorshipFAQProps) {
  const items: AccordionItem[] = SPONSORSHIP_FAQ.map((item) => ({
    id: item.id,
    trigger: item.question,
    content: item.answer,
  }));

  return <Accordion items={items} className={className} />;
}
