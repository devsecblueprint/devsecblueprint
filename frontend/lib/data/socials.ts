export interface SocialLink {
  label: string;
  url: string;
  icon: 'github' | 'discord' | 'linkedin' | 'x' | 'facebook' | 'instagram' | 'tiktok';
  description: string;
}

export const SOCIAL_LINKS: SocialLink[] = [
  {
    label: 'GitHub',
    url: 'https://github.com/devsecblueprint/devsecblueprint',
    icon: 'github',
    description: 'Explore our open-source projects and contribute',
  },
  {
    label: 'Discord',
    url: 'https://discord.gg/SkYECC4TD8',
    icon: 'discord',
    description: 'Join 2k+ builders in the community',
  },
  {
    label: 'LinkedIn',
    url: 'https://www.linkedin.com/company/devsecblueprint',
    icon: 'linkedin',
    description: 'Professional updates and career content',
  },

  {
    label: 'X',
    url: 'https://x.com/devsecblueprint',
    icon: 'x',
    description: 'Quick tips and industry commentary',
  },
  {
    label: 'Facebook',
    url: 'https://www.facebook.com/people/The-DevSec-Blueprint/61593406525237/',
    icon: 'facebook',
    description: 'Community highlights and announcements',
  },
  {
    label: 'Instagram',
    url: 'https://www.instagram.com/devsecblueprint',
    icon: 'instagram',
    description: 'Behind-the-scenes and visual content',
  },
  {
    label: 'TikTok',
    url: 'https://www.tiktok.com/@devsecblueprint',
    icon: 'tiktok',
    description: 'Bite-sized security and DevOps content',
  },
];
