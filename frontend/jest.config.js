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
  transformIgnorePatterns: [
    'node_modules/(?!(unified|remark[^/]*|rehype[^/]*|hast[^/]*|mdast[^/]*|micromark[^/]*|unist[^/]*|vfile[^/]*|bail|is-plain-obj|trough|devlop|property-information|comma-separated-tokens|space-separated-tokens|stringify-entities|ccount|escape-string-regexp|markdown-table|longest-streak|zwitch|html-void-elements|web-namespaces|trim-lines|decode-named-character-reference|character-entities[^/]*|lowlight|highlight\\.js|fault|@types)/)',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = async () => {
  const jestConfig = await createJestConfig(customJestConfig)()
  // Override transformIgnorePatterns since next/jest may override our custom patterns
  jestConfig.transformIgnorePatterns = customJestConfig.transformIgnorePatterns
  return jestConfig
}
