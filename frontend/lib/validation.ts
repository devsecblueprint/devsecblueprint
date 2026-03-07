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
