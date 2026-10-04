/**
 * Unit tests for ModuleQuizWrapper.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { ModuleQuizWrapper } from '@/components/ModuleQuizWrapper';

jest.mock('@/components/ModuleQuiz', () => ({
  ModuleQuiz: ({ moduleId }: { moduleId: string }) => <div data-testid="module-quiz">{moduleId}</div>,
}));
jest.mock('@/lib/utils/quizParser', () => ({
  parseQuizMarkdown: jest.fn(() => ({ passingScore: 70, questions: [{ id: 'q1', text: 'Q', options: [] }] })),
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => jest.clearAllMocks());

it('renders the quiz when quiz.md loads successfully', async () => {
  mockFetch.mockResolvedValue({ ok: true, status: 200, text: () => Promise.resolve('# Quiz') });
  render(<ModuleQuizWrapper moduleId="m1" quizPath="/quiz.md" />);
  expect(await screen.findByTestId('module-quiz')).toHaveTextContent('m1');
});

it('renders nothing when quiz.md does not exist (404)', async () => {
  mockFetch.mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found' });
  const { container } = render(<ModuleQuizWrapper moduleId="m1" quizPath="/quiz.md" />);
  await waitFor(() => expect(container.querySelector('.animate-spin')).not.toBeInTheDocument());
  expect(screen.queryByTestId('module-quiz')).not.toBeInTheDocument();
});

it('shows an error when the fetch fails with a non-404 status', async () => {
  mockFetch.mockResolvedValue({ ok: false, status: 500, statusText: 'Server Error' });
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<ModuleQuizWrapper moduleId="m1" quizPath="/quiz.md" />);
  expect(await screen.findByText(/Failed to load quiz/i)).toBeInTheDocument();
  spy.mockRestore();
});

it('shows an error when fetch throws', async () => {
  mockFetch.mockRejectedValue(new Error('network down'));
  const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
  render(<ModuleQuizWrapper moduleId="m1" quizPath="/quiz.md" />);
  expect(await screen.findByText('network down')).toBeInTheDocument();
  spy.mockRestore();
});
