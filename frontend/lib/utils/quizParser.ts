import matter from 'gray-matter';

export interface Option {
  key: string;  // A, B, C, D
  text: string;
}

export interface Question {
  id: string;
  text: string;
  options: Option[];
  // Note: correct answer and explanation NOT included in client-side data
}

export interface QuizData {
  moduleId: string;
  passingScore: number;
  questions: Question[];
}

/**
 * Parse quiz.md file into structured data.
 * 
 * Extracts:
 * - Frontmatter: module_id, passing_score
 * - Questions: id, text, options
 * 
 * Does NOT extract correct answers or explanations (server-side only).
 */
export function parseQuizMarkdown(markdown: string): QuizData {
  // Parse frontmatter
  const { data: frontmatter, content } = matter(markdown);
  
  if (!frontmatter.module_id || !frontmatter.passing_score) {
    throw new Error('Quiz markdown must include module_id and passing_score in frontmatter');
  }

  // Split content by horizontal rules (---) to get question sections
  const sections = content.split(/\n---\n/).filter(s => s.trim());
  
  const questions: Question[] = [];
  
  for (const section of sections) {
    const lines = section.split('\n').filter(line => line.trim());
    
    // Find question heading (## Question N)
    const headingIndex = lines.findIndex(line => line.match(/^##\s+Question\s+\d+/i));
    if (headingIndex === -1) continue;
    
    const headingMatch = lines[headingIndex].match(/^##\s+Question\s+(\d+)/i);
    if (!headingMatch) continue;
    
    const questionId = `q${headingMatch[1]}`;
    
    // Find question text (first non-empty line after heading)
    let questionText = '';
    let optionsStartIndex = -1;
    
    for (let i = headingIndex + 1; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Skip empty lines
      if (!line) continue;
      
      // Check if this is an option line (starts with A., B., C., D. or A), B), etc.)
      if (line.match(/^[A-D][\.\)]\s/)) {
        optionsStartIndex = i;
        break;
      }
      
      // Check if this is a correct answer or explanation (skip these)
      if (line.match(/^\*\*Correct Answer:\*\*/i) || line.match(/^\*\*Explanation:\*\*/i)) {
        break;
      }
      
      // This must be the question text
      if (!questionText) {
        questionText = line;
      }
    }
    
    // Extract options
    const options: Option[] = [];
    if (optionsStartIndex !== -1) {
      for (let i = optionsStartIndex; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Stop at correct answer or explanation
        if (line.match(/^\*\*Correct Answer:\*\*/i) || line.match(/^\*\*Explanation:\*\*/i)) {
          break;
        }
        
        // Parse option format: "A. Option text" or "A) Option text"
        const optionMatch = line.match(/^([A-D])[\.\)]\s*(.+)$/);
        if (optionMatch) {
          options.push({
            key: optionMatch[1],
            text: optionMatch[2].trim()
          });
        }
      }
    }
    
    // Add question if we have all required parts
    if (questionId && questionText && options.length > 0) {
      questions.push({
        id: questionId,
        text: questionText,
        options
      });
    }
  }

  return {
    moduleId: frontmatter.module_id,
    passingScore: frontmatter.passing_score,
    questions
  };
}
