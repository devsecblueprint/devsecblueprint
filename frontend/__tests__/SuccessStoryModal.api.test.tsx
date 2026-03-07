import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SuccessStoryModal } from '@/components/features/SuccessStoryModal';
import { apiClient } from '@/lib/api';

// Mock the apiClient
jest.mock('@/lib/api', () => ({
  apiClient: {
    sendSuccessStory: jest.fn(),
  },
}));

describe('SuccessStoryModal - API Integration (Task 6.3)', () => {
  const mockOnClose = jest.fn();
  const mockSendSuccessStory = apiClient.sendSuccessStory as jest.MockedFunction<typeof apiClient.sendSuccessStory>;

  beforeEach(() => {
    mockOnClose.mockClear();
    mockSendSuccessStory.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const fillValidForm = () => {
    const nameInput = screen.getByLabelText(/^name$/i);
    const emailInput = screen.getByLabelText(/^email$/i);
    const storyInput = screen.getByRole('textbox', { name: /success story/i });

    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(storyInput, { 
      target: { value: 'A'.repeat(50) } 
    });
  };

  describe('Successful submission', () => {
    it('should send POST request with form data', async () => {
      mockSendSuccessStory.mockResolvedValueOnce({
        data: { message: 'Success story sent successfully' },
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockSendSuccessStory).toHaveBeenCalledWith(
          'John Doe',
          'john@example.com',
          'A'.repeat(50),
          false
        );
      });
    });

    it('should display success message on successful submission', async () => {
      mockSendSuccessStory.mockResolvedValueOnce({
        data: { message: 'Success story sent successfully' },
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Thank you for sharing your story!')).toBeInTheDocument();
      });
    });

    it('should auto-close modal after 2 seconds on success', async () => {
      jest.useFakeTimers();
      
      mockSendSuccessStory.mockResolvedValueOnce({
        data: { message: 'Success story sent successfully' },
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Thank you for sharing your story!')).toBeInTheDocument();
      });

      // Fast-forward 2 seconds
      jest.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });

      jest.useRealTimers();
    });

    it('should show loading state during submission', async () => {
      mockSendSuccessStory.mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          data: { message: 'Success story sent successfully' },
        }), 100))
      );

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      // Check loading state
      expect(screen.getByText('Sending...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();

      await waitFor(() => {
        expect(screen.getByText('Thank you for sharing your story!')).toBeInTheDocument();
      });
    });
  });

  describe('Failed submission', () => {
    it('should display error message on failed submission', async () => {
      mockSendSuccessStory.mockResolvedValueOnce({
        error: 'Failed to send email',
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to send your story. Please try again later.')).toBeInTheDocument();
      });
    });

    it('should keep modal open on failed submission', async () => {
      mockSendSuccessStory.mockResolvedValueOnce({
        error: 'Failed to send email',
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to send your story. Please try again later.')).toBeInTheDocument();
      });

      // Modal should still be open
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should handle network errors', async () => {
      mockSendSuccessStory.mockRejectedValueOnce(new Error('Network error'));

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to send your story. Please try again later.')).toBeInTheDocument();
      });
    });
  });

  describe('Form data handling', () => {
    it('should include sharePublicly checkbox value in request', async () => {
      mockSendSuccessStory.mockResolvedValueOnce({
        data: { message: 'Success story sent successfully' },
      });

      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fillValidForm();
      
      const checkbox = screen.getByLabelText(/i give permission to share my story publicly/i);
      fireEvent.click(checkbox);
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockSendSuccessStory).toHaveBeenCalledWith(
          'John Doe',
          'john@example.com',
          'A'.repeat(50),
          true
        );
      });
    });
  });
});
