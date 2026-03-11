import { CurriculumStage } from './types';

export const CURRICULUM_STAGES: CurriculumStage[] = [
  {
    id: 'stage-1',
    name: 'Know Before You Go',
    description: 'Essential prerequisites and foundational knowledge',
    moduleCount: 2,
    stageNumber: 1,
    modules: [
      {
        id: 'module-1-1',
        name: 'Prerequisites',
        description: 'Essential knowledge and skills needed before starting',
        topics: [
          'Git and version control',
          'Programming concepts',
          'Linux and Bash scripting',
          'Networking fundamentals',
          'Security fundamentals',
          'DevOps philosophy',
          'CI/CD pipelines',
          'Cloud computing basics'
        ]
      },
      {
        id: 'module-1-2',
        name: 'Soft Skills',
        description: 'Professional skills for success in DevSecOps',
        topics: [
          'Communication with engineering teams',
          'Problem solving frameworks',
          'Root cause analysis',
          'Security leadership and influence',
          'Collaboration and teamwork',
          'Technical writing',
          'Stakeholder management'
        ]
      }
    ]
  },
  {
    id: 'stage-2',
    name: 'DevSecOps',
    description: 'Integrating security into the development lifecycle',
    moduleCount: 6,
    stageNumber: 2,
    modules: [
      {
        id: 'module-2-1',
        name: 'What is the Secure SDLC?',
        description: 'Understanding the Secure Software Development Lifecycle',
        topics: [
          'Traditional SDLC vs Secure SDLC',
          'Shift-left security',
          'Security checkpoints in development',
          'Integrating security into pipelines'
        ]
      },
      {
        id: 'module-2-2',
        name: 'What is Application Security?',
        description: 'Understanding application security basics and why it matters',
        topics: [
          'Application security fundamentals',
          'SAST vs DAST',
          'Software composition analysis',
          'Common application vulnerabilities',
          'Secure development practices'
        ]
      },
      {
        id: 'module-2-3',
        name: 'Secure Coding Overview',
        description: 'Best practices for writing secure code',
        topics: [
          'Secure coding principles',
          'Common security vulnerabilities',
          'Input validation',
          'Safe error handling',
          'Secure dependency usage'
        ]
      },
      {
        id: 'module-2-4',
        name: 'DevSecOps Fundamentals',
        description: 'Core concepts and principles of DevSecOps',
        topics: [
          'DevOps vs DevSecOps',
          'Security automation',
          'Pipeline security concepts',
          'Security ownership within engineering teams',
          'Continuous feedback and monitoring'
        ],
        submodules: [
          { id: 'devsecops_fundamentals_module_1', title: 'The Hidden Fracture', moduleNumber: 1, readingTime: 2 },
          { id: 'devsecops_fundamentals_module_2', title: 'The Four Pillars', moduleNumber: 2, readingTime: 2 },
          { id: 'devsecops_fundamentals_module_3', title: 'The Visual Archive', moduleNumber: 3, readingTime: 1 },
          { id: 'devsecops_fundamentals_module_4', title: 'The Pro\'s Bookshelf', moduleNumber: 4, readingTime: 3 },
          { id: 'devsecops_fundamentals_module_5', title: 'The Integration Mission', moduleNumber: 5, readingTime: 1 }
        ]
      },
      {
        id: 'module-2-5',
        name: 'Threat Modeling Fundamentals',
        description: 'Learn to identify, analyze, and mitigate security threats through systematic threat modeling',
        topics: [
          'Identifying attack surfaces',
          'Threat modeling methodologies',
          'Risk prioritization',
          'Designing secure architectures'
        ]
      },
      {
        id: 'module-2-6',
        name: 'Container Security Overview',
        description: 'Secure containerized applications and orchestration platforms from development to production',
        topics: [
          'Container isolation',
          'Image security',
          'Dependency risks',
          'Runtime protection concepts',
          'Build, ship, and run security'
        ]
      }
    ]
  },
  {
    id: 'stage-3',
    name: 'Cloud Security Development',
    description: 'Building secure applications in the cloud',
    moduleCount: 7,
    stageNumber: 2,
    modules: [
      {
        id: 'module-3-1',
        name: 'What is Cloud Security Development?',
        description: 'Defining Cloud Security Development and why it is essential for the modern landscape',
        topics: [
          'Cloud-native security principles',
          'Security engineering in cloud platforms',
          'Infrastructure automation and security integration'
        ]
      },
      {
        id: 'module-3-2',
        name: 'IAM Fundamentals',
        description: 'Understanding the fundamental role of IAM as the backbone of cloud security',
        topics: [
          'Identity and access management models',
          'Roles vs users',
          'Policy design',
          'Least privilege architecture'
        ],
        submodules: [
          { id: 'iam_fundamentals_module_1', title: 'The Gatekeeper', moduleNumber: 1, readingTime: 1 },
          { id: 'iam_fundamentals_module_2', title: 'The Cracks in the Key', moduleNumber: 2, readingTime: 1 },
          { id: 'iam_fundamentals_module_3', title: 'The IAM Lifecycle', moduleNumber: 3, readingTime: 1 },
          { id: 'iam_fundamentals_module_4', title: 'Best Practices & Providers', moduleNumber: 4, readingTime: 1 },
          { id: 'iam_fundamentals_module_5', title: 'The Master Key Library', moduleNumber: 5, readingTime: 2 },
          { id: 'iam_fundamentals_module_6', title: 'The Hardening Mission', moduleNumber: 6, readingTime: 1 }
        ]
      },
      {
        id: 'module-3-3',
        name: 'API Patterns and SDKs',
        description: 'Understanding how APIs and SDKs enable cloud security development at scale',
        topics: [
          'Secure API design',
          'Authentication models',
          'SDK security considerations',
          'API abuse prevention'
        ]
      },
      {
        id: 'module-3-4',
        name: 'Secrets Management In The Cloud',
        description: 'Securely storing, accessing, and distributing sensitive credentials across your systems',
        topics: [
          'Secrets management strategies',
          'Secret rotation',
          'Secure storage practices',
          'Avoiding credential leakage'
        ]
      },
      {
        id: 'module-3-5',
        name: 'Cloud Logging and Monitoring',
        description: 'Understanding how logs and events form the foundation of cloud detection and trust',
        topics: [
          'Observability for security',
          'Log pipelines',
          'Threat detection signals',
          'Security monitoring strategies'
        ]
      },
      {
        id: 'module-3-6',
        name: 'Serverless',
        description: 'Understanding how serverless computing and orchestration enable cloud-native security',
        topics: [
          'Event-driven architectures',
          'Lambda security patterns',
          'Runtime isolation',
          'Permission boundaries'
        ]
      },
      {
        id: 'module-3-7',
        name: 'IaC Security',
        description: 'Defining Infrastructure as Code and its critical role in cloud security',
        topics: [
          'Terraform security practices',
          'Preventing misconfigurations',
          'Policy enforcement',
          'Infrastructure scanning'
        ]
      }
    ]
  },
  {
    id: 'stage-4',
    name: 'Capstone Projects',
    description: 'Apply everything you\'ve learned through real-world engineering scenarios. Build complete systems with security integrated from design through deployment.',
    stageNumber: 3,
    projects: [
      'DevSecOps Capstone: Build an automated security pipeline',
      'Cloud Security Development Capstone: Build a self-healing cloud environment'
    ]
  }
];
