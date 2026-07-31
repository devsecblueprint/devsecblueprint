export interface SocialLink {
  platform: string;
  url: string;
}

export interface TeamMember {
  name: string;
  role: string;
  bio: string;
  highlights: string[];
  photoUrl?: string;
  socialLinks?: SocialLink[];
  isFounder: boolean;
  isAdvisor: boolean;
}

export const TEAM_MEMBERS: TeamMember[] = [
  {
    name: "Damien Burks",
    role: "Founder",
    bio: "Damien Burks is the Founder of The DevSec Blueprint, a cloud security engineer, international speaker, LinkedIn Learning instructor, and AWS Community Builder dedicated to transforming how people learn DevSecOps and cloud security. With experience building security guardrails, cloud platforms, CI/CD controls, and secure engineering systems across major technology and financial organizations, Damien created DSB to close the gap between theory and the real-world skills employers expect. His work centers on practical education, hands-on engineering, career development, and creating opportunities for technologists to build confidence, demonstrate their abilities, and develop lasting careers in security.",
    highlights: [
      "Cloud Security Engineering Leader: Builds security guardrails, secure cloud platforms, CI/CD controls, and scalable engineering systems across complex enterprise environments",
      "Founder & Curriculum Architect: Created The DevSec Blueprint to turn DevSecOps and cloud security theory into structured, hands-on learning built around real systems",
      "LinkedIn Learning Instructor & International Speaker: Teaches practical cloud security concepts and shares real-world engineering lessons with technical audiences worldwide",
      "AWS Community Builder & Career Advocate: Uses his experience, platform, and industry visibility to help technologists strengthen their skills, demonstrate their capabilities, and build lasting careers in security",
    ],
    photoUrl: "/team/damien-burks.jpeg",
    socialLinks: [
      { platform: "linkedin", url: "https://www.linkedin.com/in/damienjburks" },
    ],
    isFounder: true,
    isAdvisor: false,
  },
  {
    name: "Iman Crooks",
    role: "Head of Community & Member Experience",
    bio: "Iman Crooks is the Head of Community & Member Experience at The DevSec Blueprint, where she combines her background in cloud engineering, DevOps, gaming, mentorship, and workforce development to create a welcoming and career-focused community. As a career changer herself, she understands the challenges of breaking into technology and is passionate about helping members build confidence, meaningful connections, and lasting careers.",
    highlights: [
      "Cloud & DevOps Leader: Built and supported secure, scalable cloud infrastructure across FinTech and marketing technology environments",
      "Fortnite Contributor: Led QA efforts for Fortnite's Technical Art and Visual Effects teams, including the record-breaking Travis Scott Astronomical experience",
      "Career-Changer Advocate: Turned her own path into tech into a mission to mentor, guide, and open doors for the next generation of technologists",
      "Globally Minded Community Builder: Brings international perspective, technical credibility, and genuine empathy to creating spaces where members feel seen, supported, and empowered",
    ],
    photoUrl: "/team/iman-crooks.jpeg",
    socialLinks: [
      { platform: "linkedin", url: "https://www.linkedin.com/in/iman-crooks" },
    ],
    isFounder: false,
    isAdvisor: false,
  },
  {
    name: "Timothy Hogue",
    role: "Head of Technical Content and Programs",
    bio: "Alex brings extensive experience in cloud infrastructure security, helping design hands-on labs and walkthroughs that teach real-world security patterns.",
    highlights: [
      "Cloud security curriculum",
      "Lab environment design",
      "Technical reviews",
    ],
    isFounder: false,
    isAdvisor: false,
  }
];

export const ADVISORS: TeamMember[] = TEAM_MEMBERS.filter(
  (m) => m.isAdvisor
);

export const CORE_TEAM: TeamMember[] = TEAM_MEMBERS.filter(
  (m) => !m.isAdvisor
);
