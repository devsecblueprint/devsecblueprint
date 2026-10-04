const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@/components/MarkdownRenderer$': '<rootDir>/__mocks__/MarkdownRenderer.tsx',
  },
  testMatch: [
    '**/__tests__/**/*.test.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],
  // Coverage: emit lcov (consumed by SonarQube) + a console summary.
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['lcov', 'text-summary'],
  // Coverage ratchet: a local regression guard, NOT the project's 80% target —
  // that gate lives in SonarQube (sonar-project.properties). These sit a couple
  // points under the CI actuals so the guard can't be stricter than the
  // environment that runs it. CI's jsdom has no global `fetch`, so a few
  // fetch-on-mount components execute fewer lines there than on a local Node
  // with native fetch (~0.6-0.8pt lower across metrics). Thresholds are keyed
  // to the CI numbers, with margin. Raise only (ratchet UP, never lower).
  coverageThreshold: {
    global: {
      statements: 76,
      branches: 63,
      functions: 74,
      lines: 77,
    },
  },
  // Measure coverage over real source only, using the SAME denominator as
  // SonarQube (sonar.coverage.exclusions). SonarQube is the coverage gate, so
  // jest's scope mirrors it: all route `page.tsx`/`layout.tsx` are excluded
  // (declarative route composition in a static-export content site), along with
  // scripts, config, type declarations, mocks, and generated data.
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    'hooks/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    // Mirror sonar.coverage.exclusions: exclude all route entrypoints.
    '!app/**/page.tsx',
    '!app/**/layout.tsx',
    '!**/*.config.{js,ts}',
    '!scripts/**',
    '!jest.setup.js',
    // Generated data and mocks are not meaningful to cover.
    '!lib/walkthroughs-data.ts',
    '!lib/curriculum-data.ts',
    '!lib/data/**',
    '!**/__mocks__/**',
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(unified|remark[^/]*|rehype[^/]*|hast[^/]*|mdast[^/]*|micromark[^/]*|unist[^/]*|vfile[^/]*|bail|is-plain-obj|trough|devlop|property-information|comma-separated-tokens|space-separated-tokens|stringify-entities|parse-entities|character-reference-invalid|character-entities[^/]*|is-decimal|is-hexadecimal|is-alphanumerical|is-alphabetical|ccount|escape-string-regexp|markdown-table|longest-streak|zwitch|html-void-elements|web-namespaces|trim-lines|decode-named-character-reference|lowlight|highlight\\.js|fault|@types)/)',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = async () => {
  const jestConfig = await createJestConfig(customJestConfig)()
  // Override transformIgnorePatterns since next/jest may override our custom patterns
  jestConfig.transformIgnorePatterns = customJestConfig.transformIgnorePatterns
  return jestConfig
}
