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
  // Coverage ratchet: thresholds sit just below current coverage so CI stays
  // green while preventing regressions. Raise toward the 80% SonarQube target
  // as coverage grows (ratchet UP only — never lower). Current coverage on the
  // Sonar-aligned scope is ~15.4% lines; thresholds are set just under that.
  coverageThreshold: {
    global: {
      statements: 14,
      branches: 13,
      functions: 11,
      lines: 15,
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
