/**
 * CapstoneSubmissionForm Component Tests
 * 
 * Tests for the CapstoneSubmissionForm component including:
 * - Form rendering
 * - Input validation
 * - Form submission
 * - Success state
 * - Error state
 * - Loading state
 * - Update functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CapstoneSubmissionForm } from '@/components/CapstoneSubmissionForm';
import { apiClient } from '@/lib/api';
import * as useAuthModule from '@/lib/hooks/useAuth';

// Mock the MarkdownRenderer component
jest.mock('@/components/MarkdownRenderer', () => {
  return function MockMarkdownRenderer({ markdown }: { markdown: string }) {
    return <div data-testid="markdown-renderer">{markdown}</div>;
  };
});

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    saveProgress: jest.fn(),
    getCapstoneSubmission: jest.fn().mockResolvedValue({ data: null, error: undefined }),
    getCapstoneReview: jest.fn().mockResolvedValue({ data: { review: null }, error: undefined }),
  },
}));

// Mock the useAuth hook
jest.mock('@/lib/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

describe('CapstoneSubmissionForm', () => {
  const mockUsername = 'testuser';
  const mockGithubUsername = 'testuser';
  const mockContentId = 'devsecops-capstone';
  const mockOnSubmitSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset default mock implementations
    (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({ data: null, error: undefined });
    (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({ data: { review: null }, error: undefined });

    // Default mock for authenticated user
    (useAuthModule.useAuth as jest.Mock).mockReturnValue({
      username: mockUsername,
      githubUsername: mockGithubUsername,
      providerUsername: mockGithubUsername,
      provider: 'github',
      isAuthenticated: true,
      isLoading: false,
      userId: 'github|12345',
      avatarUrl: null,
      error: null,
    });
  });

  // Helper to render and wait for loading to complete
  async function renderAndWaitForForm(props: { contentId: string; onSubmitSuccess?: () => void }) {
    const result = render(<CapstoneSubmissionForm {...props} />);
    await waitFor(() => {
      expect(screen.queryByText('Submit Your Project')).toBeInTheDocument();
    });
    return result;
  }

  describe('Form Rendering', () => {
    it('should render the form with all elements', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      expect(screen.getByText('Submit Your Project')).toBeInTheDocument();
      expect(screen.getByLabelText('Repository URL')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit project/i })).toBeInTheDocument();
    });

    it('should render with correct placeholder text', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL') as HTMLInputElement;
      expect(input.placeholder).toBe(`https://github.com/${mockGithubUsername}/project-name`);
    });

    it('should not render form when user is not authenticated', () => {
      (useAuthModule.useAuth as jest.Mock).mockReturnValue({
        username: null,
        githubUsername: null,
        providerUsername: null,
        provider: null,
        isAuthenticated: false,
        isLoading: false,
        userId: null,
        avatarUrl: null,
        error: null,
      });

      const { container } = render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should have submit button enabled initially', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Input Validation', () => {
    it('should show error for invalid URL format', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { target: { value: 'not-a-valid-url' } });

      expect(screen.getByText('Invalid GitHub URL format')).toBeInTheDocument();
    });

    it('should show error for username mismatch', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: 'https://github.com/wronguser/project' } 
      });

      expect(screen.getByText(`Repository must be under your GitHub account (${mockGithubUsername})`)).toBeInTheDocument();
    });

    it('should clear error when user starts typing after error', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      
      // Trigger error
      fireEvent.change(input, { target: { value: 'invalid' } });
      expect(screen.getByText('Invalid GitHub URL format')).toBeInTheDocument();

      // Start typing valid URL
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/project` } 
      });
      
      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with https', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with http', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `http://github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with www', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://www.github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should validate username case-insensitively', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername.toUpperCase()}/my-project` } 
      });

      expect(screen.queryByText(/Repository must be under your GitHub account/)).not.toBeInTheDocument();
    });

    it('should show validation error for invalid URL', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { target: { value: 'invalid-url' } });

      expect(screen.getByText('Invalid GitHub URL format')).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid URL', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.saveProgress).toHaveBeenCalledWith(mockContentId, validUrl);
      });
    });

    it('should trim whitespace from URL before submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: `  ${validUrl}  ` } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.saveProgress).toHaveBeenCalledWith(mockContentId, validUrl);
      });
    });

    it('should show error if submitting empty URL', async () => {
      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { target: { value: '   ' } });

      const form = screen.getByRole('button', { name: /submit project/i }).closest('form');
      fireEvent.submit(form!);

      await waitFor(() => {
        expect(screen.getByText('Please enter a repository URL')).toBeInTheDocument();
      });
    });

    it('should call onSubmitSuccess callback after successful submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmitSuccess).toHaveBeenCalledTimes(1);
      });
    });

    it('should not call onSubmitSuccess if callback is not provided', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({ contentId: mockContentId });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.saveProgress).toHaveBeenCalled();
      });

      // Should not throw error
      expect(mockOnSubmitSuccess).not.toHaveBeenCalled();
    });
  });

  describe('Success State', () => {
    it('should display pending review message after submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Project submitted — under review/)).toBeInTheDocument();
      });
    });

    it('should display submitted URL after success', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const link = screen.getByRole('link', { name: validUrl });
        expect(link).toHaveAttribute('href', validUrl);
        expect(link).toHaveAttribute('target', '_blank');
      });
    });

    it('should show review timeline message after submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Your project will be reviewed within 7-10 business days.')).toBeInTheDocument();
      });
    });

    it('should hide form after successful submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByLabelText('Repository URL')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('should display API error message', async () => {
      const mockResponse = {
        data: undefined,
        error: 'Repository validation failed',
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Repository validation failed')).toBeInTheDocument();
      });
    });

    it('should display generic error for unexpected errors', async () => {
      (apiClient.saveProgress as jest.Mock).mockRejectedValue(new Error('Network error'));

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred. Please try again.')).toBeInTheDocument();
      });
    });

    it('should not call onSubmitSuccess when submission fails', async () => {
      const mockResponse = {
        data: undefined,
        error: 'Submission failed',
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submission failed')).toBeInTheDocument();
      });

      expect(mockOnSubmitSuccess).not.toHaveBeenCalled();
    });

    it('should keep form visible after error', async () => {
      const mockResponse = {
        data: undefined,
        error: 'Submission failed',
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submission failed')).toBeInTheDocument();
      });

      // Form should still be visible
      expect(screen.getByLabelText('Repository URL')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading text on submit button during submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      
      // Delay the response to test loading state
      (apiClient.saveProgress as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
      );

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Check for loading text
      expect(screen.getByText('Submitting...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText(/Project submitted — under review/)).toBeInTheDocument();
      });
    });

    it('should disable input during submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      
      (apiClient.saveProgress as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
      );

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL') as HTMLInputElement;
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Input should be disabled during submission
      expect(input).toBeDisabled();

      await waitFor(() => {
        expect(screen.getByText(/Project submitted — under review/)).toBeInTheDocument();
      });
    });

    it('should disable submit button during submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      
      (apiClient.saveProgress as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
      );

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Button should be disabled during submission
      const loadingButton = screen.getByRole('button', { name: /submitting/i });
      expect(loadingButton).toBeDisabled();

      await waitFor(() => {
        expect(screen.getByText(/Project submitted — under review/)).toBeInTheDocument();
      });
    });

    it('should re-enable form after submission completes', async () => {
      const mockResponse = {
        data: undefined,
        error: 'Submission failed',
      };
      
      (apiClient.saveProgress as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockResponse), 100))
      );

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL') as HTMLInputElement;
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submission failed')).toBeInTheDocument();
      });

      // Form should be re-enabled after error
      expect(input).not.toBeDisabled();
    });
  });

  describe('Update Functionality', () => {
    it('should show Update Submission button for legacy submissions (no status)', async () => {
      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });
    });

    it('should show form again when Update Submission is clicked', async () => {
      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      // Form should be visible again
      expect(screen.getByLabelText('Repository URL')).toBeInTheDocument();
    });

    it('should pre-fill input with submitted URL when updating', async () => {
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      
      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: validUrl },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      const updatedInput = screen.getByLabelText('Repository URL') as HTMLInputElement;
      expect(updatedInput.value).toBe(validUrl);
    });

    it('should change submit button text to "Update Project" when updating', async () => {
      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      expect(screen.getByRole('button', { name: /update project/i })).toBeInTheDocument();
    });

    it('should allow submitting updated URL', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/first-project` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      // Click update
      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      // Change URL
      const updatedInput = screen.getByLabelText('Repository URL');
      const secondUrl = `https://github.com/${mockGithubUsername}/second-project`;
      fireEvent.change(updatedInput, { target: { value: secondUrl } });

      // Submit update
      const updateProjectButton = screen.getByRole('button', { name: /update project/i });
      fireEvent.click(updateProjectButton);

      await waitFor(() => {
        expect(apiClient.saveProgress).toHaveBeenCalledWith(mockContentId, secondUrl);
      });
    });

    it('should clear errors when clicking Update Submission', async () => {
      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      // No errors should be visible
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });

    it('should call onSubmitSuccess again after updating', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      // Mock a legacy submission (no status field)
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/first-project` },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      // Update submission
      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      const updatedInput = screen.getByLabelText('Repository URL');
      fireEvent.change(updatedInput, { 
        target: { value: `https://github.com/${mockGithubUsername}/second-project` } 
      });

      const updateProjectButton = screen.getByRole('button', { name: /update project/i });
      fireEvent.click(updateProjectButton);

      await waitFor(() => {
        expect(mockOnSubmitSuccess).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Pending Review State', () => {
    it('should display pending review state when submission has pending_review status', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'pending_review' },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Project submitted — under review/)).toBeInTheDocument();
      });
    });

    it('should display the submitted URL as read-only in pending_review state', async () => {
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: validUrl, status: 'pending_review' },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        const link = screen.getByRole('link', { name: validUrl });
        expect(link).toHaveAttribute('href', validUrl);
      });

      // Should not have an input field or resubmit button
      expect(screen.queryByLabelText('Repository URL')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /resubmit/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /update/i })).not.toBeInTheDocument();
    });

    it('should display review timeline message in pending_review state', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'pending_review' },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Your project will be reviewed within 7-10 business days.')).toBeInTheDocument();
      });
    });
  });

  describe('Reviewed State', () => {
    const mockReview: import('@/lib/types').ReviewData = {
      feedback: '## Great work!\n\nYour implementation is solid.',
      reviewed_by: 'admin_user',
      reviewed_at: '2025-03-15T10:30:00Z',
      updated_at: '2025-03-15T10:30:00Z',
    };

    it('should display reviewed state with feedback when submission has reviewed status', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'reviewed' },
        error: undefined,
      });
      (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({
        data: { review: mockReview },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Review Complete')).toBeInTheDocument();
      });

      // Should render feedback via MarkdownRenderer
      expect(screen.getByTestId('markdown-renderer')).toBeInTheDocument();
      expect(screen.getByTestId('markdown-renderer').textContent).toContain('Great work!');
    });

    it('should display reviewer and timestamp in reviewed state', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'reviewed' },
        error: undefined,
      });
      (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({
        data: { review: mockReview },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Reviewed by admin_user/)).toBeInTheDocument();
      });
    });

    it('should show Download Feedback button in reviewed state', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'reviewed' },
        error: undefined,
      });
      (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({
        data: { review: mockReview },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /download feedback/i })).toBeInTheDocument();
      });
    });

    it('should show Resubmit button in reviewed state', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'reviewed' },
        error: undefined,
      });
      (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({
        data: { review: mockReview },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /resubmit/i })).toBeInTheDocument();
      });
    });

    it('should show resubmission form when Resubmit is clicked', async () => {
      (apiClient.getCapstoneSubmission as jest.Mock).mockResolvedValue({
        data: { repo_url: `https://github.com/${mockGithubUsername}/my-capstone`, status: 'reviewed' },
        error: undefined,
      });
      (apiClient.getCapstoneReview as jest.Mock).mockResolvedValue({
        data: { review: mockReview },
        error: undefined,
      });

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /resubmit/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /resubmit/i }));

      expect(screen.getByLabelText('Repository URL')).toBeInTheDocument();
      expect(screen.getByText('Resubmit Your Project')).toBeInTheDocument();
    });
  });

  describe('409 Conflict Handling', () => {
    it('should display locked message when receiving 409 on submission', async () => {
      (apiClient.saveProgress as jest.Mock).mockResolvedValue({
        data: undefined,
        error: 'Submission is locked for review',
        statusCode: 409,
      });

      await renderAndWaitForForm({
        contentId: mockContentId,
        onSubmitSuccess: mockOnSubmitSuccess,
      });

      const input = screen.getByLabelText('Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Your submission is currently under review and cannot be updated')).toBeInTheDocument();
      });
    });
  });
});
