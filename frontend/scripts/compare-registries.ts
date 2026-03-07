#!/usr/bin/env tsx
/**
 * Registry Comparison Script
 * 
 * Compares the generated content registry with the hardcoded quiz_registry.py
 * to verify migration compatibility.
 */

import * as fs from 'fs';
import * as path from 'path';

interface QuizQuestion {
  id: string;
  correct_answer: string;
  explanation: string;
}

interface HardcodedQuiz {
  passing_score: number;
  questions: QuizQuestion[];
}

interface HardcodedRegistry {
  [key: string]: HardcodedQuiz;
}

interface GeneratedQuizEntry {
  content_type: 'quiz';
  topic_slug: string;
  module_id: string;
  passing_score: number;
  question_count: number;
  questions: Array<{
    id: string;
    question_text: string;
    options: string[];
    correct_answer: string;
    explanation: string;
  }>;
}

interface ContentRegistry {
  schema_version: string;
  generated_at: string;
  generator_version: string;
  entries: {
    [topic_slug: string]: GeneratedQuizEntry | any;
  };
}

// Hardcoded registry from backend/services/quiz_registry.py
const HARDCODED_REGISTRY: HardcodedRegistry = {
  "prerequisites": {
    "passing_score": 70,
    "questions": [
      { "id": "q1", "correct_answer": "C", "explanation": "DevSecOps workflows rely heavily on version control systems like Git for managing source code, pull requests, branching strategies, and triggering automated pipeline builds." },
      { "id": "q2", "correct_answer": "B", "explanation": "DevSecOps professionals frequently operate in Linux environments and must be comfortable navigating the command line, managing processes, and automating tasks using Bash scripting." },
      { "id": "q3", "correct_answer": "C", "explanation": "DevSecOps involves scripting, Infrastructure as Code, APIs, and automation. Understanding programming concepts enables secure and effective automation." },
      { "id": "q4", "correct_answer": "B", "explanation": "Understanding IP addressing, DNS, firewalls, and protocols like HTTP/HTTPS is fundamental to configuring and securing cloud and on-prem environments." },
      { "id": "q5", "correct_answer": "B", "explanation": "Security fundamentals include encryption, authentication, access control, and understanding common threats such as malware and phishing." },
      { "id": "q6", "correct_answer": "C", "explanation": "DevSecOps extends DevOps by integrating security into automation and collaboration practices. Without DevOps foundations, DevSecOps concepts will not make sense." },
      { "id": "q7", "correct_answer": "B", "explanation": "Continuous Integration and Continuous Delivery pipelines are where security tools and automation are integrated into the development lifecycle." },
      { "id": "q8", "correct_answer": "C", "explanation": "Cloud knowledge allows you to build scalable DevSecOps solutions by leveraging managed services, identity systems, and automation capabilities provided by cloud platforms." },
      { "id": "q9", "correct_answer": "B", "explanation": "The Prerequisites section ensures learners have the foundational understanding necessary before diving into deeper DevSecOps and Cloud Security Development topics." }
    ]
  },
  "secure-sdlc": {
    "passing_score": 70,
    "questions": [
      { "id": "q1", "correct_answer": "B", "explanation": "Secure SDLC (SSDLC) embeds security practices throughout the entire software development lifecycle, from planning to deployment and maintenance. This proactive approach helps identify and mitigate security vulnerabilities early in the development process." },
      { "id": "q2", "correct_answer": "C", "explanation": "Threat modeling is a structured approach to identify potential security threats and vulnerabilities in a system's design. It helps teams understand attack vectors and prioritize security controls before implementation begins." },
      { "id": "q3", "correct_answer": "A", "explanation": "Static Application Security Testing (SAST) analyzes source code without executing it to identify security vulnerabilities. It's most effective when integrated early in the development process, allowing developers to fix issues before they reach production." },
      { "id": "q4", "correct_answer": "D", "explanation": "Dynamic Application Security Testing (DAST) tests running applications to identify security vulnerabilities by simulating attacks. Unlike SAST, DAST doesn't require access to source code and can identify runtime and environment-specific issues." },
      { "id": "q5", "correct_answer": "B", "explanation": "Security code reviews should be performed continuously throughout development, not just at the end. Regular reviews help catch security issues early when they're easier and less expensive to fix, and they promote security awareness among the development team." }
    ]
  }
};

// Mapping from hardcoded keys to generated topic_slugs
const KEY_MAPPING: { [key: string]: string } = {
  "prerequisites": "prerequisites",
  "secure-sdlc": "what_is_the_secure_sdlc"
};

function loadGeneratedRegistry(filePath: string): ContentRegistry {
  const content = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(content);
}

function compareQuizzes(): void {
  console.log('Registry Comparison Report');
  console.log('='.repeat(80));
  console.log();

  const registryPath = path.join(__dirname, '../content-registry.json');
  
  if (!fs.existsSync(registryPath)) {
    console.error('❌ Generated registry not found at:', registryPath);
    console.error('   Run: npm run generate-registry -- --output=content-registry.json --validate-only');
    process.exit(1);
  }

  const generatedRegistry = loadGeneratedRegistry(registryPath);
  
  console.log('📊 Registry Statistics:');
  console.log(`   Generated at: ${generatedRegistry.generated_at}`);
  console.log(`   Schema version: ${generatedRegistry.schema_version}`);
  console.log(`   Total entries: ${Object.keys(generatedRegistry.entries).length}`);
  console.log();

  let allMatch = true;
  let totalDiscrepancies = 0;

  for (const [hardcodedKey, hardcodedQuiz] of Object.entries(HARDCODED_REGISTRY)) {
    const topicSlug = KEY_MAPPING[hardcodedKey];
    console.log(`\n🔍 Comparing: "${hardcodedKey}" → "${topicSlug}"`);
    console.log('-'.repeat(80));

    const generatedEntry = generatedRegistry.entries[topicSlug];
    
    if (!generatedEntry) {
      console.error(`   ❌ Quiz not found in generated registry: ${topicSlug}`);
      allMatch = false;
      totalDiscrepancies++;
      continue;
    }

    if (generatedEntry.content_type !== 'quiz') {
      console.error(`   ❌ Entry is not a quiz: ${generatedEntry.content_type}`);
      allMatch = false;
      totalDiscrepancies++;
      continue;
    }

    const generatedQuiz = generatedEntry as GeneratedQuizEntry;

    // Compare passing scores
    console.log(`\n   Passing Score:`);
    console.log(`     Hardcoded: ${hardcodedQuiz.passing_score}%`);
    console.log(`     Generated: ${generatedQuiz.passing_score}%`);
    
    if (hardcodedQuiz.passing_score !== generatedQuiz.passing_score) {
      console.log(`     ⚠️  MISMATCH: Passing scores differ`);
      totalDiscrepancies++;
    } else {
      console.log(`     ✓ Match`);
    }

    // Compare question counts
    console.log(`\n   Question Count:`);
    console.log(`     Hardcoded: ${hardcodedQuiz.questions.length}`);
    console.log(`     Generated: ${generatedQuiz.question_count}`);
    
    if (hardcodedQuiz.questions.length !== generatedQuiz.question_count) {
      console.log(`     ⚠️  MISMATCH: Question counts differ`);
      totalDiscrepancies++;
    } else {
      console.log(`     ✓ Match`);
    }

    // Compare individual questions
    console.log(`\n   Questions:`);
    const maxQuestions = Math.max(hardcodedQuiz.questions.length, generatedQuiz.questions.length);
    
    for (let i = 0; i < maxQuestions; i++) {
      const hardcodedQ = hardcodedQuiz.questions[i];
      const generatedQ = generatedQuiz.questions[i];

      if (!hardcodedQ) {
        console.log(`     ⚠️  Question ${i + 1}: Only in generated registry`);
        totalDiscrepancies++;
        continue;
      }

      if (!generatedQ) {
        console.log(`     ⚠️  Question ${i + 1}: Only in hardcoded registry`);
        totalDiscrepancies++;
        continue;
      }

      const idMatch = hardcodedQ.id === generatedQ.id;
      const answerMatch = hardcodedQ.correct_answer === generatedQ.correct_answer;
      const explanationMatch = hardcodedQ.explanation === generatedQ.explanation;

      if (idMatch && answerMatch && explanationMatch) {
        console.log(`     ✓ Question ${i + 1} (${generatedQ.id}): All fields match`);
      } else {
        console.log(`     ⚠️  Question ${i + 1} (${generatedQ.id}): Discrepancies found`);
        if (!idMatch) {
          console.log(`        - ID: "${hardcodedQ.id}" vs "${generatedQ.id}"`);
          totalDiscrepancies++;
        }
        if (!answerMatch) {
          console.log(`        - Answer: "${hardcodedQ.correct_answer}" vs "${generatedQ.correct_answer}"`);
          totalDiscrepancies++;
        }
        if (!explanationMatch) {
          console.log(`        - Explanation differs`);
          totalDiscrepancies++;
        }
        allMatch = false;
      }
    }
  }

  // Check for additional quizzes in generated registry
  console.log(`\n\n📋 Additional Quizzes in Generated Registry:`);
  console.log('-'.repeat(80));
  
  const hardcodedTopicSlugs = Object.values(KEY_MAPPING);
  const additionalQuizzes = Object.entries(generatedRegistry.entries)
    .filter(([slug, entry]) => entry.content_type === 'quiz' && !hardcodedTopicSlugs.includes(slug))
    .map(([slug, entry]) => ({ slug, module_id: entry.module_id }));

  if (additionalQuizzes.length > 0) {
    console.log(`   Found ${additionalQuizzes.length} additional quizzes:`);
    additionalQuizzes.forEach(({ slug, module_id }) => {
      console.log(`     • ${slug} (${module_id})`);
    });
  } else {
    console.log(`   No additional quizzes found.`);
  }

  // Summary
  console.log(`\n\n${'='.repeat(80)}`);
  console.log('📊 Summary:');
  console.log(`   Hardcoded quizzes checked: ${Object.keys(HARDCODED_REGISTRY).length}`);
  console.log(`   Total quizzes in generated registry: ${Object.values(generatedRegistry.entries).filter(e => e.content_type === 'quiz').length}`);
  console.log(`   Total discrepancies: ${totalDiscrepancies}`);
  
  if (allMatch && totalDiscrepancies === 0) {
    console.log(`\n✅ SUCCESS: All hardcoded quizzes match the generated registry!`);
    console.log(`   Migration compatibility verified.`);
    process.exit(0);
  } else {
    console.log(`\n⚠️  WARNING: ${totalDiscrepancies} discrepancies found.`);
    console.log(`   Review the differences above before proceeding with migration.`);
    process.exit(1);
  }
}

// Run comparison
compareQuizzes();
