/**
 * Unit tests for admin UserSearch.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '@/lib/api';
import { UserSearch } from '@/components/admin/UserSearch';

jest.mock('@/lib/api', () => ({ apiClient: { searchUsers: jest.fn() } }));
const mockApi = apiClient as jest.Mocked<typeof apiClient>;

function result(username: string) {
  return {
    user_id: username,
    username,
    github_username: `gh-${username}`,
    gitlab_username: '',
    avatar_url: '',
    registered_at: '2026-01-01T00:00:00Z',
    stats: {
      overall_completion: 75,
      completed_count: 10,
      current_streak: 4,
      quizzes_passed: 5,
    },
  };
}

beforeEach(() => jest.clearAllMocks());

it('shows the initial prompt before searching', () => {
  render(<UserSearch />);
  expect(screen.getByText('Enter a username to search')).toBeInTheDocument();
});

it('validates an empty query', () => {
  render(<UserSearch />);
  fireEvent.click(screen.getByRole('button', { name: /search/i }));
  expect(screen.getByText('Please enter a search query')).toBeInTheDocument();
});

it('renders search results with stats', async () => {
  mockApi.searchUsers.mockResolvedValue({ data: { users: [result('ada')], total_results: 1 }, statusCode: 200 });
  render(<UserSearch />);
  fireEvent.change(screen.getByPlaceholderText(/Search by username/i), { target: { value: 'ada' } });
  fireEvent.click(screen.getByRole('button', { name: /search/i }));

  expect(await screen.findByText('ada')).toBeInTheDocument();
  expect(screen.getByText('Found 1 user')).toBeInTheDocument();
  expect(screen.getByText('75%')).toBeInTheDocument();
});

it('shows a no-results message', async () => {
  mockApi.searchUsers.mockResolvedValue({ data: { users: [], total_results: 0 }, statusCode: 200 });
  render(<UserSearch />);
  fireEvent.change(screen.getByPlaceholderText(/Search by username/i), { target: { value: 'ghost' } });
  fireEvent.click(screen.getByRole('button', { name: /search/i }));
  expect(await screen.findByText(/No users found matching "ghost"/i)).toBeInTheDocument();
});

it('shows an API error', async () => {
  mockApi.searchUsers.mockResolvedValue({ error: 'search failed', statusCode: 500 });
  render(<UserSearch />);
  fireEvent.change(screen.getByPlaceholderText(/Search by username/i), { target: { value: 'ada' } });
  fireEvent.click(screen.getByRole('button', { name: /search/i }));
  expect(await screen.findByText('search failed')).toBeInTheDocument();
});
