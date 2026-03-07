import { parseQuizMarkdown } from '../lib/utils/quizParser';

describe('parseQuizMarkdown', () => {
  const validQuizMarkdown = `---
module_id: secure-sdlc
passing_score: 70
---

## Question 1

What is the primary goal of Secure SDLC?

A. Reduce development costs
B. Embed security throughout the development lifecycle
C. Speed up deployment
D. Eliminate all security vulnerabilities

**Correct Answer:** B

**Explanation:** SSDLC embeds security practices early and throughout the development lifecycle to identify and mitigate vulnerabilities before production.

---

## Question 2

When should threat modeling occur?

A. After deployment
B. During testing only
C. During design and architecture phases
D. Only when vulnerabilities are found

**Correct Answer:** C

**Explanation:** Threat modeling should occur during design and architecture phases to identify potential security issues before implementation begins.

---
`;

  it('should parse valid quiz markdown with multiple questions', () => {
    const result = parseQuizMarkdown(validQuizMarkdown);
    
    expect(result.moduleId).toBe('secure-sdlc');
    expect(result.passingScore).toBe(70);
    expect(result.questions).toHaveLength(2);
    
    // Check first question
    expect(result.questions[0].id).toBe('q1');
    expect(result.questions[0].text).toBe('What is the primary goal of Secure SDLC?');
    expect(result.questions[0].options).toHaveLength(4);
    expect(result.questions[0].options[0]).toEqual({
      key: 'A',
      text: 'Reduce development costs'
    });
    expect(result.questions[0].options[1]).toEqual({
      key: 'B',
      text: 'Embed security throughout the development lifecycle'
    });
    
    // Check second question
    expect(result.questions[1].id).toBe('q2');
    expect(result.questions[1].text).toBe('When should threat modeling occur?');
    expect(result.questions[1].options).toHaveLength(4);
  });

  it('should throw error when frontmatter is missing module_id', () => {
    const invalidMarkdown = `---
passing_score: 70
---

## Question 1

Test question?

A. Option A
B. Option B
`;
    
    expect(() => parseQuizMarkdown(invalidMarkdown)).toThrow(
      'Quiz markdown must include module_id and passing_score in frontmatter'
    );
  });

  it('should throw error when frontmatter is missing passing_score', () => {
    const invalidMarkdown = `---
module_id: test-module
---

## Question 1

Test question?

A. Option A
B. Option B
`;
    
    expect(() => parseQuizMarkdown(invalidMarkdown)).toThrow(
      'Quiz markdown must include module_id and passing_score in frontmatter'
    );
  });

  it('should not include correct answers in parsed output', () => {
    const result = parseQuizMarkdown(validQuizMarkdown);
    
    // Verify that the parsed questions don't have correct answer or explanation fields
    result.questions.forEach(question => {
      expect(question).not.toHaveProperty('correctAnswer');
      expect(question).not.toHaveProperty('explanation');
      expect(question).toHaveProperty('id');
      expect(question).toHaveProperty('text');
      expect(question).toHaveProperty('options');
    });
  });

  it('should handle quiz with single question', () => {
    const singleQuestionMarkdown = `---
module_id: test-module
passing_score: 80
---

## Question 1

What is a test question?

A. First option
B. Second option
C. Third option
D. Fourth option

**Correct Answer:** A

**Explanation:** This is just a test.

---
`;
    
    const result = parseQuizMarkdown(singleQuestionMarkdown);
    
    expect(result.moduleId).toBe('test-module');
    expect(result.passingScore).toBe(80);
    expect(result.questions).toHaveLength(1);
    expect(result.questions[0].id).toBe('q1');
    expect(result.questions[0].options).toHaveLength(4);
  });
});
