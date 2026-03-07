/**
 * ModuleQuizWrapper Component Tests
 * 
 * Tests for the ModuleQuizWrapper component including:
 * - Quiz.md file existence checking
 * - Quiz parsing and rendering
 * - Module completion state handling
 * - Conditional rendering (no quiz UI when quiz.md doesn't exist)
 */

import { render, screen, waitFor } from '@testing-library/react';
import { ModuleQuizWrapper } from '@/components/ModuleQuizWrapper';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    getProgress: jest.fn(),
  },
}));

// Mock the ModuleQuiz component
jest.mock('@/components/ModuleQuiz', () => ({
  ModuleQuiz: ({ quizData, moduleId, isCompleted, bestScore }: any) => (
    <div data-testid="module-quiz">
      <div>Module ID: {moduleId}</div>
      <div>Quiz ID: {quizData.moduleId}</div>
      <div>Passing Score: {quizData.passingScore}%</div>
      <div>Questions: {quizData.questions.length}</div>
      <div>Completed: {isCompleted ? 'Yes' : 'No'}</div>
      {bestScore !== undefined && <div>Best Score: {bestScore}%</div>}
    </div>
  ),
}));

// Mock fetch
global.fetch = jest.fn();

describe('ModuleQuizWrapper', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render quiz when quiz.md exists', async () => {
    // Mock successful quiz.md fetch
    const mockQuizMarkdown = `---
module_id: test-module
passing_score: 70
---

## Question 1

What is the test question?

A. Option A
B. Option B
C. Option C
D. Option D

**Correct Answer:** B

**Explanation:** This is the explanation.

---
`;

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => mockQuizMarkdown,
    });

    // Mock progress API response
    (apiClient.getProgress as jest.Mock).mockResolvedValueOnce({
      data: {
        progress: [],
      },
    });

    render(
      <ModuleQuizWrapper
        moduleId="test-module"
        quizPath="/quizzes/test-quiz.md"
      />
    );

    // Should show loading initially
    expect(screen.getByText('Loading quiz...')).toBeInTheDocument();

    // Wait for quiz to load
    await waitFor(() => {
      expect(screen.getByTestId('module-quiz')).toBeInTheDocument();
    });

    // Verify quiz data is passed correctly
    expect(screen.getByText('Module ID: test-module')).toBeInTheDocument();
    expect(screen.getByText('Quiz ID: test-module')).toBeInTheDocument();
    expect(screen.getByText('Passing Score: 70%')).toBeInTheDocument();
    expect(screen.getByText('Questions: 1')).toBeInTheDocument();
    expect(screen.getByText('Completed: No')).toBeInTheDocument();
  });

  it('should not render quiz UI when quiz.md does not exist (404)', async () => {
    // Mock 404 response for quiz.md
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    render(
      <ModuleQuizWrapper
        moduleId="test-module"
        quizPath="/quizzes/nonexistent-quiz.md"
      />
    );

    // Should show loading initially
    expect(screen.getByText('Loading quiz...')).toBeInTheDocument();

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading quiz...')).not.toBeInTheDocument();
    });

    // Should not render quiz UI
    expect(screen.queryByTestId('module-quiz')).not.toBeInTheDocument();
  });

  it('should display completed state when module is completed', async () => {
    // Mock successful quiz.md fetch
    const mockQuizMarkdown = `---
module_id: completed-module
passing_score: 70
---

## Question 1

Test question?

A. Option A
B. Option B

**Correct Answer:** A

**Explanation:** Explanation text.

---
`;

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => mockQuizMarkdown,
    });

    // Mock progress API response with completed module
    (apiClient.getProgress as jest.Mock).mockResolvedValueOnce({
      data: {
        progress: [
          {
            content_id: 'completed-module',
            completed: true,
          },
        ],
      },
    });

    render(
      <ModuleQuizWrapper
        moduleId="completed-module"
        quizPath="/quizzes/completed-quiz.md"
      />
    );

    // Wait for quiz to load
    await waitFor(() => {
      expect(screen.getByTestId('module-quiz')).toBeInTheDocument();
    });

    // Verify completed state is passed
    expect(screen.getByText('Completed: Yes')).toBeInTheDocument();
  });

  it('should display error message when quiz.md fetch fails (non-404)', async () => {
    // Mock server error response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    render(
      <ModuleQuizWrapper
        moduleId="test-module"
        quizPath="/quizzes/error-quiz.md"
      />
    );

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText(/Failed to load quiz/i)).toBeInTheDocument();
    });

    // Should not render quiz UI
    expect(screen.queryByTestId('module-quiz')).not.toBeInTheDocument();
  });

  it('should handle quiz parsing errors gracefully', async () => {
    // Mock successful fetch but invalid markdown
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => 'Invalid markdown without frontmatter',
    });

    render(
      <ModuleQuizWrapper
        moduleId="test-module"
        quizPath="/quizzes/invalid-quiz.md"
      />
    );

    // Wait for error to display
    await waitFor(() => {
      expect(screen.getByText(/module_id and passing_score/i)).toBeInTheDocument();
    });

    // Should not render quiz UI
    expect(screen.queryByTestId('module-quiz')).not.toBeInTheDocument();
  });
});
