/**
 * Demonstration script for enhanced validation error reporting
 * Shows how validation errors include file paths, field names, and invalid values
 */

import { validateRegistry } from './generate-content-registry';
import type { ContentRegistry } from './generate-content-registry';

// Create a registry with multiple validation errors
const testRegistry: ContentRegistry = {
  schema_version: '1.0.0',
  generated_at: new Date().toISOString(),
  generator_version: '1.0.0',
  entries: {
    'invalid-quiz-1': {
      content_type: 'quiz',
      topic_slug: 'invalid-quiz-1',
      module_id: 'test/invalid-quiz-1',
      passing_score: 150, // ERROR: Out of range (0-100)
      question_count: 2,
      questions: [
        {
          id: 'q1',
          question_text: 'What is DevSecOps?',
          options: ['A. Only one option'], // ERROR: Need at least 2 options
          correct_answer: 'A',
          explanation: 'DevSecOps integrates security into DevOps.'
        },
        {
          id: 'q2',
          question_text: 'What is CI/CD?',
          options: ['A. Continuous Integration', 'B. Continuous Deployment', 'C. Both'],
          correct_answer: 'Z', // ERROR: Invalid option letter
          explanation: 'CI/CD stands for Continuous Integration and Continuous Deployment.'
        }
      ]
    },
    'invalid-quiz-2': {
      content_type: 'quiz',
      topic_slug: 'duplicate', // ERROR: Duplicate topic slug
      module_id: 'invalid', // ERROR: Invalid module_id format
      passing_score: 80,
      question_count: 1,
      questions: [
        {
          id: 'q1',
          question_text: 'Test question?',
          options: ['A. Option 1', 'B. Option 2'],
          correct_answer: 'A',
          explanation: 'Test explanation'
        }
      ]
    },
    'invalid-quiz-3': {
      content_type: 'quiz',
      topic_slug: 'duplicate', // ERROR: Duplicate topic slug
      module_id: 'test/duplicate',
      passing_score: -10, // ERROR: Negative passing score
      question_count: 1,
      questions: [
        {
          id: 'q1',
          question_text: 'Another test?',
          options: ['A. Yes', 'B. No'],
          correct_answer: 'A',
          explanation: 'Test'
        }
      ]
    }
  }
};

// Create file path mapping
const filePaths = new Map<string, string>();
filePaths.set('invalid-quiz-1', 'content/test/invalid-quiz-1/quiz.md');
filePaths.set('invalid-quiz-2', 'content/test/invalid-quiz-2/quiz.md');
filePaths.set('invalid-quiz-3', 'content/test/invalid-quiz-3/quiz.md');

console.log('='.repeat(80));
console.log('ENHANCED VALIDATION ERROR REPORTING DEMONSTRATION');
console.log('='.repeat(80));
console.log('\nValidating registry with intentional errors...\n');

// Validate the registry
const result = validateRegistry(testRegistry, filePaths);

console.log(`\nValidation Result: ${result.valid ? 'PASSED' : 'FAILED'}`);
console.log(`Total Errors: ${result.errors.length}`);
console.log(`Total Warnings: ${result.warnings.length}`);

if (!result.valid) {
  console.log('\n' + '='.repeat(80));
  console.log('DETAILED ERROR REPORT');
  console.log('='.repeat(80));
  
  result.errors.forEach((error, index) => {
    console.log(`\n[Error ${index + 1}] ${error.type}`);
    console.log('-'.repeat(80));
    
    if (error.filePath) {
      console.log(`📁 File: ${error.filePath}`);
    }
    
    if (error.field) {
      console.log(`🔍 Field: ${error.field}`);
    }
    
    if (error.value !== undefined) {
      console.log(`❌ Invalid Value: ${JSON.stringify(error.value)}`);
    }
    
    console.log(`💬 Message: ${error.message}`);
  });
  
  console.log('\n' + '='.repeat(80));
  console.log('SUMMARY OF ISSUES');
  console.log('='.repeat(80));
  
  // Group errors by type
  const errorsByType = result.errors.reduce((acc, error) => {
    if (!acc[error.type]) {
      acc[error.type] = [];
    }
    acc[error.type].push(error);
    return acc;
  }, {} as Record<string, typeof result.errors>);
  
  Object.entries(errorsByType).forEach(([type, errors]) => {
    console.log(`\n${type}: ${errors.length} occurrence(s)`);
    errors.forEach(error => {
      console.log(`  - ${error.filePath || 'Unknown file'}: ${error.field || 'N/A'}`);
    });
  });
}

console.log('\n' + '='.repeat(80));
console.log('KEY FEATURES DEMONSTRATED:');
console.log('='.repeat(80));
console.log('✓ File paths included in all validation errors');
console.log('✓ Specific field names for each error');
console.log('✓ Invalid values shown for debugging');
console.log('✓ Actionable error messages with context');
console.log('✓ Multiple errors collected and reported together');
console.log('='.repeat(80));
