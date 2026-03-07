#!/usr/bin/env node
/**
 * Content Registry Generator
 * 
 * This script generates a unified content registry from markdown files.
 * It parses quizzes, modules, capstones, and walkthroughs to create a
 * single JSON registry that serves as the source of truth for the backend.
 */

import { promises as fs } from 'fs';
import path from 'path';
import { glob } from 'glob';
import matter from 'gray-matter';
import { S3Client, PutObjectCommand, ListObjectsV2Command, DeleteObjectCommand } from '@aws-sdk/client-s3';

/**
 * Metadata about a discovered content file
 */
interface ContentFileMetadata {
  filePath: string;
  absolutePath: string;
  relativePath: string;
  contentType: 'quiz' | 'module' | 'capstone' | 'walkthrough';
  learningPath?: string;
  topic?: string;
}

/**
 * Quiz frontmatter metadata extracted from YAML
 */
interface QuizFrontmatter {
  module_id: string;
  passing_score: number;
  [key: string]: any; // Allow additional metadata fields
}

/**
 * Error thrown when frontmatter parsing fails
 */
class FrontmatterParsingError extends Error {
  filePath: string;
  details?: string;
  
  constructor(
    message: string,
    filePath: string,
    details?: string
  ) {
    super(message);
    this.name = 'FrontmatterParsingError';
    this.filePath = filePath;
    this.details = details;
  }
}

/**
 * Discover all quiz.md files in the frontend/content directory
 * 
 * @param basePath - Base path to search from (default: content)
 * @returns Array of file paths with metadata
 */
async function discoverQuizFiles(basePath: string = 'content'): Promise<ContentFileMetadata[]> {
  const pattern = path.join(basePath, '**/quiz.md');
  
  try {
    // Use glob to find all quiz.md files
    const files = await glob(pattern, {
      ignore: ['**/node_modules/**', '**/dist/**', '**/.next/**'],
      absolute: false
    });
    
    // Map files to metadata objects
    const metadata: ContentFileMetadata[] = files.map((filePath: string) => {
      const absolutePath = path.resolve(filePath);
      const relativePath = path.relative(process.cwd(), absolutePath);
      
      // Extract learning path and topic from file path
      // Pattern: content/{learning_path}/{topic}/quiz.md
      const pathParts = filePath.split(path.sep);
      const contentIndex = pathParts.indexOf('content');
      
      let learningPath: string | undefined;
      let topic: string | undefined;
      
      if (contentIndex >= 0 && pathParts.length > contentIndex + 2) {
        learningPath = pathParts[contentIndex + 1];
        topic = pathParts[contentIndex + 2];
      }
      
      return {
        filePath,
        absolutePath,
        relativePath,
        contentType: 'quiz',
        learningPath,
        topic
      };
    });
    
    return metadata;
  } catch (error) {
    console.error(`Error discovering quiz files: ${error}`);
    throw error;
  }
}

/**
 * Discover all walkthrough README.md files in the frontend/content/walkthroughs directory
 *
 * @param basePath - Base path to search from (default: content/walkthroughs)
 * @returns Array of file paths with metadata including walkthrough ID
 */
async function discoverWalkthroughFiles(basePath: string = 'content/walkthroughs'): Promise<ContentFileMetadata[]> {
  const pattern = path.join(basePath, '*/README.md');

  try {
    // Use glob to find all README.md files in walkthrough subdirectories
    const files = await glob(pattern, {
      ignore: ['**/node_modules/**', '**/dist/**', '**/.next/**'],
      absolute: false
    });

    // Map files to metadata objects
    const metadata: ContentFileMetadata[] = files.map((filePath: string) => {
      const absolutePath = path.resolve(filePath);
      const relativePath = path.relative(process.cwd(), absolutePath);

      // Extract walkthrough ID from directory name
      // Pattern: content/walkthroughs/{walkthrough-id}/README.md
      const pathParts = filePath.split(path.sep);
      const walkthroughsIndex = pathParts.indexOf('walkthroughs');

      let walkthroughId: string | undefined;

      if (walkthroughsIndex >= 0 && pathParts.length > walkthroughsIndex + 1) {
        // Get the directory name between 'walkthroughs' and 'README.md'
        walkthroughId = pathParts[walkthroughsIndex + 1];
      }

      return {
        filePath,
        absolutePath,
        relativePath,
        contentType: 'walkthrough',
        topic: walkthroughId // Store walkthrough ID in topic field for consistency
      };
    });

    return metadata;
  } catch (error) {
    console.error(`Error discovering walkthrough files: ${error}`);
    throw error;
  }
}
/**
 * Discover all module_*.md files in the frontend/content directory
 *
 * @param basePath - Base path to search from (default: content)
 * @returns Array of file paths with metadata
 */
async function discoverModuleFiles(basePath: string = 'content'): Promise<ContentFileMetadata[]> {
  const pattern = path.join(basePath, '**/module_*.md');

  try {
    // Use glob to find all module_*.md files
    const files = await glob(pattern, {
      ignore: ['**/node_modules/**', '**/dist/**', '**/.next/**'],
      absolute: false
    });

    // Map files to metadata objects
    const metadata: ContentFileMetadata[] = files.map((filePath: string) => {
      const absolutePath = path.resolve(filePath);
      const relativePath = path.relative(process.cwd(), absolutePath);

      // Extract learning path and topic from file path
      // Pattern: content/{learning_path}/{topic}/module_N.md
      const pathParts = filePath.split(path.sep);
      const contentIndex = pathParts.indexOf('content');

      let learningPath: string | undefined;
      let topic: string | undefined;

      if (contentIndex >= 0 && pathParts.length > contentIndex + 2) {
        learningPath = pathParts[contentIndex + 1];
        topic = pathParts[contentIndex + 2];
      }

      return {
        filePath,
        absolutePath,
        relativePath,
        contentType: 'module',
        learningPath,
        topic
      };
    });

    return metadata;
  } catch (error) {
    console.error(`Error discovering module files: ${error}`);
    throw error;
  }
}
/**
 * Discover all capstone/index.md files in the frontend/content directory
 *
 * @param basePath - Base path to search from (default: content)
 * @returns Array of file paths with metadata
 */
async function discoverCapstoneFiles(basePath: string = 'content'): Promise<ContentFileMetadata[]> {
  const pattern = path.join(basePath, '**/capstone/index.md');

  try {
    // Use glob to find all capstone/index.md files
    const files = await glob(pattern, {
      ignore: ['**/node_modules/**', '**/dist/**', '**/.next/**'],
      absolute: false
    });

    // Map files to metadata objects
    const metadata: ContentFileMetadata[] = files.map((filePath: string) => {
      const absolutePath = path.resolve(filePath);
      const relativePath = path.relative(process.cwd(), absolutePath);

      // Extract learning path from file path
      // Pattern: content/{learning_path}/capstone/index.md
      const pathParts = filePath.split(path.sep);
      const contentIndex = pathParts.indexOf('content');

      let learningPath: string | undefined;

      if (contentIndex >= 0 && pathParts.length > contentIndex + 1) {
        learningPath = pathParts[contentIndex + 1];
      }

      return {
        filePath,
        absolutePath,
        relativePath,
        contentType: 'capstone',
        learningPath,
        topic: 'capstone' // Topic is always 'capstone' for capstone projects
      };
    });

    return metadata;
  } catch (error) {
    console.error(`Error discovering capstone files: ${error}`);
    throw error;
  }
}

/**
 * Parse frontmatter from a markdown file
 * 
 * @param filePath - Path to the markdown file
 * @returns Parsed frontmatter data and content
 * @throws FrontmatterParsingError if frontmatter is invalid or missing required fields
 */
async function parseFrontmatter(filePath: string): Promise<{ data: QuizFrontmatter; content: string }> {
  try {
    // Read the file content
    const fileContent = await fs.readFile(filePath, 'utf-8');
    
    // Parse with gray-matter
    const parsed = matter(fileContent);
    
    // Validate that frontmatter exists
    if (!parsed.data || Object.keys(parsed.data).length === 0) {
      throw new FrontmatterParsingError(
        'Missing or empty frontmatter',
        filePath,
        'Frontmatter block must be present at the top of the file between --- delimiters'
      );
    }
    
    // Validate required fields for quiz files
    const data = parsed.data as QuizFrontmatter;
    
    if (!data.module_id) {
      throw new FrontmatterParsingError(
        'Missing required field: module_id',
        filePath,
        'The frontmatter must include a module_id field'
      );
    }
    
    if (data.passing_score === undefined || data.passing_score === null) {
      throw new FrontmatterParsingError(
        'Missing required field: passing_score',
        filePath,
        'The frontmatter must include a passing_score field'
      );
    }
    
    // Validate passing_score is a number
    if (typeof data.passing_score !== 'number') {
      throw new FrontmatterParsingError(
        'Invalid passing_score type',
        filePath,
        `passing_score must be a number, got ${typeof data.passing_score}`
      );
    }
    
    // Validate passing_score range (0-100)
    if (data.passing_score < 0 || data.passing_score > 100) {
      throw new FrontmatterParsingError(
        'Invalid passing_score value',
        filePath,
        `passing_score must be between 0 and 100, got ${data.passing_score}`
      );
    }
    
    return {
      data,
      content: parsed.content
    };
    
  } catch (error) {
    // Re-throw FrontmatterParsingError as-is
    if (error instanceof FrontmatterParsingError) {
      throw error;
    }
    
    // Handle file reading errors
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new FrontmatterParsingError(
        'File not found',
        filePath,
        `Could not read file: ${filePath}`
      );
    }
    
    // Handle YAML parsing errors from gray-matter
    if (error instanceof Error && error.message.includes('can not read')) {
      throw new FrontmatterParsingError(
        'Invalid YAML in frontmatter',
        filePath,
        error.message
      );
    }
    
    // Handle other unexpected errors
    throw new FrontmatterParsingError(
      'Failed to parse frontmatter',
      filePath,
      error instanceof Error ? error.message : String(error)
    );
  }
}

/**
 * Extract module_id, passing_score, and other metadata from quiz frontmatter
 * 
 * @param filePath - Path to the quiz markdown file
 * @returns Extracted metadata
 * @throws FrontmatterParsingError with descriptive error message
 */
async function extractQuizMetadata(filePath: string): Promise<QuizFrontmatter> {
  const { data } = await parseFrontmatter(filePath);
  return data;
}

/**
 * Represents a parsed quiz question with all components
 */
interface QuizQuestion {
  id: string;
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

/**
 * Error thrown when question parsing fails
 */
class QuestionParsingError extends Error {
  filePath: string;
  questionNumber?: number;
  details?: string;
  
  constructor(
    message: string,
    filePath: string,
    questionNumber?: number,
    details?: string
  ) {
    super(message);
    this.name = 'QuestionParsingError';
    this.filePath = filePath;
    this.questionNumber = questionNumber;
    this.details = details;
  }
}

/**
 * Parse questions from quiz markdown content
 * 
 * Splits content by `---` separators and extracts:
 * - Question text from `## Question N` sections
 * - Options in A., B., C., D. format
 * - Correct answer from `**Correct Answer:**` section
 * - Explanation from `**Explanation:**` section
 * 
 * @param markdown - The markdown content (without frontmatter)
 * @param filePath - Path to the file (for error reporting)
 * @returns Array of parsed questions
 * @throws QuestionParsingError if questions are malformed
 */
function parseQuestions(markdown: string, filePath: string): QuizQuestion[] {
  const questions: QuizQuestion[] = [];
  
  // Split by --- separators (question boundaries)
  const sections = markdown.split(/^---$/m).map(s => s.trim()).filter(s => s.length > 0);
  
  if (sections.length === 0) {
    throw new QuestionParsingError(
      'No questions found in quiz',
      filePath,
      undefined,
      'Quiz must contain at least one question separated by --- markers'
    );
  }
  
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i];
    const questionNumber = i + 1;
    
    try {
      // Extract question number and text
      // Pattern: ## Question N followed by the question text
      const questionMatch = section.match(/^##\s+Question\s+(\d+)\s*\n\n([\s\S]+?)(?=\n[A-Z]\.|$)/);
      
      if (!questionMatch) {
        throw new QuestionParsingError(
          'Invalid question format',
          filePath,
          questionNumber,
          'Question must start with "## Question N" followed by question text and options'
        );
      }
      
      const questionText = questionMatch[2].trim();
      
      // Check if question text is empty after trimming
      if (!questionText || questionText.length === 0) {
        throw new QuestionParsingError(
          'Empty question text',
          filePath,
          questionNumber,
          'Question text cannot be empty'
        );
      }
      
      // Extract options (A., B., C., D. format)
      const options = extractOptions(section, filePath, questionNumber);
      
      if (options.length < 2) {
        throw new QuestionParsingError(
          'Insufficient options',
          filePath,
          questionNumber,
          `Question must have at least 2 options, found ${options.length}`
        );
      }
      
      // Extract correct answer
      const correctAnswer = extractCorrectAnswer(section, filePath, questionNumber);
      
      // Validate correct answer is one of the option letters
      const optionLetters = options.map(opt => opt.charAt(0));
      if (!optionLetters.includes(correctAnswer)) {
        throw new QuestionParsingError(
          'Invalid correct answer',
          filePath,
          questionNumber,
          `Correct answer "${correctAnswer}" is not one of the available options: ${optionLetters.join(', ')}`
        );
      }
      
      // Extract explanation
      const explanation = extractExplanation(section, filePath, questionNumber);
      
      // Create question object
      questions.push({
        id: `q${questionNumber}`,
        question_text: questionText,
        options,
        correct_answer: correctAnswer,
        explanation
      });
      
    } catch (error) {
      // Re-throw QuestionParsingError as-is
      if (error instanceof QuestionParsingError) {
        throw error;
      }
      
      // Wrap other errors
      throw new QuestionParsingError(
        'Failed to parse question',
        filePath,
        questionNumber,
        error instanceof Error ? error.message : String(error)
      );
    }
  }
  
  return questions;
}

/**
 * Extract options from a question section
 * 
 * @param section - The question section text
 * @param filePath - Path to the file (for error reporting)
 * @param questionNumber - Question number (for error reporting)
 * @returns Array of option strings (e.g., ["A. Option 1", "B. Option 2"])
 */
function extractOptions(section: string, filePath: string, questionNumber: number): string[] {
  const options: string[] = [];
  
  // Match lines that start with a letter followed by a period
  // Pattern: A. Option text
  const optionRegex = /^([A-Z])\.\s+(.+)$/gm;
  let match;
  
  while ((match = optionRegex.exec(section)) !== null) {
    const letter = match[1];
    const text = match[2].trim();
    
    if (!text || text.length === 0) {
      throw new QuestionParsingError(
        'Empty option text',
        filePath,
        questionNumber,
        `Option ${letter} has no text`
      );
    }
    
    options.push(`${letter}. ${text}`);
  }
  
  return options;
}

/**
 * Extract correct answer from a question section
 * 
 * @param section - The question section text
 * @param filePath - Path to the file (for error reporting)
 * @param questionNumber - Question number (for error reporting)
 * @returns The correct answer letter (e.g., "A", "B", "C", "D")
 */
function extractCorrectAnswer(section: string, filePath: string, questionNumber: number): string {
  // Pattern: **Correct Answer:** followed by the letter
  const answerMatch = section.match(/\*\*Correct Answer:\*\*\s+([A-Z])/);
  
  if (!answerMatch) {
    throw new QuestionParsingError(
      'Missing correct answer',
      filePath,
      questionNumber,
      'Question must include "**Correct Answer:**" followed by the answer letter'
    );
  }
  
  return answerMatch[1];
}

/**
 * Extract explanation from a question section
 * 
 * @param section - The question section text
 * @param filePath - Path to the file (for error reporting)
 * @param questionNumber - Question number (for error reporting)
 * @returns The explanation text
 */
function extractExplanation(section: string, filePath: string, questionNumber: number): string {
  // Pattern: **Explanation:** followed by the explanation text
  const explanationMatch = section.match(/\*\*Explanation:\*\*\s+([\s\S]+?)$/);
  
  if (!explanationMatch) {
    throw new QuestionParsingError(
      'Missing explanation',
      filePath,
      questionNumber,
      'Question must include "**Explanation:**" followed by explanation text'
    );
  }
  
  const explanation = explanationMatch[1].trim();
  
  if (!explanation || explanation.length === 0) {
    throw new QuestionParsingError(
      'Empty explanation',
      filePath,
      questionNumber,
      'Explanation text cannot be empty'
    );
  }
  
  return explanation;
}
/**
 * Extract Topic_Slug from Module_ID by taking the last path segment
 *
 * Validates that the extracted slug contains only alphanumeric characters,
 * hyphens, and underscores.
 *
 * @param moduleId - The Module_ID in format "{learning_path}/{topic_slug}"
 * @returns The extracted topic_slug
 * @throws Error if moduleId is invalid or topic_slug format is invalid
 *
 * @example
 * extractTopicSlug("devsecops/what_is_the_secure_sdlc") // Returns: "what_is_the_secure_sdlc"
 * extractTopicSlug("know_before_you_go/prerequisites") // Returns: "prerequisites"
 */
function extractTopicSlug(moduleId: string): string {
  // Validate input type
  if (typeof moduleId !== 'string') {
    throw new Error('Module_ID must be a non-empty string');
  }

  // Trim whitespace
  const trimmedModuleId = moduleId.trim();

  // Validate not empty after trimming
  if (trimmedModuleId.length === 0) {
    throw new Error('Module_ID cannot be empty or whitespace');
  }

  // Extract last path segment
  const segments = trimmedModuleId.split('/');
  const topicSlug = segments[segments.length - 1];

  // Validate topic_slug is not empty
  if (!topicSlug || topicSlug.length === 0) {
    throw new Error(`Invalid Module_ID format: "${moduleId}" - cannot end with /`);
  }

  // Validate format: alphanumeric + hyphens/underscores only
  // Pattern: ^[a-zA-Z0-9_-]+$
  const validFormatRegex = /^[a-zA-Z0-9_-]+$/;

  if (!validFormatRegex.test(topicSlug)) {
    throw new Error(
      `Invalid topic_slug format: "${topicSlug}" - must contain only alphanumeric characters, hyphens, and underscores`
    );
  }

  return topicSlug;
}
/**
 * Capstone frontmatter metadata extracted from YAML
 */
interface CapstoneFrontmatter {
  id?: string;
  title: string;
  author?: string;
  description?: string;
  sidebar_position?: number;
  [key: string]: any; // Allow additional metadata fields
}

/**
 * Represents a parsed capstone entry
 */
interface CapstoneEntry {
  content_type: 'capstone';
  topic_slug: string;
  module_id: string;
  title: string;
  description: string;
  submission_requirements: string[];
  evaluation_criteria: string[];
}

/**
 * Parse capstone frontmatter from a markdown file
 *
 * @param filePath - Path to the capstone markdown file
 * @returns Parsed frontmatter data
 * @throws Error if frontmatter is invalid or missing required fields
 */
async function parseCapstoneFrontmatter(filePath: string): Promise<CapstoneFrontmatter> {
  try {
    // Read the file content
    const fileContent = await fs.readFile(filePath, 'utf-8');

    // Parse with gray-matter
    const parsed = matter(fileContent);

    // Validate that frontmatter exists
    if (!parsed.data || Object.keys(parsed.data).length === 0) {
      throw new Error(
        `Missing or empty frontmatter in ${filePath}: Frontmatter block must be present at the top of the file between --- delimiters`
      );
    }

    // Validate required fields for capstone files
    const data = parsed.data as CapstoneFrontmatter;

    if (!data.title) {
      throw new Error(
        `Missing required field: title in ${filePath}: The frontmatter must include a title field`
      );
    }

    if (!data.description) {
      throw new Error(
        `Missing required field: description in ${filePath}: The frontmatter must include a description field`
      );
    }

    return data;

  } catch (error) {
    // Handle file reading errors
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`File not found: ${filePath}`);
    }

    // Re-throw other errors
    throw error;
  }
}

/**
 * Extract submission requirements from the capstone markdown content
 * Looks for the "Submission" section and extracts numbered or bulleted list items
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns Array of submission requirement strings
 *
 * @example
 * extractSubmissionRequirements("### 📤 Submission...\n\n1. Publish the Blueprint\n2. Tell the Story")
 * // Returns: ["Publish the Blueprint", "Tell the Story"]
 */
function extractSubmissionRequirements(markdown: string, filePath: string): string[] {
  const requirements: string[] = [];

  // Match the Submission section (various heading formats)
  // Pattern: ### 📤 Submission or ## Submission Requirements, etc.
  const submissionMatch = markdown.match(/^#{2,3}\s+(?:📤\s+)?Submission[:\s].*?\n((?:(?!^#{2,3}\s)[\s\S])+)/m);

  if (!submissionMatch) {
    // Submission section is optional, return empty array
    return [];
  }

  const submissionSection = submissionMatch[1];

  // Extract numbered list items (1. Item, 2. Item, etc.)
  const numberedPattern = /^\d+\.\s+\*\*([^*]+)\*\*:?\s*(.*?)(?=\n\d+\.|\n\n|$)/gm;
  let match;

  while ((match = numberedPattern.exec(submissionSection)) !== null) {
    const title = match[1].trim();
    const description = match[2].trim();
    // Combine title and description if both exist
    const requirement = description ? `${title}: ${description}` : title;
    requirements.push(requirement);
  }

  // If no numbered items found, try bullet points
  if (requirements.length === 0) {
    const bulletPattern = /^[-*]\s+\*\*([^*]+)\*\*:?\s*(.*?)(?=\n[-*]|\n\n|$)/gm;

    while ((match = bulletPattern.exec(submissionSection)) !== null) {
      const title = match[1].trim();
      const description = match[2].trim();
      const requirement = description ? `${title}: ${description}` : title;
      requirements.push(requirement);
    }
  }

  // If still no items found, try simple numbered or bulleted lists
  if (requirements.length === 0) {
    const simplePattern = /^(?:\d+\.|-|\*)\s+([^\n]+)/gm;

    while ((match = simplePattern.exec(submissionSection)) !== null) {
      const requirement = match[1].trim();
      // Filter out empty lines and very short items
      if (requirement && requirement.length > 5) {
        requirements.push(requirement);
      }
    }
  }

  return requirements;
}

/**
 * Extract evaluation criteria from the capstone markdown content
 * Looks for the "Deliverables" or "Evaluation" section and extracts table rows or list items
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns Array of evaluation criteria strings
 *
 * @example
 * extractEvaluationCriteria("### The Final Deliverables\n\n| Deliverable | Value |\n| Pipeline | Proves automation |")
 * // Returns: ["Pipeline: Proves automation"]
 */
function extractEvaluationCriteria(markdown: string, filePath: string): string[] {
  const criteria: string[] = [];

  // Match the Deliverables or Evaluation section
  // Pattern: ### The Final Deliverables or ## Evaluation Criteria, etc.
  const criteriaMatch = markdown.match(/^#{2,3}\s+(?:The\s+)?(?:Final\s+)?(?:Deliverables?|Evaluation\s+Criteria)[:\s].*?\n((?:(?!^#{2,3}\s)[\s\S])+)/m);

  if (!criteriaMatch) {
    // Evaluation section is optional, return empty array
    return [];
  }

  const criteriaSection = criteriaMatch[1];

  // Try to extract from markdown table
  // Pattern: | Deliverable | Description |
  const tableRowPattern = /^\|\s*\*\*([^*|]+)\*\*\s*\|\s*([^|]+)\s*\|/gm;
  let match;

  while ((match = tableRowPattern.exec(criteriaSection)) !== null) {
    const deliverable = match[1].trim();
    const description = match[2].trim();

    // Skip header rows
    if (deliverable.toLowerCase() === 'deliverable' || description.includes('---')) {
      continue;
    }

    // Combine deliverable and description
    const criterion = `${deliverable}: ${description}`;
    criteria.push(criterion);
  }

  // If no table found, try numbered or bulleted lists
  if (criteria.length === 0) {
    const listPattern = /^(?:\d+\.|-|\*)\s+\*\*([^*]+)\*\*:?\s*(.*?)(?=\n(?:\d+\.|-|\*)|\n\n|$)/gm;

    while ((match = listPattern.exec(criteriaSection)) !== null) {
      const title = match[1].trim();
      const description = match[2].trim();
      const criterion = description ? `${title}: ${description}` : title;
      criteria.push(criterion);
    }
  }

  // If still no items found, try simple lists
  if (criteria.length === 0) {
    const simplePattern = /^(?:\d+\.|-|\*)\s+([^\n]+)/gm;

    while ((match = simplePattern.exec(criteriaSection)) !== null) {
      const criterion = match[1].trim();
      // Filter out empty lines and very short items
      if (criterion && criterion.length > 5) {
        criteria.push(criterion);
      }
    }
  }

  return criteria;
}

/**
 * Parse a capstone markdown file and extract metadata
 *
 * @param filePath - Path to the capstone markdown file (capstone/index.md)
 * @returns Parsed capstone entry
 * @throws Error if parsing fails
 */
async function parseCapstoneFile(filePath: string): Promise<CapstoneEntry> {
  try {
    // Parse frontmatter
    const frontmatter = await parseCapstoneFrontmatter(filePath);

    // Read full content for parsing submission requirements and evaluation criteria
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const { content: markdown } = matter(fileContent);

    // Extract submission requirements
    const submissionRequirements = extractSubmissionRequirements(markdown, filePath);

    // Extract evaluation criteria
    const evaluationCriteria = extractEvaluationCriteria(markdown, filePath);

    // Extract learning path from file path
    // Pattern: content/{learning_path}/capstone/index.md
    const pathParts = filePath.split(path.sep);
    const contentIndex = pathParts.indexOf('content');

    if (contentIndex < 0 || pathParts.length <= contentIndex + 1) {
      throw new Error(
        `Invalid capstone file path: "${filePath}" - expected pattern: content/{learning_path}/capstone/index.md`
      );
    }

    const learningPath = pathParts[contentIndex + 1];

    // Construct module_id
    const moduleId = `${learningPath}/capstone`;

    // Topic slug is always "capstone" for capstone projects
    const topicSlug = 'capstone';

    return {
      content_type: 'capstone',
      topic_slug: topicSlug,
      module_id: moduleId,
      title: frontmatter.title,
      description: frontmatter.description || '',
      submission_requirements: submissionRequirements,
      evaluation_criteria: evaluationCriteria
    };

  } catch (error) {
    throw new Error(
      `Failed to parse capstone file ${filePath}: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
/**
 * Calculate reading time estimate based on word count
 * Uses average reading speed of 200 words per minute
 *
 * @param markdown - The markdown content
 * @returns Estimated reading time in minutes (minimum 1)
 *
 * @example
 * calculateReadingTime("This is a short text.") // Returns: 1
 * calculateReadingTime("...500 words...") // Returns: 3
 */
function calculateReadingTime(markdown: string): number {
  // Remove frontmatter if present
  const contentWithoutFrontmatter = markdown.replace(/^---\n[\s\S]*?\n---\n/, '');

  // Remove markdown syntax for more accurate word count
  const plainText = contentWithoutFrontmatter
    .replace(/```[\s\S]*?```/g, '') // Remove code blocks
    .replace(/`[^`]+`/g, '') // Remove inline code
    .replace(/!\[.*?\]\(.*?\)/g, '') // Remove images
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Replace links with text
    .replace(/[#*_~`]/g, '') // Remove markdown formatting
    .replace(/\n+/g, ' '); // Replace newlines with spaces

  // Count words (split by whitespace and filter empty strings)
  const words = plainText.split(/\s+/).filter(word => word.length > 0);
  const wordCount = words.length;

  // Calculate reading time (200 words per minute)
  const minutes = Math.ceil(wordCount / 200);

  // Minimum 1 minute
  return Math.max(1, minutes);
}

/**
 * Module frontmatter metadata extracted from YAML
 */
interface ModuleFrontmatter {
  id?: string;
  title: string;
  author?: string;
  description?: string;
  sidebar_position?: number;
  [key: string]: any; // Allow additional metadata fields
}

/**
 * Represents a parsed module entry
 */
interface ModuleEntry {
  content_type: 'module';
  topic_slug: string;
  module_id: string;
  module_number: number;
  title: string;
  reading_time: number;
  has_quiz: boolean;
}

/**
 * Parse module frontmatter from a markdown file
 *
 * @param filePath - Path to the module markdown file
 * @returns Parsed frontmatter data
 * @throws Error if frontmatter is invalid or missing required fields
 */
async function parseModuleFrontmatter(filePath: string): Promise<ModuleFrontmatter> {
  try {
    // Read the file content
    const fileContent = await fs.readFile(filePath, 'utf-8');

    // Parse with gray-matter
    const parsed = matter(fileContent);

    // Validate that frontmatter exists
    if (!parsed.data || Object.keys(parsed.data).length === 0) {
      throw new Error(
        `Missing or empty frontmatter in ${filePath}: Frontmatter block must be present at the top of the file between --- delimiters`
      );
    }

    // Validate required fields for module files
    const data = parsed.data as ModuleFrontmatter;

    if (!data.title) {
      throw new Error(
        `Missing required field: title in ${filePath}: The frontmatter must include a title field`
      );
    }

    return data;

  } catch (error) {
    // Handle file reading errors
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`File not found: ${filePath}`);
    }

    // Re-throw other errors
    throw error;
  }
}

/**
 * Extract module number from filename
 *
 * @param filePath - Path to the module file (e.g., "module_1.md", "module_10.md")
 * @returns The module number
 * @throws Error if filename doesn't match expected pattern
 *
 * @example
 * extractModuleNumber("content/path/module_1.md") // Returns: 1
 * extractModuleNumber("content/path/module_10.md") // Returns: 10
 */
function extractModuleNumber(filePath: string): number {
  // Extract filename from path
  const filename = path.basename(filePath);

  // Match pattern: module_N.md where N is one or more digits
  const match = filename.match(/^module_(\d+)\.md$/);

  if (!match) {
    throw new Error(
      `Invalid module filename format: "${filename}" - expected format: module_N.md`
    );
  }

  const moduleNumber = parseInt(match[1], 10);

  if (isNaN(moduleNumber) || moduleNumber <= 0) {
    throw new Error(
      `Invalid module number in filename: "${filename}" - module number must be a positive integer`
    );
  }

  return moduleNumber;
}

/**
 * Check if quiz.md exists in the same directory as the module file
 *
 * @param modulePath - Path to the module file
 * @returns True if quiz.md exists, false otherwise
 */
async function hasQuiz(modulePath: string): Promise<boolean> {
  try {
    const directory = path.dirname(modulePath);
    const quizPath = path.join(directory, 'quiz.md');

    // Check if file exists
    await fs.access(quizPath);
    return true;
  } catch {
    // File doesn't exist or is not accessible
    return false;
  }
}

/**
 * Parse a module markdown file and extract metadata
 *
 * @param filePath - Path to the module markdown file
 * @returns Parsed module entry
 * @throws Error if parsing fails
 */
async function parseModuleFile(filePath: string): Promise<ModuleEntry> {
  try {
    // Extract module number from filename
    const moduleNumber = extractModuleNumber(filePath);

    // Parse frontmatter
    const frontmatter = await parseModuleFrontmatter(filePath);

    // Read full content for reading time calculation
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const { content: markdown } = matter(fileContent);

    // Calculate reading time
    const readingTime = calculateReadingTime(markdown);

    // Check if quiz exists
    const quizExists = await hasQuiz(filePath);

    // Extract learning path and topic from file path
    // Pattern: content/{learning_path}/{topic}/module_N.md
    const pathParts = filePath.split(path.sep);
    const contentIndex = pathParts.indexOf('content');

    if (contentIndex < 0 || pathParts.length <= contentIndex + 2) {
      throw new Error(
        `Invalid module file path: "${filePath}" - expected pattern: content/{learning_path}/{topic}/module_N.md`
      );
    }

    const learningPath = pathParts[contentIndex + 1];
    const topic = pathParts[contentIndex + 2];

    // Construct module_id
    const moduleId = `${learningPath}/${topic}`;

    // Extract topic_slug (same as topic in this case)
    const topicSlug = topic;

    return {
      content_type: 'module',
      topic_slug: topicSlug,
      module_id: moduleId,
      module_number: moduleNumber,
      title: frontmatter.title,
      reading_time: readingTime,
      has_quiz: quizExists
    };

  } catch (error) {
    throw new Error(
      `Failed to parse module file ${filePath}: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
/**
 * Extract title from the first # heading in markdown content
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns The extracted title text
 * @throws Error if no title heading is found
 *
 * @example
 * extractTitle("# My Title\n\nContent...") // Returns: "My Title"
 */
function extractTitle(markdown: string, filePath: string): string {
  // Match the first level-1 heading (# Title)
  // Pattern: ^# followed by spaces/tabs and content on the same line
  // Use [ \t]+ instead of \s+ to avoid matching newlines
  const titleMatch = markdown.match(/^#[ \t]+([^\n\r]*)$/m);

  if (!titleMatch) {
    throw new Error(
      `Failed to extract title from ${filePath}: No level-1 heading (# Title) found`
    );
  }

  const title = titleMatch[1].trim();

  if (!title || title.length === 0) {
    throw new Error(
      `Failed to extract title from ${filePath}: Title heading is empty`
    );
  }

  return title;
}

/**
 * Extract description from the ## Introduction section in markdown content
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns The extracted description text
 * @throws Error if no Introduction section is found
 *
 * @example
 * extractDescription("## Introduction\n\nThis is the description.\n\n## Next Section")
 * // Returns: "This is the description."
 */
function extractDescription(markdown: string, filePath: string): string {
  // Match the ## Introduction section and capture all content until the next ## heading (same level)
  // Allow ### sub-headings within the Introduction section
  // Use negative lookahead to match everything that is NOT the start of a new ## heading
  const IntroductionMatch = markdown.match(/^##\s+Introduction\s*\n((?:(?!^##\s)[\s\S])+)/m);

  if (!IntroductionMatch) {
    throw new Error(
      `Failed to extract description from ${filePath}: No ## Introduction section found`
    );
  }

  const description = IntroductionMatch[1].trim();

  if (!description || description.length === 0) {
    throw new Error(
      `Failed to extract description from ${filePath}: Introduction section is empty`
    );
  }

  return description;
}

/**
 * Extract estimated time from markdown content
 * Parses the "Estimated Time" section and converts to minutes
 * If no explicit time is found, calculates based on content length
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns The estimated time in minutes
 *
 * @example
 * extractEstimatedTime("### Estimated Time\n\n120 minutes (2 hours)")
 * // Returns: 120
 */
function extractEstimatedTime(markdown: string, filePath: string): number {
  // Match the "Estimated Time" section in various formats:
  // - ### Estimated Time\n\n120 minutes
  // - **Estimated time:** 30 minutes
  // Handle extra whitespace around the number
  const timeMatch = markdown.match(/(?:###?\s*Estimated Time\s*\n+\s*|\*\*Estimated time:\*\*\s*)(\d+)\s*minutes?/i);

  if (timeMatch) {
    const minutes = parseInt(timeMatch[1], 10);

    if (!isNaN(minutes) && minutes > 0) {
      return minutes;
    }
  }

  // If no explicit time found, calculate from content length
  // Use the calculateReadingTime function which is already defined
  return calculateReadingTime(markdown);
}

/**
 * Extract prerequisites from the ## Prerequisites section
 * Parses markdown links and returns an array of prerequisite walkthrough IDs
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns Array of prerequisite walkthrough IDs (can be empty)
 *
 * @example
 * extractPrerequisites("## Prerequisites\n\n- [Container Security](../container-security/README.md)")
 * // Returns: ["container-security"]
 */
function extractPrerequisites(markdown: string, filePath: string): string[] {
  // Match the ## Prerequisites section
  const prereqMatch = markdown.match(/^##\s+Prerequisites\s*\n((?:(?!^##\s)[\s\S])+)/m);

  if (!prereqMatch) {
    // Prerequisites section is optional, return empty array
    return [];
  }

  const prereqSection = prereqMatch[1];
  const prerequisites: string[] = [];

  // Extract markdown links that point to other walkthroughs
  // Pattern: [text](../walkthrough-id/README.md) or [text](../walkthrough-id)
  const linkPattern = /\[([^\]]+)\]\(\.\.\/([^/)]+)(?:\/README\.md)?\)/g;
  let match;

  while ((match = linkPattern.exec(prereqSection)) !== null) {
    const walkthroughId = match[2];
    if (walkthroughId && !prerequisites.includes(walkthroughId)) {
      prerequisites.push(walkthroughId);
    }
  }

  return prerequisites;
}

/**
 * Infer difficulty level from markdown content
 * Looks for explicit difficulty mentions or defaults to "Intermediate"
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns Difficulty level: "Beginner", "Intermediate", or "Advanced"
 *
 * @example
 * inferDifficulty("This is an advanced walkthrough...")
 * // Returns: "Advanced"
 */
function inferDifficulty(markdown: string, filePath: string): string {
  // Look for explicit difficulty mentions in the content
  // Check in Introduction section and first few paragraphs
  const lowerContent = markdown.toLowerCase();

  // Check for explicit difficulty statements
  if (lowerContent.includes('beginner-level') || 
      lowerContent.includes('beginner level') ||
      lowerContent.match(/\bthis\s+(?:is\s+)?(?:a\s+)?beginner\b/)) {
    return 'Beginner';
  }

  if (lowerContent.includes('advanced-level') || 
      lowerContent.includes('advanced level') ||
      lowerContent.match(/\bthis\s+(?:is\s+)?(?:an\s+)?advanced\b/)) {
    return 'Advanced';
  }

  if (lowerContent.includes('intermediate-level') || 
      lowerContent.includes('intermediate level') ||
      lowerContent.match(/\bthis\s+(?:is\s+)?(?:an\s+)?intermediate\b/)) {
    return 'Intermediate';
  }

  // Default to Intermediate if no explicit mention
  return 'Intermediate';
}

/**
 * Extract topics from markdown content
 * Analyzes the content to identify key topics/tags
 *
 * @param markdown - The markdown content
 * @param filePath - Path to the file (for error reporting)
 * @returns Array of topic strings
 *
 * @example
 * extractTopics("# Kubernetes Security\n\n## Introduction\n\nLearn about RBAC and network policies...")
 * // Returns: ["kubernetes", "security", "rbac", "network-policies"]
 */
function extractTopics(markdown: string, filePath: string): string[] {
  const topics: string[] = [];

  // Extract from title (first # heading)
  const titleMatch = markdown.match(/^#\s+([^\n]+)/m);
  if (titleMatch) {
    const titleWords = titleMatch[1]
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3); // Filter out short words
    topics.push(...titleWords);
  }

  // Look for common security/tech keywords in the content
  const keywords = [
    'kubernetes', 'docker', 'container', 'security', 'rbac', 'iam',
    'network', 'policies', 'authentication', 'authorization', 'encryption',
    'tls', 'ssl', 'firewall', 'vpc', 'aws', 'azure', 'gcp', 'cloud',
    'devsecops', 'cicd', 'pipeline', 'monitoring', 'logging', 'audit',
    'compliance', 'threat', 'vulnerability', 'scanning', 'hardening',
    'zero-trust', 'secrets', 'vault', 'kms', 'api', 'gateway', 'proxy',
    'service-mesh', 'istio', 'linkerd', 'helm', 'terraform', 'ansible'
  ];

  const lowerContent = markdown.toLowerCase();
  for (const keyword of keywords) {
    // Check if keyword appears multiple times or in headings
    const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
    const matches = lowerContent.match(regex);
    if (matches && matches.length >= 2 && !topics.includes(keyword)) {
      topics.push(keyword);
    }
  }

  // Remove duplicates and limit to reasonable number
  const uniqueTopics = Array.from(new Set(topics)).slice(0, 10);

  // Ensure we have at least one topic
  if (uniqueTopics.length === 0) {
    // Extract from filename as fallback
    const pathParts = filePath.split('/');
    const dirIndex = pathParts.findIndex(part => part === 'walkthroughs');
    if (dirIndex >= 0 && dirIndex < pathParts.length - 1) {
      const walkthroughId = pathParts[dirIndex + 1];
      if (walkthroughId) {
        uniqueTopics.push(walkthroughId);
      }
    }
  }

  return uniqueTopics;
}

/**
 * Represents a parsed walkthrough entry
 */
interface WalkthroughEntry {
  content_type: 'walkthrough';
  id: string;
  title: string;
  description: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  topics: string[];
  estimated_time: number;
  prerequisites: string[];
  repository: string;
}

/**
 * Parse a walkthrough README.md file and extract metadata
 *
 * @param filePath - Path to the walkthrough README.md file
 * @returns Parsed walkthrough entry
 * @throws Error if parsing fails
 */
async function parseWalkthroughFile(filePath: string): Promise<WalkthroughEntry> {
  try {
    // Read file content
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const { content: markdown } = matter(fileContent);

    // Extract walkthrough ID from directory name
    // Pattern: content/walkthroughs/{walkthrough-id}/README.md
    const pathParts = filePath.split(path.sep);
    const walkthroughsIndex = pathParts.indexOf('walkthroughs');

    if (walkthroughsIndex < 0 || pathParts.length <= walkthroughsIndex + 1) {
      throw new Error(
        `Invalid walkthrough file path: "${filePath}" - expected pattern: content/walkthroughs/{walkthrough-id}/README.md`
      );
    }

    const walkthroughId = pathParts[walkthroughsIndex + 1];

    // Try to read metadata.json from the walkthrough directory
    const walkthroughDir = path.dirname(filePath);
    const metadataPath = path.join(walkthroughDir, 'metadata.json');
    let metadata: any = {};
    
    try {
      const metadataContent = await fs.readFile(metadataPath, 'utf-8');
      metadata = JSON.parse(metadataContent);
    } catch (error) {
      // metadata.json doesn't exist or is invalid, will use inferred values
    }

    // Extract title from metadata or first # heading
    const title = metadata.title || extractTitle(markdown, filePath);

    // Extract description from metadata or ## Introduction section
    const description = metadata.description || extractDescription(markdown, filePath);

    // Extract estimated time from metadata or markdown
    const estimatedTime = metadata.estimated_time || metadata.estimatedTime || extractEstimatedTime(markdown, filePath);

    // Extract prerequisites from metadata or markdown
    const prerequisites = metadata.prerequisites || extractPrerequisites(markdown, filePath);

    // Get difficulty from metadata first, then infer from markdown
    const difficulty = metadata.difficulty || inferDifficulty(markdown, filePath);

    // Extract topics from metadata or markdown
    const topics = metadata.topics || extractTopics(markdown, filePath);

    // Construct repository path (relative to project root)
    const repository = path.join('frontend', 'content', 'walkthroughs', walkthroughId);

    return {
      content_type: 'walkthrough',
      id: walkthroughId,
      title,
      description,
      difficulty: difficulty as 'Beginner' | 'Intermediate' | 'Advanced',
      topics,
      estimated_time: estimatedTime,
      prerequisites,
      repository
    };

  } catch (error) {
    throw new Error(
      `Failed to parse walkthrough file ${filePath}: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Represents a parsed quiz entry
 */
interface QuizEntry {
  content_type: 'quiz';
  topic_slug: string;
  module_id: string;
  passing_score: number;
  question_count: number;
  questions: QuizQuestion[];
}

/**
 * Parse a quiz markdown file and extract metadata and questions
 *
 * @param filePath - Path to the quiz markdown file
 * @returns Parsed quiz entry
 * @throws Error if parsing fails
 */
async function parseQuizFile(filePath: string): Promise<QuizEntry> {
  try {
    // Parse frontmatter
    const { data: frontmatter, content: markdown } = await parseFrontmatter(filePath);

    // Parse questions
    const questions = parseQuestions(markdown, filePath);

    // Extract learning path and topic from file path if module_id doesn't include it
    // Pattern: content/{learning_path}/{topic}/quiz.md
    let moduleId = frontmatter.module_id;
    
    if (!moduleId.includes('/')) {
      // module_id doesn't include learning path, construct it from file path
      const pathParts = filePath.split(path.sep);
      const contentIndex = pathParts.indexOf('content');
      
      if (contentIndex >= 0 && pathParts.length > contentIndex + 2) {
        const learningPath = pathParts[contentIndex + 1];
        const topic = pathParts[contentIndex + 2];
        moduleId = `${learningPath}/${topic}`;
      }
    }

    // Extract topic_slug from module_id
    const topicSlug = extractTopicSlug(moduleId);

    return {
      content_type: 'quiz',
      topic_slug: topicSlug,
      module_id: moduleId,
      passing_score: frontmatter.passing_score,
      question_count: questions.length,
      questions
    };

  } catch (error) {
    throw new Error(
      `Failed to parse quiz file ${filePath}: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Content Registry structure
 */
interface ContentRegistry {
  schema_version: string;
  generated_at: string;
  generator_version: string;
  entries: Record<string, QuizEntry | ModuleEntry | CapstoneEntry | WalkthroughEntry>;
}

/**
 * Generate the complete content registry from all markdown files
 * 
 * This is the main orchestration function that:
 * 1. Discovers all content files (quizzes, modules, capstones, walkthroughs)
 * 2. Parses each file using the appropriate parser
 * 3. Collects all entries into a unified registry structure
 * 4. Adds metadata (schema_version, generated_at, generator_version)
 *
 * @param basePath - Base path to search for content files (default: 'content')
 * @returns Complete content registry with all entries
 * @throws Error if any parsing fails
 */
async function generateRegistry(basePath: string = 'content'): Promise<ContentRegistry> {
  console.log('Generating content registry...');
  
  const entries: Record<string, QuizEntry | ModuleEntry | CapstoneEntry | WalkthroughEntry> = {};
  const errors: string[] = [];
  // Map entry keys to file paths for validation error reporting
  const entryFilePaths: Map<string, string> = new Map();

  // Discover all content files
  console.log('\n1. Discovering content files...');
  const quizFiles = await discoverQuizFiles(basePath);
  const moduleFiles = await discoverModuleFiles(basePath);
  const capstoneFiles = await discoverCapstoneFiles(basePath);
  const walkthroughFiles = await discoverWalkthroughFiles(path.join(basePath, 'walkthroughs'));

  console.log(`   Found ${quizFiles.length} quiz files`);
  console.log(`   Found ${moduleFiles.length} module files`);
  console.log(`   Found ${capstoneFiles.length} capstone files`);
  console.log(`   Found ${walkthroughFiles.length} walkthrough files`);

  // Parse quiz files
  console.log('\n2. Parsing quiz files...');
  for (const file of quizFiles) {
    try {
      const entry = await parseQuizFile(file.filePath);
      entries[entry.topic_slug] = entry;
      entryFilePaths.set(entry.topic_slug, file.filePath);
      console.log(`   ✓ Parsed quiz: ${entry.topic_slug}`);
    } catch (error) {
      const errorMsg = `Failed to parse quiz ${file.filePath}: ${error instanceof Error ? error.message : String(error)}`;
      errors.push(errorMsg);
      console.error(`   ✗ ${errorMsg}`);
    }
  }

  // Parse module files
  console.log('\n3. Parsing module files...');
  for (const file of moduleFiles) {
    try {
      const entry = await parseModuleFile(file.filePath);
      // Use a composite key for modules: topic_slug + module_number
      const key = `${entry.topic_slug}_module_${entry.module_number}`;
      entries[key] = entry;
      entryFilePaths.set(key, file.filePath);
      console.log(`   ✓ Parsed module: ${key}`);
    } catch (error) {
      const errorMsg = `Failed to parse module ${file.filePath}: ${error instanceof Error ? error.message : String(error)}`;
      errors.push(errorMsg);
      console.error(`   ✗ ${errorMsg}`);
    }
  }

  // Parse capstone files
  console.log('\n4. Parsing capstone files...');
  for (const file of capstoneFiles) {
    try {
      const entry = await parseCapstoneFile(file.filePath);
      // Use module_id as key for capstones (e.g., "devsecops/capstone")
      entries[entry.module_id] = entry;
      entryFilePaths.set(entry.module_id, file.filePath);
      console.log(`   ✓ Parsed capstone: ${entry.module_id}`);
    } catch (error) {
      const errorMsg = `Failed to parse capstone ${file.filePath}: ${error instanceof Error ? error.message : String(error)}`;
      errors.push(errorMsg);
      console.error(`   ✗ ${errorMsg}`);
    }
  }

  // Parse walkthrough files
  console.log('\n5. Parsing walkthrough files...');
  for (const file of walkthroughFiles) {
    try {
      const entry = await parseWalkthroughFile(file.filePath);
      entries[entry.id] = entry;
      entryFilePaths.set(entry.id, file.filePath);
      console.log(`   ✓ Parsed walkthrough: ${entry.id}`);
    } catch (error) {
      const errorMsg = `Failed to parse walkthrough ${file.filePath}: ${error instanceof Error ? error.message : String(error)}`;
      errors.push(errorMsg);
      console.error(`   ✗ ${errorMsg}`);
    }
  }

  // Report errors if any
  if (errors.length > 0) {
    console.error(`\n❌ Registry generation completed with ${errors.length} error(s):`);
    errors.forEach(err => console.error(`   - ${err}`));
    throw new Error(`Registry generation failed with ${errors.length} error(s)`);
  }

  // Create registry with metadata
  const registry: ContentRegistry = {
    schema_version: '1.0.0',
    generated_at: new Date().toISOString(),
    generator_version: '1.0.0',
    entries
  };

  console.log(`\n✓ Registry generation complete!`);
  console.log(`   Total entries: ${Object.keys(entries).length}`);
  console.log(`   Schema version: ${registry.schema_version}`);
  console.log(`   Generated at: ${registry.generated_at}`);

  // Validate the registry with file path mapping
  const validationResult = validateRegistry(registry, entryFilePaths);
  
  if (!validationResult.valid) {
    console.error('\n❌ Registry validation failed:');
    validationResult.errors.forEach(error => {
      const fileInfo = error.filePath ? ` (${error.filePath})` : '';
      const fieldInfo = error.field ? ` - Field: ${error.field}` : '';
      const valueInfo = error.value !== undefined ? ` - Invalid value: ${JSON.stringify(error.value)}` : '';
      console.error(`   [${error.type}]${fileInfo}${fieldInfo}${valueInfo}`);
      console.error(`      ${error.message}`);
    });
    throw new Error(`Registry validation failed with ${validationResult.errors.length} error(s)`);
  }

  return registry;
}
/**
 * Validation error details
 */
interface ValidationError {
  type: string;
  message: string;
  filePath?: string;
  field?: string;
  value?: any;
}

/**
 * Validation result containing errors and warnings
 */
interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

/**
 * Validate Topic_Slug uniqueness across all entries
 * Note: Only quizzes, capstones, and walkthroughs need unique topic slugs.
 * Modules can share the same topic_slug as they use composite keys.
 *
 * @param entries - Registry entries to validate
 * @returns Array of validation errors (empty if valid)
 */
function validateTopicSlugUniqueness(
  entries: Record<string, QuizEntry | ModuleEntry | CapstoneEntry | WalkthroughEntry>
): ValidationError[] {
  const errors: ValidationError[] = [];
  const topicSlugMap = new Map<string, string[]>();

  // Build map of topic_slug to entry keys (only for quizzes, capstones, and walkthroughs)
  for (const [key, entry] of Object.entries(entries)) {
    // Skip modules - they can share topic_slugs
    if (entry.content_type === 'module') {
      continue;
    }

    let slug: string;

    if (entry.content_type === 'walkthrough') {
      slug = entry.id;
    } else {
      slug = entry.topic_slug;
    }

    if (!topicSlugMap.has(slug)) {
      topicSlugMap.set(slug, []);
    }
    topicSlugMap.get(slug)!.push(key);
  }

  // Check for duplicates (but allow capstones to have duplicate topic_slugs across learning paths)
  for (const [slug, keys] of topicSlugMap.entries()) {
    if (keys.length > 1) {
      // Check if all duplicates are capstones
      const allCapstones = keys.every(key => {
        const entry = entries[key];
        return entry && entry.content_type === 'capstone';
      });

      // Only report error if not all duplicates are capstones
      if (!allCapstones) {
        errors.push({
          type: 'DUPLICATE_TOPIC_SLUG',
          message: `Topic slug "${slug}" is used by multiple entries: ${keys.join(', ')}`,
          field: 'topic_slug',
          value: slug
        });
      }
    }
  }

  return errors;
}

/**
 * Validate passing_score range (0-100) for quiz entries
 *
 * @param entry - Quiz entry to validate
 * @param key - Entry key for error reporting
 * @returns Array of validation errors (empty if valid)
 */
function validatePassingScore(entry: QuizEntry, key: string): ValidationError[] {
  const errors: ValidationError[] = [];

  if (typeof entry.passing_score !== 'number') {
    errors.push({
      type: 'INVALID_PASSING_SCORE_TYPE',
      message: `Passing score must be a number for entry "${key}", got ${typeof entry.passing_score}`,
      field: 'passing_score',
      value: entry.passing_score
    });
    return errors;
  }

  if (entry.passing_score < 0 || entry.passing_score > 100) {
    errors.push({
      type: 'INVALID_PASSING_SCORE_RANGE',
      message: `Passing score must be between 0 and 100 for entry "${key}", got ${entry.passing_score}`,
      field: 'passing_score',
      value: entry.passing_score
    });
  }

  return errors;
}

/**
 * Validate question structure (at least 2 options, exactly 1 correct answer)
 *
 * @param entry - Quiz entry to validate
 * @param key - Entry key for error reporting
 * @returns Array of validation errors (empty if valid)
 */
function validateQuestionStructure(entry: QuizEntry, key: string): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!entry.questions || !Array.isArray(entry.questions)) {
    errors.push({
      type: 'INVALID_QUESTIONS_FIELD',
      message: `Questions field must be an array for entry "${key}"`,
      field: 'questions',
      value: entry.questions
    });
    return errors;
  }

  for (let i = 0; i < entry.questions.length; i++) {
    const question = entry.questions[i];
    const questionNum = i + 1;

    // Validate options count (at least 2)
    if (!question.options || !Array.isArray(question.options)) {
      errors.push({
        type: 'INVALID_OPTIONS_FIELD',
        message: `Question ${questionNum} in entry "${key}" must have an options array`,
        field: `questions[${i}].options`,
        value: question.options
      });
      continue;
    }

    if (question.options.length < 2) {
      errors.push({
        type: 'INSUFFICIENT_OPTIONS',
        message: `Question ${questionNum} in entry "${key}" must have at least 2 options, found ${question.options.length}`,
        field: `questions[${i}].options`,
        value: question.options.length
      });
    }

    // Validate correct answer exists and is valid
    if (!question.correct_answer || typeof question.correct_answer !== 'string') {
      errors.push({
        type: 'MISSING_CORRECT_ANSWER',
        message: `Question ${questionNum} in entry "${key}" must have a correct_answer string`,
        field: `questions[${i}].correct_answer`,
        value: question.correct_answer
      });
      continue;
    }

    // Validate correct answer is one of the option letters
    const optionLetters = question.options.map(opt => opt.charAt(0));
    if (!optionLetters.includes(question.correct_answer)) {
      errors.push({
        type: 'INVALID_CORRECT_ANSWER',
        message: `Question ${questionNum} in entry "${key}" has correct_answer "${question.correct_answer}" which is not one of the available options: ${optionLetters.join(', ')}`,
        field: `questions[${i}].correct_answer`,
        value: question.correct_answer
      });
    }

    // Count how many times the correct answer appears (should be exactly 1)
    const correctAnswerCount = optionLetters.filter(letter => letter === question.correct_answer).length;
    if (correctAnswerCount !== 1) {
      errors.push({
        type: 'MULTIPLE_CORRECT_ANSWERS',
        message: `Question ${questionNum} in entry "${key}" has ${correctAnswerCount} options with letter "${question.correct_answer}", expected exactly 1`,
        field: `questions[${i}].correct_answer`,
        value: correctAnswerCount
      });
    }
  }

  return errors;
}

/**
 * Validate Module_ID format and learning path validity
 *
 * @param entry - Entry to validate
 * @param key - Entry key for error reporting
 * @returns Array of validation errors (empty if valid)
 */
function validateModuleId(
  entry: QuizEntry | ModuleEntry | CapstoneEntry,
  key: string
): ValidationError[] {
  const errors: ValidationError[] = [];

  if (!entry.module_id || typeof entry.module_id !== 'string') {
    errors.push({
      type: 'MISSING_MODULE_ID',
      message: `Entry "${key}" must have a module_id string`,
      field: 'module_id',
      value: entry.module_id
    });
    return errors;
  }

  // Validate format: {learning_path}/{topic_slug}
  const parts = entry.module_id.split('/');
  if (parts.length < 2) {
    errors.push({
      type: 'INVALID_MODULE_ID_FORMAT',
      message: `Module_ID "${entry.module_id}" in entry "${key}" must be in format "{learning_path}/{topic_slug}"`,
      field: 'module_id',
      value: entry.module_id
    });
    return errors;
  }

  const learningPath = parts[0];
  const topicSlug = parts[parts.length - 1];

  // Validate learning path is not empty
  if (!learningPath || learningPath.length === 0) {
    errors.push({
      type: 'EMPTY_LEARNING_PATH',
      message: `Learning path in module_id "${entry.module_id}" for entry "${key}" cannot be empty`,
      field: 'module_id',
      value: entry.module_id
    });
  }

  // Validate topic slug is not empty
  if (!topicSlug || topicSlug.length === 0) {
    errors.push({
      type: 'EMPTY_TOPIC_SLUG',
      message: `Topic slug in module_id "${entry.module_id}" for entry "${key}" cannot be empty`,
      field: 'module_id',
      value: entry.module_id
    });
  }

  // Validate format (alphanumeric + hyphens/underscores)
  const validFormatRegex = /^[a-zA-Z0-9_-]+$/;

  if (!validFormatRegex.test(learningPath)) {
    errors.push({
      type: 'INVALID_LEARNING_PATH_FORMAT',
      message: `Learning path "${learningPath}" in module_id for entry "${key}" must contain only alphanumeric characters, hyphens, and underscores`,
      field: 'module_id',
      value: learningPath
    });
  }

  if (!validFormatRegex.test(topicSlug)) {
    errors.push({
      type: 'INVALID_TOPIC_SLUG_FORMAT',
      message: `Topic slug "${topicSlug}" in module_id for entry "${key}" must contain only alphanumeric characters, hyphens, and underscores`,
      field: 'module_id',
      value: topicSlug
    });
  }

  return errors;
}

/**
 * Validate required fields for each content_type
 *
 * @param entry - Entry to validate
 * @param key - Entry key for error reporting
 * @returns Array of validation errors (empty if valid)
 */
function validateRequiredFields(
  entry: QuizEntry | ModuleEntry | CapstoneEntry | WalkthroughEntry,
  key: string
): ValidationError[] {
  const errors: ValidationError[] = [];

  // Common validation for all types
  if (!entry.content_type) {
    errors.push({
      type: 'MISSING_CONTENT_TYPE',
      message: `Entry "${key}" must have a content_type field`,
      field: 'content_type',
      value: (entry as any).content_type
    });
    return errors; // Return early if no content_type
  }

  // Type-specific validation
  switch (entry.content_type) {
    case 'quiz': {
      const quizEntry = entry as QuizEntry;
      if (!quizEntry.topic_slug) {
        errors.push({
          type: 'MISSING_TOPIC_SLUG',
          message: `Quiz entry "${key}" must have a topic_slug field`,
          field: 'topic_slug'
        });
      }
      if (!quizEntry.module_id) {
        errors.push({
          type: 'MISSING_MODULE_ID',
          message: `Quiz entry "${key}" must have a module_id field`,
          field: 'module_id'
        });
      }
      if (quizEntry.passing_score === undefined || quizEntry.passing_score === null) {
        errors.push({
          type: 'MISSING_PASSING_SCORE',
          message: `Quiz entry "${key}" must have a passing_score field`,
          field: 'passing_score'
        });
      }
      if (!quizEntry.questions || !Array.isArray(quizEntry.questions)) {
        errors.push({
          type: 'MISSING_QUESTIONS',
          message: `Quiz entry "${key}" must have a questions array`,
          field: 'questions'
        });
      }
      if (typeof quizEntry.question_count !== 'number') {
        errors.push({
          type: 'MISSING_QUESTION_COUNT',
          message: `Quiz entry "${key}" must have a question_count number`,
          field: 'question_count'
        });
      }
      break;
    }

    case 'module': {
      const moduleEntry = entry as ModuleEntry;
      if (!moduleEntry.topic_slug) {
        errors.push({
          type: 'MISSING_TOPIC_SLUG',
          message: `Module entry "${key}" must have a topic_slug field`,
          field: 'topic_slug'
        });
      }
      if (!moduleEntry.module_id) {
        errors.push({
          type: 'MISSING_MODULE_ID',
          message: `Module entry "${key}" must have a module_id field`,
          field: 'module_id'
        });
      }
      if (typeof moduleEntry.module_number !== 'number') {
        errors.push({
          type: 'MISSING_MODULE_NUMBER',
          message: `Module entry "${key}" must have a module_number field`,
          field: 'module_number'
        });
      }
      if (!moduleEntry.title) {
        errors.push({
          type: 'MISSING_TITLE',
          message: `Module entry "${key}" must have a title field`,
          field: 'title'
        });
      }
      if (typeof moduleEntry.reading_time !== 'number') {
        errors.push({
          type: 'MISSING_READING_TIME',
          message: `Module entry "${key}" must have a reading_time field`,
          field: 'reading_time'
        });
      }
      if (typeof moduleEntry.has_quiz !== 'boolean') {
        errors.push({
          type: 'MISSING_HAS_QUIZ',
          message: `Module entry "${key}" must have a has_quiz boolean field`,
          field: 'has_quiz'
        });
      }
      break;
    }

    case 'capstone': {
      const capstoneEntry = entry as CapstoneEntry;
      if (!capstoneEntry.topic_slug) {
        errors.push({
          type: 'MISSING_TOPIC_SLUG',
          message: `Capstone entry "${key}" must have a topic_slug field`,
          field: 'topic_slug'
        });
      }
      if (!capstoneEntry.module_id) {
        errors.push({
          type: 'MISSING_MODULE_ID',
          message: `Capstone entry "${key}" must have a module_id field`,
          field: 'module_id'
        });
      }
      if (!capstoneEntry.title) {
        errors.push({
          type: 'MISSING_TITLE',
          message: `Capstone entry "${key}" must have a title field`,
          field: 'title'
        });
      }
      if (!capstoneEntry.description) {
        errors.push({
          type: 'MISSING_DESCRIPTION',
          message: `Capstone entry "${key}" must have a description field`,
          field: 'description'
        });
      }
      if (!Array.isArray(capstoneEntry.submission_requirements)) {
        errors.push({
          type: 'MISSING_SUBMISSION_REQUIREMENTS',
          message: `Capstone entry "${key}" must have a submission_requirements array`,
          field: 'submission_requirements'
        });
      }
      if (!Array.isArray(capstoneEntry.evaluation_criteria)) {
        errors.push({
          type: 'MISSING_EVALUATION_CRITERIA',
          message: `Capstone entry "${key}" must have an evaluation_criteria array`,
          field: 'evaluation_criteria'
        });
      }
      break;
    }

    case 'walkthrough': {
      const walkthroughEntry = entry as WalkthroughEntry;
      if (!walkthroughEntry.id) {
        errors.push({
          type: 'MISSING_ID',
          message: `Walkthrough entry "${key}" must have an id field`,
          field: 'id'
        });
      }
      if (!walkthroughEntry.title) {
        errors.push({
          type: 'MISSING_TITLE',
          message: `Walkthrough entry "${key}" must have a title field`,
          field: 'title'
        });
      }
      if (!walkthroughEntry.description) {
        errors.push({
          type: 'MISSING_DESCRIPTION',
          message: `Walkthrough entry "${key}" must have a description field`,
          field: 'description'
        });
      }
      if (!walkthroughEntry.difficulty || !['Beginner', 'Intermediate', 'Advanced'].includes(walkthroughEntry.difficulty)) {
        errors.push({
          type: 'INVALID_DIFFICULTY',
          message: `Walkthrough entry "${key}" must have a difficulty field with value "Beginner", "Intermediate", or "Advanced"`,
          field: 'difficulty',
          value: walkthroughEntry.difficulty
        });
      }
      if (!Array.isArray(walkthroughEntry.topics)) {
        errors.push({
          type: 'MISSING_TOPICS',
          message: `Walkthrough entry "${key}" must have a topics array`,
          field: 'topics'
        });
      }
      if (typeof walkthroughEntry.estimated_time !== 'number') {
        errors.push({
          type: 'MISSING_ESTIMATED_TIME',
          message: `Walkthrough entry "${key}" must have an estimated_time number`,
          field: 'estimated_time'
        });
      }
      if (!Array.isArray(walkthroughEntry.prerequisites)) {
        errors.push({
          type: 'MISSING_PREREQUISITES',
          message: `Walkthrough entry "${key}" must have a prerequisites array`,
          field: 'prerequisites'
        });
      }
      if (!walkthroughEntry.repository) {
        errors.push({
          type: 'MISSING_REPOSITORY',
          message: `Walkthrough entry "${key}" must have a repository field`,
          field: 'repository'
        });
      }
      break;
    }

    default:
      errors.push({
        type: 'UNKNOWN_CONTENT_TYPE',
        message: `Entry "${key}" has unknown content_type: ${(entry as any).content_type}`,
        field: 'content_type',
        value: (entry as any).content_type
      });
  }

  return errors;
}

/**
 * Validate the complete content registry
 *
 * Performs comprehensive validation including:
 * - Topic_Slug uniqueness across all entries
 * - Passing_score range (0-100) for quizzes
 * - Question structure (at least 2 options, exactly 1 correct answer)
 * - Module_ID format and learning path validity
 * - Required fields for each content_type
 *
 * @param registry - Content registry to validate
 * @param entryFilePaths - Optional map of entry keys to file paths for error reporting
 * @returns Validation result with errors and warnings
 */
function validateRegistry(registry: ContentRegistry, entryFilePaths?: Map<string, string>): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  console.log('\nValidating content registry...');

  // Validate schema version
  if (!registry.schema_version) {
    errors.push({
      type: 'MISSING_SCHEMA_VERSION',
      message: 'Registry must have a schema_version field',
      field: 'schema_version'
    });
  }

  // Validate generated_at
  if (!registry.generated_at) {
    errors.push({
      type: 'MISSING_GENERATED_AT',
      message: 'Registry must have a generated_at field',
      field: 'generated_at'
    });
  }

  // Validate entries exist
  if (!registry.entries || typeof registry.entries !== 'object') {
    errors.push({
      type: 'MISSING_ENTRIES',
      message: 'Registry must have an entries object',
      field: 'entries'
    });
    return { valid: false, errors, warnings };
  }

  // Validate Topic_Slug uniqueness
  console.log('  Checking topic slug uniqueness...');
  const uniquenessErrors = validateTopicSlugUniqueness(registry.entries);
  // Add file paths to uniqueness errors
  if (entryFilePaths) {
    uniquenessErrors.forEach(error => {
      // Extract the first entry key from the error message to get a file path
      const match = error.message.match(/entries: ([^,]+)/);
      if (match) {
        const firstKey = match[1].trim();
        error.filePath = entryFilePaths.get(firstKey);
      }
    });
  }
  errors.push(...uniquenessErrors);

  // Validate each entry
  console.log('  Validating individual entries...');
  for (const [key, entry] of Object.entries(registry.entries)) {
    const filePath = entryFilePaths?.get(key);
    
    // Validate required fields
    const fieldErrors = validateRequiredFields(entry, key);
    fieldErrors.forEach(err => { err.filePath = filePath; });
    errors.push(...fieldErrors);

    // Type-specific validation
    if (entry.content_type === 'quiz') {
      // Validate passing_score
      const scoreErrors = validatePassingScore(entry, key);
      scoreErrors.forEach(err => { err.filePath = filePath; });
      errors.push(...scoreErrors);

      // Validate question structure
      const questionErrors = validateQuestionStructure(entry, key);
      questionErrors.forEach(err => { err.filePath = filePath; });
      errors.push(...questionErrors);

      // Validate module_id
      const moduleIdErrors = validateModuleId(entry, key);
      moduleIdErrors.forEach(err => { err.filePath = filePath; });
      errors.push(...moduleIdErrors);
    } else if (entry.content_type === 'module' || entry.content_type === 'capstone') {
      // Validate module_id
      const moduleIdErrors = validateModuleId(entry, key);
      moduleIdErrors.forEach(err => { err.filePath = filePath; });
      errors.push(...moduleIdErrors);
    }
  }

  const valid = errors.length === 0;

  if (valid) {
    console.log('  ✓ Validation passed!');
  } else {
    console.log(`  ✗ Validation failed with ${errors.length} error(s)`);
  }

  return { valid, errors, warnings };
}

/**
 * Sort object keys alphabetically
 * 
 * Recursively sorts all keys in an object and its nested objects/arrays
 * to ensure consistent ordering for diffs.
 * 
 * @param obj - Object to sort
 * @returns New object with sorted keys
 */
function sortObjectKeys(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  if (Array.isArray(obj)) {
    return obj.map(item => sortObjectKeys(item));
  }
  
  if (typeof obj === 'object') {
    const sorted: any = {};
    const keys = Object.keys(obj).sort();
    
    for (const key of keys) {
      sorted[key] = sortObjectKeys(obj[key]);
    }
    
    return sorted;
  }
  
  return obj;
}

/**
 * Pretty print Content Registry JSON with formatting rules
 * 
 * Formats the registry with:
 * - 2-space indentation for readability
 * - Alphabetically sorted keys within each entry for consistent diffs
 * - Consistent formatting across all entries
 * 
 * **Validates: Requirements 11.1, 11.2, 11.4, 11.5**
 * 
 * @param registry - Content registry to format
 * @returns Formatted JSON string
 */
function prettyPrintRegistry(registry: ContentRegistry): string {
  // Sort all keys alphabetically for consistent diffs
  const sortedRegistry = sortObjectKeys(registry);
  
  // Format with 2-space indentation
  return JSON.stringify(sortedRegistry, null, 2);
}

/**
 * Parse JSON with descriptive error handling
 * 
 * Attempts to parse JSON and provides descriptive error messages
 * if the JSON is malformed.
 * 
 * **Validates: Requirements 2.6, 11.6**
 * 
 * @param json - JSON string to parse
 * @returns Parsed object
 * @throws Error with descriptive message if JSON is malformed
 */
function parseRegistryJSON(json: string): ContentRegistry {
  try {
    return JSON.parse(json);
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(
        `Malformed JSON: ${error.message}. Please check the JSON syntax and ensure all brackets, quotes, and commas are properly formatted.`
      );
    }
    throw new Error(
      `Failed to parse JSON: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Generate versioned filename for S3 upload
 * Format: v{schema_version}-{YYYYMMDD}-{HHMMSS}.json
 * 
 * **Validates: Requirements 3.3**
 * 
 * @param schemaVersion - Schema version from registry
 * @param timestamp - Date object for timestamp (defaults to now)
 * @returns Versioned filename
 * 
 * @example
 * generateVersionedFilename("1.0.0") // Returns: "v1.0.0-20240115-103045.json"
 */
function generateVersionedFilename(schemaVersion: string, timestamp: Date = new Date()): string {
  // Format date as YYYYMMDD (using UTC)
  const year = timestamp.getUTCFullYear();
  const month = String(timestamp.getUTCMonth() + 1).padStart(2, '0');
  const day = String(timestamp.getUTCDate()).padStart(2, '0');
  const dateStr = `${year}${month}${day}`;
  
  // Format time as HHMMSS (using UTC)
  const hours = String(timestamp.getUTCHours()).padStart(2, '0');
  const minutes = String(timestamp.getUTCMinutes()).padStart(2, '0');
  const seconds = String(timestamp.getUTCSeconds()).padStart(2, '0');
  const timeStr = `${hours}${minutes}${seconds}`;
  
  return `v${schemaVersion}-${dateStr}-${timeStr}.json`;
}

/**
 * Upload Content Registry to S3 with versioning
 * 
 * Uploads the registry to S3 with both:
 * - Versioned key: content-registry/v{schema_version}-{YYYYMMDD}-{HHMMSS}.json
 * - Latest key: content-registry/latest.json
 * 
 * **Validates: Requirements 3.1, 3.3, 3.4, 3.5**
 * 
 * @param registry - Content registry to upload
 * @param bucket - S3 bucket name
 * @param region - AWS region (defaults to us-east-1)
 * @throws Error if S3 upload fails with descriptive message
 */
async function uploadToS3(
  registry: ContentRegistry,
  bucket: string,
  region: string = 'us-east-1'
): Promise<void> {
  try {
    // Initialize S3 client
    const s3Client = new S3Client({ region });
    
    // Pretty print the registry
    const json = prettyPrintRegistry(registry);
    
    // Generate versioned filename
    const timestamp = new Date(registry.generated_at);
    const versionedFilename = generateVersionedFilename(registry.schema_version, timestamp);
    const versionedKey = `content-registry/${versionedFilename}`;
    const latestKey = 'content-registry/latest.json';
    
    console.log(`\nUploading to S3 bucket: ${bucket}`);
    console.log(`  Region: ${region}`);
    
    // Upload versioned file
    console.log(`  Uploading versioned file: ${versionedKey}`);
    try {
      await s3Client.send(new PutObjectCommand({
        Bucket: bucket,
        Key: versionedKey,
        Body: json,
        ContentType: 'application/json',
        ServerSideEncryption: 'AES256'
      }));
      console.log(`  ✓ Versioned file uploaded successfully`);
    } catch (error) {
      throw new Error(
        `Failed to upload versioned file to s3://${bucket}/${versionedKey}: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
    
    // Upload latest file
    console.log(`  Uploading latest file: ${latestKey}`);
    try {
      await s3Client.send(new PutObjectCommand({
        Bucket: bucket,
        Key: latestKey,
        Body: json,
        ContentType: 'application/json',
        ServerSideEncryption: 'AES256'
      }));
      console.log(`  ✓ Latest file uploaded successfully`);
    } catch (error) {
      throw new Error(
        `Failed to upload latest file to s3://${bucket}/${latestKey}: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
    
    console.log(`\n✓ Registry uploaded to S3 successfully`);
    console.log(`  Versioned: s3://${bucket}/${versionedKey}`);
    console.log(`  Latest: s3://${bucket}/${latestKey}`);
    
    // Clean up old versions (keep 5 most recent)
    await cleanupOldVersions(bucket, region, 5);
    
  } catch (error) {
    // Re-throw with descriptive error message
    if (error instanceof Error && error.message.includes('Failed to upload')) {
      throw error;
    }
    
    throw new Error(
      `S3 upload failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}
/**
 * Clean up old registry versions in S3, keeping only the 5 most recent
 *
 * @param bucket - S3 bucket name
 * @param region - AWS region
 * @param maxVersions - Maximum number of versions to keep (default: 5)
 * @throws Error if cleanup fails
 */
async function cleanupOldVersions(
  bucket: string,
  region: string = 'us-east-1',
  maxVersions: number = 5
): Promise<void> {
  try {
    const s3Client = new S3Client({ region });

    console.log(`\nCleaning up old registry versions (keeping ${maxVersions} most recent)...`);

    // List all versioned registry files
    const listCommand = new ListObjectsV2Command({
      Bucket: bucket,
      Prefix: 'content-registry/v',
      MaxKeys: 1000
    });

    const listResponse = await s3Client.send(listCommand);

    if (!listResponse.Contents || listResponse.Contents.length === 0) {
      console.log('  No versioned files found');
      return;
    }

    // Filter to only versioned files (exclude latest.json)
    const versionedFiles = listResponse.Contents
      .filter(obj => obj.Key && obj.Key.match(/^content-registry\/v\d+\.\d+\.\d+-\d{8}-\d{6}\.json$/))
      .sort((a, b) => {
        // Sort by LastModified in descending order (newest first)
        const timeA = a.LastModified?.getTime() || 0;
        const timeB = b.LastModified?.getTime() || 0;
        return timeB - timeA;
      });

    console.log(`  Found ${versionedFiles.length} versioned file(s)`);

    // Keep only the most recent maxVersions files
    const filesToDelete = versionedFiles.slice(maxVersions);

    if (filesToDelete.length === 0) {
      console.log(`  All versions within retention limit (${maxVersions})`);
      return;
    }

    console.log(`  Deleting ${filesToDelete.length} old version(s)...`);

    // Delete old versions
    for (const file of filesToDelete) {
      if (!file.Key) continue;

      try {
        await s3Client.send(new DeleteObjectCommand({
          Bucket: bucket,
          Key: file.Key
        }));
        console.log(`    ✓ Deleted: ${file.Key}`);
      } catch (error) {
        console.warn(`    ⚠ Failed to delete ${file.Key}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    console.log(`  ✓ Cleanup complete`);

  } catch (error) {
    throw new Error(
      `Failed to cleanup old versions: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Print help text and usage examples
 */
function printHelp(): void {
  console.log(`
Content Registry Generator

USAGE:
  npm run generate-registry [OPTIONS]
  node scripts/generate-content-registry.ts [OPTIONS]

DESCRIPTION:
  Generates a unified content registry from markdown files (quizzes, modules,
  capstones, and walkthroughs). The registry serves as the single source of
  truth for the backend validation services.

OPTIONS:
  --validate-only    Validate content files without uploading to S3
                     Useful for CI/CD validation steps and local testing

  --output=PATH      Write the generated registry to the specified file path
                     Example: --output=./dist/content-registry.json

  --verbose          Enable detailed logging during generation
                     Shows configuration, parsing progress, and validation details

  --help, -h         Display this help message and exit

ENVIRONMENT VARIABLES:
  S3_BUCKET or CONTENT_REGISTRY_BUCKET
                     S3 bucket name for registry upload (required for upload)

  AWS_REGION or S3_REGION
                     AWS region for S3 bucket (default: us-east-1)

EXAMPLES:
  # Generate and upload registry to S3
  npm run generate-registry

  # Validate content without uploading
  npm run generate-registry -- --validate-only

  # Generate with verbose output and save to file
  npm run generate-registry -- --verbose --output=./registry.json

  # Validate only with verbose logging (useful for debugging)
  npm run generate-registry -- --validate-only --verbose

  # Generate and upload with custom S3 bucket
  S3_BUCKET=my-content-bucket npm run generate-registry

EXIT CODES:
  0    Success - registry generated and validated
  1    Error - validation failed or generation error occurred
`);
}

// Placeholder for main functionality
async function main() {
  // Parse command-line arguments
  const args = process.argv.slice(2);
  
  // Check for help flag first
  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
    process.exit(0);
  }
  
  const validateOnly = args.includes('--validate-only');
  const verbose = args.includes('--verbose');
  
  // Parse --output flag with validation
  let outputPath: string | undefined;
  const outputArg = args.find(arg => arg.startsWith('--output='));
  if (outputArg) {
    outputPath = outputArg.split('=')[1];
    if (!outputPath || outputPath.trim().length === 0) {
      console.error('Error: --output flag requires a path value');
      console.error('Usage: --output=./path/to/output.json');
      process.exit(1);
    }
  }
  
  // Check for unknown flags
  const knownFlags = ['--validate-only', '--verbose', '--help', '-h'];
  const unknownFlags = args.filter(arg => 
    arg.startsWith('--') && 
    !knownFlags.includes(arg) && 
    !arg.startsWith('--output=')
  );
  
  if (unknownFlags.length > 0) {
    console.error(`Error: Unknown flag(s): ${unknownFlags.join(', ')}`);
    console.error('Run with --help to see available options');
    process.exit(1);
  }
  
  console.log('Content Registry Generator - Starting...');
  
  // Get S3 configuration from environment variables
  const s3Bucket = process.env.S3_BUCKET || process.env.CONTENT_REGISTRY_BUCKET;
  const s3Region = process.env.AWS_REGION || process.env.S3_REGION || 'us-east-1';
  
  if (verbose) {
    console.log('Configuration:');
    console.log(`  Validate only: ${validateOnly}`);
    console.log(`  Output path: ${outputPath || 'none'}`);
    console.log(`  S3 bucket: ${s3Bucket || 'not configured'}`);
    console.log(`  S3 region: ${s3Region}`);
    console.log('');
  }
  
  try {
    // Generate the complete registry
    const registry = await generateRegistry('content');
    
    // Output summary
    console.log('\n=== Registry Summary ===');
    console.log(`Total entries: ${Object.keys(registry.entries).length}`);
    
    // Count by content type
    const counts = {
      quiz: 0,
      module: 0,
      capstone: 0,
      walkthrough: 0
    };
    
    Object.values(registry.entries).forEach(entry => {
      counts[entry.content_type]++;
    });
    
    console.log(`  Quizzes: ${counts.quiz}`);
    console.log(`  Modules: ${counts.module}`);
    console.log(`  Capstones: ${counts.capstone}`);
    console.log(`  Walkthroughs: ${counts.walkthrough}`);
    console.log(`\nSchema version: ${registry.schema_version}`);
    console.log(`Generated at: ${registry.generated_at}`);
    console.log(`Generator version: ${registry.generator_version}`);
    
    // Write to output file if specified
    if (outputPath) {
      // Ensure the directory exists
      const outputDir = path.dirname(outputPath);
      await fs.mkdir(outputDir, { recursive: true });
      
      const json = prettyPrintRegistry(registry);
      await fs.writeFile(outputPath, json, 'utf-8');
      console.log(`\n✓ Registry written to: ${outputPath}`);
    }
    
    // Upload to S3 unless validate-only mode
    if (!validateOnly) {
      if (!s3Bucket) {
        console.warn('\n⚠ Warning: S3_BUCKET or CONTENT_REGISTRY_BUCKET environment variable not set');
        console.warn('  Skipping S3 upload. Set the environment variable to enable upload.');
      } else {
        await uploadToS3(registry, s3Bucket, s3Region);
      }
    } else {
      console.log('\n✓ Validation only mode - skipping S3 upload');
    }
    
    console.log('\n✓ Content Registry Generator - Complete');
    
    return registry;
  } catch (error) {
    console.error('\n❌ Error generating registry:', error);
    throw error;
  }
}

// Execute if run directly
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch((error) => {
    console.error('Error:', error);
    process.exit(1);
  });
}

export { 
  main,
  generateRegistry,
  validateRegistry,
  validateTopicSlugUniqueness,
  validatePassingScore,
  validateQuestionStructure,
  validateModuleId,
  validateRequiredFields,
  discoverQuizFiles,
  discoverModuleFiles,
  discoverCapstoneFiles,
  discoverWalkthroughFiles,
  parseFrontmatter,
  extractQuizMetadata,
  parseQuestions,
  parseQuizFile,
  parseWalkthroughFile,
  extractOptions,
  extractCorrectAnswer,
  extractExplanation,
  parseModuleFile,
  extractModuleNumber,
  calculateReadingTime,
  parseCapstoneFile,
  extractSubmissionRequirements,
  extractEvaluationCriteria,
  extractTitle,
  extractDescription,
  extractEstimatedTime,
  extractPrerequisites,
  inferDifficulty,
  extractTopics,
  extractTopicSlug,
  prettyPrintRegistry,
  parseRegistryJSON,
  sortObjectKeys,
  generateVersionedFilename,
  uploadToS3,
  cleanupOldVersions,
  FrontmatterParsingError,
  QuestionParsingError
};

export type { 
  QuizQuestion, 
  QuizEntry, 
  ModuleEntry, 
  CapstoneEntry, 
  WalkthroughEntry, 
  ContentRegistry,
  ValidationError,
  ValidationResult
};
