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
  },
  testMatch: [
    '**/__tests__/**/*.test.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],
  transformIgnorePatterns: [
    'node_modules/(?!(unified|remark-parse|remark-gfm|remark-directive|remark-rehype|rehype-highlight|rehype-stringify|micromark|unist-util-visit|unist-util-is|unist-util-visit-parents|mdast-util-from-markdown|mdast-util-to-string|mdast-util-gfm|mdast-util-to-hast|mdast-util-directive|micromark-util-types|micromark-factory-space|micromark-factory-whitespace|hast-util-to-html|micromark-extension-gfm|decode-named-character-reference|character-entities|vfile|bail|is-plain-obj|trough|@types)/)',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
