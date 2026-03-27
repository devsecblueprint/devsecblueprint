/**
 * Validates a GitHub repository URL against the authenticated user's username.
 * 
 * @param url - The GitHub repository URL to validate
 * @param username - The expected GitHub username (from authenticated user)
 * @returns Validation result with error message if invalid
 */
export function validateGitHubUrl(
  url: string,
  username: string
): { valid: boolean; error?: string } {
  // GitHub URL pattern: supports http/https, with/without www
  const githubUrlPattern = /^https?:\/\/(www\.)?github\.com\/([^\/]+)\/([^\/]+)\/?$/;
  const match = url.match(githubUrlPattern);

  if (!match) {
    return { valid: false, error: "Invalid GitHub URL format" };
  }

  const urlUsername = match[2];

  // Case-insensitive username comparison
  if (urlUsername.toLowerCase() !== username.toLowerCase()) {
    return {
      valid: false,
      error: `Repository must be under your GitHub account (${username})`,
    };
  }

  return { valid: true };
}

/**
 * Validates a repository URL against the authenticated user's provider and username.
 * Supports both GitHub and GitLab repository URLs.
 *
 * @param url - The repository URL to validate
 * @param provider - The authentication provider ("github" or "gitlab")
 * @param username - The expected provider username (from authenticated user)
 * @returns Validation result with error message if invalid
 */
export function validateRepoUrl(
  url: string,
  provider: "github" | "gitlab" | "bitbucket",
  username: string
): { valid: boolean; error?: string } {
  const patterns: Record<string, { regex: RegExp; domain: string }> = {
    github: {
      regex: /^https?:\/\/(www\.)?github\.com\/([^\/]+)\/([^\/]+)\/?$/,
      domain: "GitHub",
    },
    gitlab: {
      regex: /^https?:\/\/(www\.)?gitlab\.com\/([^\/]+)\/([^\/]+)\/?$/,
      domain: "GitLab",
    },
    bitbucket: {
      regex: /^https?:\/\/(www\.)?bitbucket\.org\/([^\/]+)\/([^\/]+)\/?$/,
      domain: "Bitbucket",
    },
  };

  const { regex, domain } = patterns[provider];
  const match = url.match(regex);

  if (!match) {
    return { valid: false, error: `Invalid ${domain} URL format` };
  }

  // Bitbucket repos live under workspaces, not usernames — skip ownership check
  if (provider === "bitbucket") {
    return { valid: true };
  }

  const urlUsername = match[2];

  if (urlUsername.toLowerCase() !== username.toLowerCase()) {
    return {
      valid: false,
      error: `Repository must be under your ${domain} account (${username})`,
    };
  }

  return { valid: true };
}
