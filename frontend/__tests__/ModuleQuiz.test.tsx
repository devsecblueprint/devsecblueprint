/**
 * Unit tests for the ModuleQuiz component.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { ModuleQuiz } from '@/components/ModuleQuiz';
import type { QuizData } from '@/lib/utils/quizParser';

jest.mock('@/lib/api', () => ({ apiClient: { post: jest.fn() } }));
jest.mock('@/lib/events', () => ({ triggerBadgeCheck: jest.fn() }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

const quizData: QuizData = {
  passingScore: 70,
  questions: [
    {
      id: 'q1',
      text: 'What is **DevSecOps**?',
      options: [
        { key: 'A', text: 'A tool' },
        { key: 'B', text: 'A culture' },
      ],
    },
    {
      id: 'q2',
      text: 'Shift-left means?',
      options: [
        { key: 'A', text: 'Early security' },
        { key: 'B', text: 'Late security' },
      ],
    },
  ],
} as QuizData;

function answerAll() {
  // Select option B for q1 and A for q2
  fireEvent.click(screen.getByText('A culture'));
  fireEvent.click(screen.getByText('Early security'));
}

beforeEach(() => jest.clearAllMocks());

it('renders questions and the passing score', () => {
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  expect(screen.getByText(/Module Quiz/i)).toBeInTheDocument();
  expect(screen.getByText(/Passing Score: 70%/i)).toBeInTheDocument();
  // bold markdown rendered as <strong>
  expect(screen.getByText('DevSecOps')).toBeInTheDocument();
});

it('disables submit until all questions are answered', () => {
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  const submit = screen.getByRole('button', { name: /submit quiz/i });
  expect(submit).toBeDisabled();
  answerAll();
  expect(submit).toBeEnabled();
});

it('shows a passed result after a successful submit', async () => {
  mockApi.post.mockResolvedValue({
    data: {
      passed: true,
      score: 100,
      passing_score: 70,
      already_completed: false,
      current_streak: 1,
      results: [
        { question_id: 'q1', correct: true, correct_answer: 'B', explanation: '' },
        { question_id: 'q2', correct: true, correct_answer: 'A', explanation: '' },
      ],
    },
    statusCode: 200,
  });
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  answerAll();
  fireEvent.click(screen.getByRole('button', { name: /submit quiz/i }));

  expect(await screen.findByText('Quiz Passed!')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /continue learning/i })).toBeInTheDocument();
  expect(mockApi.post).toHaveBeenCalledWith('/quiz/submit', {
    module_id: 'm1',
    answers: { q1: 'B', q2: 'A' },
  });
});

it('shows a failed result with retry and explanations', async () => {
  mockApi.post.mockResolvedValue({
    data: {
      passed: false,
      score: 50,
      passing_score: 70,
      already_completed: false,
      current_streak: 0,
      results: [
        { question_id: 'q1', correct: false, correct_answer: 'B', explanation: 'B is the culture answer.' },
        { question_id: 'q2', correct: true, correct_answer: 'A', explanation: '' },
      ],
    },
    statusCode: 200,
  });
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  answerAll();
  fireEvent.click(screen.getByRole('button', { name: /submit quiz/i }));

  expect(await screen.findByText('Quiz Not Passed')).toBeInTheDocument();
  expect(screen.getByText('B is the culture answer.')).toBeInTheDocument();

  // Retry resets to the question view
  fireEvent.click(screen.getByRole('button', { name: /retry quiz/i }));
  expect(screen.getByRole('button', { name: /submit quiz/i })).toBeInTheDocument();
});

it('maps a 404 to a friendly not-available message', async () => {
  mockApi.post.mockResolvedValue({ error: 'QUIZ_NOT_FOUND', statusCode: 404 });
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  answerAll();
  fireEvent.click(screen.getByRole('button', { name: /submit quiz/i }));
  expect(await screen.findByText(/not available/i)).toBeInTheDocument();
});

it('maps a 503 to a temporarily-unavailable message', async () => {
  mockApi.post.mockResolvedValue({ error: 'REGISTRY_UNAVAILABLE', statusCode: 503 });
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} />);
  answerAll();
  fireEvent.click(screen.getByRole('button', { name: /submit quiz/i }));
  expect(await screen.findByText(/temporarily unavailable/i)).toBeInTheDocument();
});

it('shows the completed banner with best score', () => {
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted bestScore={88} />);
  expect(screen.getByText('Module Completed')).toBeInTheDocument();
  expect(screen.getByText('88%')).toBeInTheDocument();
});

it('calls onQuizComplete when continuing after a pass', async () => {
  const onQuizComplete = jest.fn();
  mockApi.post.mockResolvedValue({
    data: {
      passed: true, score: 100, passing_score: 70, already_completed: false, current_streak: 1,
      results: [
        { question_id: 'q1', correct: true, correct_answer: 'B', explanation: '' },
        { question_id: 'q2', correct: true, correct_answer: 'A', explanation: '' },
      ],
    },
    statusCode: 200,
  });
  render(<ModuleQuiz quizData={quizData} moduleId="m1" isCompleted={false} onQuizComplete={onQuizComplete} />);
  answerAll();
  fireEvent.click(screen.getByRole('button', { name: /submit quiz/i }));
  fireEvent.click(await screen.findByRole('button', { name: /continue learning/i }));
  expect(onQuizComplete).toHaveBeenCalled();
});
