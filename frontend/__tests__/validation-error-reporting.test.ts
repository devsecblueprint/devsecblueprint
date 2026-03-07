/**
 * Unit tests for Enhanced Validation Error Reporting
 * Tests Task 9.2: Implement validation error reporting
 * 
 * Validates Requirements 8.5:
 * - Report all validation errors with file paths
 * - Include specific error details (field name, invalid value)
 * - Provide actionable error messages
 */

import { 
  validateRegistry
} from '../scripts/generate-content-registry';
import type { ContentRegistry, QuizEntry } from '../scripts/generate-content-registry';

describe('Enhanced Validation Error Reporting - Task 9.2', () => {
  describe('File Path Reporting', () => {
    it('should include file paths in validation errors when provided', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'invalid-quiz': {
            content_type: 'quiz',
            topic_slug: 'invalid-quiz',
            module_id: 'test/invalid-quiz',
            passing_score: 150, // Invalid!
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. Only one'], // Invalid!
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const filePaths = new Map<string, string>();
      filePaths.set('invalid-quiz', 'content/test/invalid-quiz/quiz.md');

      const result = validateRegistry(registry, filePaths);
      
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      
      // All errors should have file paths
      result.errors.forEach(error => {
        expect(error.filePath).toBe('content/test/invalid-quiz/quiz.md');
      });
    });

    it('should handle missing file path mapping gracefully', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'invalid-quiz': {
            content_type: 'quiz',
            topic_slug: 'invalid-quiz',
            module_id: 'test/invalid-quiz',
            passing_score: 150, // Invalid!
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      // No file path mapping provided
      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      
      // Errors should still be reported, just without file paths
      expect(result.errors[0].message).toBeDefined();
      expect(result.errors[0].type).toBeDefined();
    });
  });

  describe('Field Name Reporting', () => {
    it('should include field names in validation errors', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 150, // Invalid!
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      
      // Find the passing_score error
      const passingScoreError = result.errors.find(e => e.type === 'INVALID_PASSING_SCORE_RANGE');
      expect(passingScoreError).toBeDefined();
      expect(passingScoreError?.field).toBe('passing_score');
    });

    it('should include specific field paths for nested errors', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 80,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. Only one'], // Invalid!
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      
      // Find the question options error
      const optionsError = result.errors.find(e => e.type === 'INSUFFICIENT_OPTIONS');
      expect(optionsError).toBeDefined();
      expect(optionsError?.field).toBe('questions[0].options');
    });
  });

  describe('Invalid Value Reporting', () => {
    it('should include invalid values in error details', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 150, // Invalid!
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      
      // Find the passing_score error
      const passingScoreError = result.errors.find(e => e.type === 'INVALID_PASSING_SCORE_RANGE');
      expect(passingScoreError).toBeDefined();
      expect(passingScoreError?.value).toBe(150);
    });

    it('should include invalid values for question structure errors', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 80,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. Only one'], // Invalid!
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      
      // Find the options error
      const optionsError = result.errors.find(e => e.type === 'INSUFFICIENT_OPTIONS');
      expect(optionsError).toBeDefined();
      expect(optionsError?.value).toBe(1); // Only 1 option found
    });
  });

  describe('Actionable Error Messages', () => {
    it('should provide clear, actionable error messages for passing_score', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 150,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      const passingScoreError = result.errors.find(e => e.type === 'INVALID_PASSING_SCORE_RANGE');
      expect(passingScoreError?.message).toContain('between 0 and 100');
      expect(passingScoreError?.message).toContain('150');
      expect(passingScoreError?.message).toContain('test-quiz');
    });

    it('should provide clear error messages for question structure', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'test-quiz': {
            content_type: 'quiz',
            topic_slug: 'test-quiz',
            module_id: 'test/test-quiz',
            passing_score: 80,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. Only one'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      const optionsError = result.errors.find(e => e.type === 'INSUFFICIENT_OPTIONS');
      expect(optionsError?.message).toContain('at least 2 options');
      expect(optionsError?.message).toContain('Question 1');
      expect(optionsError?.message).toContain('found 1');
    });

    it('should provide clear error messages for duplicate topic slugs', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'quiz1': {
            content_type: 'quiz',
            topic_slug: 'duplicate',
            module_id: 'path1/duplicate',
            passing_score: 80,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          },
          'quiz2': {
            content_type: 'quiz',
            topic_slug: 'duplicate',
            module_id: 'path2/duplicate',
            passing_score: 70,
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. 1', 'B. 2'],
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const result = validateRegistry(registry);
      
      const duplicateError = result.errors.find(e => e.type === 'DUPLICATE_TOPIC_SLUG');
      expect(duplicateError?.message).toContain('duplicate');
      expect(duplicateError?.message).toContain('quiz1');
      expect(duplicateError?.message).toContain('quiz2');
    });
  });

  describe('Complete Error Reporting', () => {
    it('should report all errors with complete information', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'invalid-quiz': {
            content_type: 'quiz',
            topic_slug: 'invalid-quiz',
            module_id: 'invalid', // Invalid format
            passing_score: 150, // Invalid range
            question_count: 1,
            questions: [{
              id: 'q1',
              question_text: 'Q?',
              options: ['A. Only one'], // Invalid - need at least 2
              correct_answer: 'A',
              explanation: 'E'
            }]
          }
        }
      };

      const filePaths = new Map<string, string>();
      filePaths.set('invalid-quiz', 'content/test/invalid-quiz/quiz.md');

      const result = validateRegistry(registry, filePaths);
      
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      
      // Verify each error has complete information
      result.errors.forEach(error => {
        // Should have error type
        expect(error.type).toBeDefined();
        expect(typeof error.type).toBe('string');
        
        // Should have message
        expect(error.message).toBeDefined();
        expect(typeof error.message).toBe('string');
        expect(error.message.length).toBeGreaterThan(0);
        
        // Should have file path (when provided)
        expect(error.filePath).toBe('content/test/invalid-quiz/quiz.md');
        
        // Should have field name
        expect(error.field).toBeDefined();
        expect(typeof error.field).toBe('string');
      });
    });

    it('should collect and report multiple errors from the same entry', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'multi-error-quiz': {
            content_type: 'quiz',
            topic_slug: 'multi-error-quiz',
            module_id: 'test/multi-error-quiz',
            passing_score: 150, // Error 1
            question_count: 2,
            questions: [
              {
                id: 'q1',
                question_text: 'Q1?',
                options: ['A. Only one'], // Error 2
                correct_answer: 'A',
                explanation: 'E1'
              },
              {
                id: 'q2',
                question_text: 'Q2?',
                options: ['A. 1', 'B. 2'],
                correct_answer: 'Z', // Error 3
                explanation: 'E2'
              }
            ]
          }
        }
      };

      const result = validateRegistry(registry);
      
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(3);
      
      // Should have passing_score error
      expect(result.errors.some(e => e.type === 'INVALID_PASSING_SCORE_RANGE')).toBe(true);
      
      // Should have insufficient options error
      expect(result.errors.some(e => e.type === 'INSUFFICIENT_OPTIONS')).toBe(true);
      
      // Should have invalid correct answer error
      expect(result.errors.some(e => e.type === 'INVALID_CORRECT_ANSWER')).toBe(true);
    });
  });
});
