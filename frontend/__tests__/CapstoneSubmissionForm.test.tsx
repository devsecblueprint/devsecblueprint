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

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    saveProgress: jest.fn(),
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
    
    // Default mock for authenticated user
    (useAuthModule.useAuth as jest.Mock).mockReturnValue({
      username: mockUsername,
      githubUsername: mockGithubUsername,
      isAuthenticated: true,
      isLoading: false,
      userId: 'github|12345',
      avatarUrl: null,
      error: null,
    });
  });

  describe('Form Rendering', () => {
    it('should render the form with all elements', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      expect(screen.getByText('Submit Your Project')).toBeInTheDocument();
      expect(screen.getByLabelText('GitHub Repository URL')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit project/i })).toBeInTheDocument();
    });

    it('should render with correct placeholder text', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL') as HTMLInputElement;
      expect(input.placeholder).toBe(`https://github.com/${mockGithubUsername}/project-name`);
    });

    it('should not render form when user is not authenticated', () => {
      (useAuthModule.useAuth as jest.Mock).mockReturnValue({
        username: null,
        githubUsername: null,
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

    it('should have submit button disabled initially', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Input Validation', () => {
    it('should show error for invalid URL format', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { target: { value: 'not-a-valid-url' } });

      expect(screen.getByText('Invalid GitHub URL format')).toBeInTheDocument();
    });

    it('should show error for username mismatch', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: 'https://github.com/wronguser/project' } 
      });

      expect(screen.getByText(`Repository must be under your GitHub account (${mockGithubUsername})`)).toBeInTheDocument();
    });

    it('should clear error when user starts typing after error', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      
      // Trigger error
      fireEvent.change(input, { target: { value: 'invalid' } });
      expect(screen.getByText('Invalid GitHub URL format')).toBeInTheDocument();

      // Start typing valid URL
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/project` } 
      });
      
      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with https', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with http', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `http://github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should accept valid GitHub URL with www', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://www.github.com/${mockGithubUsername}/my-project` } 
      });

      expect(screen.queryByText('Invalid GitHub URL format')).not.toBeInTheDocument();
    });

    it('should validate username case-insensitively', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername.toUpperCase()}/my-project` } 
      });

      expect(screen.queryByText(/Repository must be under your GitHub account/)).not.toBeInTheDocument();
    });

    it('should disable submit button when there is a validation error', () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { target: { value: 'invalid-url' } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Form Submission', () => {
    it('should submit form with valid URL', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: `  ${validUrl}  ` } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(apiClient.saveProgress).toHaveBeenCalledWith(mockContentId, validUrl);
      });
    });

    it('should show error if submitting empty URL', async () => {
      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { target: { value: '   ' } });

      const form = screen.getByRole('button', { name: /submit project/i }).closest('form');
      fireEvent.submit(form!);

      await waitFor(() => {
        expect(screen.getByText('Please enter a GitHub repository URL')).toBeInTheDocument();
      });
    });

    it('should call onSubmitSuccess callback after successful submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

      render(
        <CapstoneSubmissionForm contentId={mockContentId} />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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
    it('should display success message after submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Project submitted successfully!')).toBeInTheDocument();
      });
    });

    it('should display submitted URL after success', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

    it('should show success icon after submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Project submitted successfully!')).toBeInTheDocument();
      });

      // Check for SVG checkmark icon
      const successIcon = screen.getByText('Project submitted successfully!').previousSibling;
      expect(successIcon).toBeInTheDocument();
    });

    it('should hide form after successful submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByLabelText('GitHub Repository URL')).not.toBeInTheDocument();
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submission failed')).toBeInTheDocument();
      });

      // Form should still be visible
      expect(screen.getByLabelText('GitHub Repository URL')).toBeInTheDocument();
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Check for loading text
      expect(screen.getByText('Submitting...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText('Project submitted successfully!')).toBeInTheDocument();
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL') as HTMLInputElement;
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Input should be disabled during submission
      expect(input).toBeDisabled();

      await waitFor(() => {
        expect(screen.getByText('Project submitted successfully!')).toBeInTheDocument();
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      // Button should be disabled during submission
      const loadingButton = screen.getByRole('button', { name: /submitting/i });
      expect(loadingButton).toBeDisabled();

      await waitFor(() => {
        expect(screen.getByText('Project submitted successfully!')).toBeInTheDocument();
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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL') as HTMLInputElement;
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
    it('should show Update Submission button after successful submission', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });
    });

    it('should show form again when Update Submission is clicked', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      // Form should be visible again
      expect(screen.getByLabelText('GitHub Repository URL')).toBeInTheDocument();
    });

    it('should pre-fill input with submitted URL when updating', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL') as HTMLInputElement;
      const validUrl = `https://github.com/${mockGithubUsername}/my-capstone`;
      fireEvent.change(input, { target: { value: validUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      const updatedInput = screen.getByLabelText('GitHub Repository URL') as HTMLInputElement;
      expect(updatedInput.value).toBe(validUrl);
    });

    it('should change submit button text to "Update Project" when updating', async () => {
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      // Initial submission
      const input = screen.getByLabelText('GitHub Repository URL');
      const firstUrl = `https://github.com/${mockGithubUsername}/first-project`;
      fireEvent.change(input, { target: { value: firstUrl } });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update submission/i })).toBeInTheDocument();
      });

      // Click update
      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      // Change URL
      const updatedInput = screen.getByLabelText('GitHub Repository URL');
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
      const mockResponse = {
        data: { message: 'Progress saved successfully' },
        error: undefined,
      };
      (apiClient.saveProgress as jest.Mock).mockResolvedValue(mockResponse);

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/my-capstone` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

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

      render(
        <CapstoneSubmissionForm
          contentId={mockContentId}
          onSubmitSuccess={mockOnSubmitSuccess}
        />
      );

      // Initial submission
      const input = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(input, { 
        target: { value: `https://github.com/${mockGithubUsername}/first-project` } 
      });

      const submitButton = screen.getByRole('button', { name: /submit project/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmitSuccess).toHaveBeenCalledTimes(1);
      });

      // Update submission
      const updateButton = screen.getByRole('button', { name: /update submission/i });
      fireEvent.click(updateButton);

      const updatedInput = screen.getByLabelText('GitHub Repository URL');
      fireEvent.change(updatedInput, { 
        target: { value: `https://github.com/${mockGithubUsername}/second-project` } 
      });

      const updateProjectButton = screen.getByRole('button', { name: /update project/i });
      fireEvent.click(updateProjectButton);

      await waitFor(() => {
        expect(mockOnSubmitSuccess).toHaveBeenCalledTimes(2);
      });
    });
  });
});
