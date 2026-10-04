/**
 * Unit tests for lib/validation.ts — testimonial and repository URL validators.
 */
import {
  validateDisplayName,
  validateLinkedInUrl,
  validateQuote,
  validateGitHubUrl,
  validateRepoUrl,
} from '@/lib/validation';

describe('validateDisplayName', () => {
  it('returns null for a valid name', () => {
    expect(validateDisplayName('Ada Lovelace')).toBeNull();
  });

  it('rejects an empty string', () => {
    expect(validateDisplayName('')).toMatch(/required/);
  });

  it('rejects a whitespace-only string', () => {
    expect(validateDisplayName('   ')).toMatch(/required/);
  });
});

describe('validateLinkedInUrl', () => {
  it('accepts an empty value (optional field)', () => {
    expect(validateLinkedInUrl('')).toBeNull();
  });

  it('accepts a canonical linkedin profile url', () => {
    expect(validateLinkedInUrl('https://linkedin.com/in/ada-lovelace')).toBeNull();
  });

  it('accepts a www-prefixed profile url with trailing slash', () => {
    expect(validateLinkedInUrl('https://www.linkedin.com/in/ada_lovelace/')).toBeNull();
  });

  it('rejects a non-linkedin url', () => {
    expect(validateLinkedInUrl('https://example.com/in/ada')).toMatch(/linkedin_url/);
  });

  it('rejects an http (non-https) linkedin url', () => {
    expect(validateLinkedInUrl('http://linkedin.com/in/ada')).toMatch(/linkedin_url/);
  });

  it('rejects a company url rather than a profile url', () => {
    expect(validateLinkedInUrl('https://linkedin.com/company/acme')).toMatch(/linkedin_url/);
  });
});

describe('validateQuote', () => {
  it('returns null for a reasonable quote', () => {
    expect(validateQuote('This program changed my career.')).toBeNull();
  });

  it('rejects an empty quote', () => {
    expect(validateQuote('')).toMatch(/required/);
  });

  it('rejects a whitespace-only quote', () => {
    expect(validateQuote('    ')).toMatch(/required/);
  });

  it('accepts a quote at exactly the 350 char limit', () => {
    expect(validateQuote('a'.repeat(350))).toBeNull();
  });

  it('rejects a quote exceeding 350 chars and reports the length', () => {
    const result = validateQuote('a'.repeat(351));
    expect(result).toMatch(/exceeds maximum of 350/);
    expect(result).toMatch(/351/);
  });

  it('trims before counting so trailing whitespace does not push over the limit', () => {
    expect(validateQuote('a'.repeat(350) + '    ')).toBeNull();
  });
});

describe('validateGitHubUrl', () => {
  it('accepts a repo owned by the user', () => {
    expect(validateGitHubUrl('https://github.com/ada/project', 'ada')).toEqual({
      valid: true,
    });
  });

  it('is case-insensitive on the username', () => {
    expect(validateGitHubUrl('https://github.com/Ada/project', 'ada').valid).toBe(true);
  });

  it('accepts http and www variants', () => {
    expect(validateGitHubUrl('http://www.github.com/ada/project', 'ada').valid).toBe(true);
  });

  it('rejects a malformed url', () => {
    const result = validateGitHubUrl('not-a-url', 'ada');
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/Invalid GitHub URL/);
  });

  it('rejects a repo owned by someone else', () => {
    const result = validateGitHubUrl('https://github.com/someone-else/project', 'ada');
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/under your GitHub account \(ada\)/);
  });
});

describe('validateRepoUrl', () => {
  it('validates a github repo under the user', () => {
    expect(validateRepoUrl('https://github.com/ada/x', 'github', 'ada').valid).toBe(true);
  });

  it('validates a gitlab repo under the user', () => {
    expect(validateRepoUrl('https://gitlab.com/ada/x', 'gitlab', 'ada').valid).toBe(true);
  });

  it('rejects a gitlab repo under a different user with provider-specific message', () => {
    const result = validateRepoUrl('https://gitlab.com/other/x', 'gitlab', 'ada');
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/GitLab account \(ada\)/);
  });

  it('skips ownership check for bitbucket (workspace-based)', () => {
    expect(validateRepoUrl('https://bitbucket.org/any-workspace/x', 'bitbucket', 'ada').valid).toBe(
      true,
    );
  });

  it('rejects a url that does not match the provider domain', () => {
    const result = validateRepoUrl('https://github.com/ada/x', 'gitlab', 'ada');
    expect(result.valid).toBe(false);
    expect(result.error).toMatch(/Invalid GitLab URL/);
  });
});
