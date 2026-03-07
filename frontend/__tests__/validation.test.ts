/**
 * Unit tests for Content Registry Validation
 * Tests the validation rules for the content registry
 */

import { 
  validateRegistry,
  validateTopicSlugUniqueness,
  validatePassingScore,
  validateQuestionStructure,
  validateModuleId,
  validateRequiredFields
} from '../scripts/generate-content-registry';
import type { ContentRegistry, QuizEntry, ModuleEntry, CapstoneEntry, WalkthroughEntry } from '../scripts/generate-content-registry';

describe('Content Registry Validation', () => {
  describe('validateTopicSlugUniqueness', () => {
    it('should pass when all topic slugs are unique', () => {
      const entries: Record<string, QuizEntry> = {
        'quiz1': {
          content_type: 'quiz',
          topic_slug: 'topic1',
          module_id: 'path/topic1',
          passing_score: 80,
          question_count: 1,
          questions: []
        },
        'quiz2': {
          content_type: 'quiz',
          topic_slug: 'topic2',
          module_id: 'path/topic2',
          passing_score: 70,
          question_count: 1,
          questions: []
        }
      };

      const errors = validateTopicSlugUniqueness(entries);
      expect(errors).toHaveLength(0);
    });

    it('should detect duplicate topic slugs', () => {
      const entries: Record<string, QuizEntry> = {
        'quiz1': {
          content_type: 'quiz',
          topic_slug: 'duplicate',
          module_id: 'path1/duplicate',
          passing_score: 80,
          question_count: 1,
          questions: []
        },
        'quiz2': {
          content_type: 'quiz',
          topic_slug: 'duplicate',
          module_id: 'path2/duplicate',
          passing_score: 70,
          question_count: 1,
          questions: []
        }
      };

      const errors = validateTopicSlugUniqueness(entries);
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('DUPLICATE_TOPIC_SLUG');
      expect(errors[0].message).toContain('duplicate');
      expect(errors[0].message).toContain('quiz1');
      expect(errors[0].message).toContain('quiz2');
    });
  });

  describe('validatePassingScore', () => {
    it('should pass for valid passing score (0-100)', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should pass for passing score of 0', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 0,
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should pass for passing score of 100', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 100,
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should fail for passing score below 0', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: -10,
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('INVALID_PASSING_SCORE_RANGE');
      expect(errors[0].message).toContain('0 and 100');
      expect(errors[0].message).toContain('-10');
    });

    it('should fail for passing score above 100', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 150,
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('INVALID_PASSING_SCORE_RANGE');
      expect(errors[0].message).toContain('0 and 100');
      expect(errors[0].message).toContain('150');
    });

    it('should fail for non-number passing score', () => {
      const quiz: any = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 'eighty',
        question_count: 1,
        questions: []
      };

      const errors = validatePassingScore(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('INVALID_PASSING_SCORE_TYPE');
    });
  });

  describe('validateQuestionStructure', () => {
    it('should pass for valid question structure', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 2,
        questions: [
          {
            id: 'q1',
            question_text: 'Question 1?',
            options: ['A. Option 1', 'B. Option 2'],
            correct_answer: 'A',
            explanation: 'Explanation 1'
          },
          {
            id: 'q2',
            question_text: 'Question 2?',
            options: ['A. Option 1', 'B. Option 2', 'C. Option 3'],
            correct_answer: 'B',
            explanation: 'Explanation 2'
          }
        ]
      };

      const errors = validateQuestionStructure(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should fail for question with less than 2 options', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 1,
        questions: [
          {
            id: 'q1',
            question_text: 'Question?',
            options: ['A. Only one'],
            correct_answer: 'A',
            explanation: 'Explanation'
          }
        ]
      };

      const errors = validateQuestionStructure(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('INSUFFICIENT_OPTIONS');
      expect(errors[0].message).toContain('at least 2 options');
    });

    it('should fail for question with invalid correct answer', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 1,
        questions: [
          {
            id: 'q1',
            question_text: 'Question?',
            options: ['A. Option 1', 'B. Option 2'],
            correct_answer: 'Z', // Invalid!
            explanation: 'Explanation'
          }
        ]
      };

      const errors = validateQuestionStructure(quiz, 'test-quiz');
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.type === 'INVALID_CORRECT_ANSWER')).toBe(true);
      expect(errors.some(e => e.message.includes('not one of the available options'))).toBe(true);
    });

    it('should fail for question with missing correct answer', () => {
      const quiz: any = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 1,
        questions: [
          {
            id: 'q1',
            question_text: 'Question?',
            options: ['A. Option 1', 'B. Option 2'],
            correct_answer: null,
            explanation: 'Explanation'
          }
        ]
      };

      const errors = validateQuestionStructure(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('MISSING_CORRECT_ANSWER');
    });
  });

  describe('validateModuleId', () => {
    it('should pass for valid module_id format', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'learning-path/topic-slug',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateModuleId(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should pass for module_id with underscores', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'learning_path/topic_slug',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateModuleId(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should fail for module_id without slash', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'invalid',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateModuleId(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('INVALID_MODULE_ID_FORMAT');
      expect(errors[0].message).toContain('learning_path}/{topic_slug');
    });

    it('should fail for module_id with invalid characters', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'learning path/topic slug',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateModuleId(quiz, 'test-quiz');
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.type === 'INVALID_LEARNING_PATH_FORMAT' || e.type === 'INVALID_TOPIC_SLUG_FORMAT')).toBe(true);
    });

    it('should fail for missing module_id', () => {
      const quiz: any = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: null,
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateModuleId(quiz, 'test-quiz');
      expect(errors).toHaveLength(1);
      expect(errors[0].type).toBe('MISSING_MODULE_ID');
    });
  });

  describe('validateRequiredFields', () => {
    it('should pass for valid quiz entry', () => {
      const quiz: QuizEntry = {
        content_type: 'quiz',
        topic_slug: 'test',
        module_id: 'test/test',
        passing_score: 80,
        question_count: 1,
        questions: []
      };

      const errors = validateRequiredFields(quiz, 'test-quiz');
      expect(errors).toHaveLength(0);
    });

    it('should pass for valid module entry', () => {
      const module: ModuleEntry = {
        content_type: 'module',
        topic_slug: 'test',
        module_id: 'test/test',
        module_number: 1,
        title: 'Test Module',
        reading_time: 5,
        has_quiz: false
      };

      const errors = validateRequiredFields(module, 'test-module');
      expect(errors).toHaveLength(0);
    });

    it('should pass for valid capstone entry', () => {
      const capstone: CapstoneEntry = {
        content_type: 'capstone',
        topic_slug: 'capstone',
        module_id: 'test/capstone',
        title: 'Test Capstone',
        description: 'Test description',
        submission_requirements: ['Requirement 1'],
        evaluation_criteria: ['Criterion 1']
      };

      const errors = validateRequiredFields(capstone, 'test-capstone');
      expect(errors).toHaveLength(0);
    });

    it('should pass for valid walkthrough entry', () => {
      const walkthrough: WalkthroughEntry = {
        content_type: 'walkthrough',
        id: 'test-walkthrough',
        title: 'Test Walkthrough',
        description: 'Test description',
        difficulty: 'Intermediate',
        topics: ['topic1', 'topic2'],
        estimated_time: 60,
        prerequisites: [],
        repository: 'frontend/content/walkthroughs/test'
      };

      const errors = validateRequiredFields(walkthrough, 'test-walkthrough');
      expect(errors).toHaveLength(0);
    });

    it('should fail for quiz missing required fields', () => {
      const quiz: any = {
        content_type: 'quiz',
        topic_slug: 'test'
        // Missing module_id, passing_score, questions, question_count
      };

      const errors = validateRequiredFields(quiz, 'test-quiz');
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.type === 'MISSING_MODULE_ID')).toBe(true);
      expect(errors.some(e => e.type === 'MISSING_PASSING_SCORE')).toBe(true);
      expect(errors.some(e => e.type === 'MISSING_QUESTIONS')).toBe(true);
    });

    it('should fail for module missing required fields', () => {
      const module: any = {
        content_type: 'module',
        topic_slug: 'test'
        // Missing module_id, module_number, title, reading_time, has_quiz
      };

      const errors = validateRequiredFields(module, 'test-module');
      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.type === 'MISSING_MODULE_ID')).toBe(true);
      expect(errors.some(e => e.type === 'MISSING_TITLE')).toBe(true);
    });
  });

  describe('validateRegistry', () => {
    it('should pass for valid registry', () => {
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
            question_count: 2,
            questions: [
              {
                id: 'q1',
                question_text: 'Question 1?',
                options: ['A. Option 1', 'B. Option 2'],
                correct_answer: 'A',
                explanation: 'Explanation 1'
              },
              {
                id: 'q2',
                question_text: 'Question 2?',
                options: ['A. Option 1', 'B. Option 2', 'C. Option 3'],
                correct_answer: 'B',
                explanation: 'Explanation 2'
              }
            ]
          }
        }
      };

      const result = validateRegistry(registry);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should fail for registry with duplicate topic slugs', () => {
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
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some(e => e.type === 'DUPLICATE_TOPIC_SLUG')).toBe(true);
    });

    it('should fail for registry with invalid passing scores', () => {
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

      const result = validateRegistry(registry);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'INVALID_PASSING_SCORE_RANGE')).toBe(true);
    });

    it('should fail for registry with invalid question structure', () => {
      const registry: ContentRegistry = {
        schema_version: '1.0.0',
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {
          'invalid-quiz': {
            content_type: 'quiz',
            topic_slug: 'invalid-quiz',
            module_id: 'test/invalid-quiz',
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
      expect(result.errors.some(e => e.type === 'INSUFFICIENT_OPTIONS')).toBe(true);
    });

    it('should fail for registry missing schema_version', () => {
      const registry: any = {
        generated_at: new Date().toISOString(),
        generator_version: '1.0.0',
        entries: {}
      };

      const result = validateRegistry(registry);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'MISSING_SCHEMA_VERSION')).toBe(true);
    });
  });
});
