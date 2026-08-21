/**
 * Maps curriculum module names (from curriculum-data.ts) to their
 * corresponding public preview page slugs.
 *
 * Used by the ModuleCard component to add "Preview" links on the
 * public curriculum page.
 */

/** Map of module name → preview slug (module ID with / replaced by --) */
const MODULE_PREVIEW_MAP: Record<string, string> = {
  // Stage 1: Know Before You Go
  'Prerequisites': 'know_before_you_go--prerequisites',
  'Soft Skills': 'know_before_you_go--soft_skills',

  // Stage 2: DevSecOps
  'What is the Secure SDLC?': 'devsecops--what_is_the_secure_sdlc',
  'What is Application Security?': 'devsecops--what_is_application_security',
  'Secure Coding Overview': 'devsecops--secure_coding_overview',
  'DevSecOps Fundamentals': 'devsecops--devsecops_fundamentals',
  'Threat Modeling Fundamentals': 'devsecops--threat_modeling_fundamentals',
  'Container Security Overview': 'devsecops--container_security_overview',
  'DevSecOps Capstone': 'devsecops--capstone',

  // Stage 2 (parallel): Cloud Security Development
  'What is Cloud Security Development?': 'cloud_security_development--what_is_cloud_security_development',
  'IAM Fundamentals': 'cloud_security_development--iam_fundamentals',
  'API Patterns and SDKs': 'cloud_security_development--api_patterns_and_sdks',
  'Secrets Management In The Cloud': 'cloud_security_development--secrets_management_in_the_cloud',
  'Cloud Logging and Monitoring': 'cloud_security_development--cloud_logging_and_monitoring',
  'Serverless': 'cloud_security_development--serverless',
  'IaC Security': 'cloud_security_development--iac_security',
  'Cloud Security Development Capstone': 'cloud_security_development--capstone',

  // Stage 3: Career Strategy
  'Career Strategy': 'career_strategy--career_strategy',
};

/**
 * Get the preview URL for a curriculum module by its display name.
 * Returns undefined if no matching preview exists.
 */
export function getModulePreviewUrl(moduleName: string): string | undefined {
  const slug = MODULE_PREVIEW_MAP[moduleName];
  return slug ? `/courses/preview/${slug}` : undefined;
}
