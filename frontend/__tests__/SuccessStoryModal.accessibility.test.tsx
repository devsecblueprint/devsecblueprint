import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SuccessStoryModal } from '@/components/features/SuccessStoryModal';

describe('SuccessStoryModal - Accessibility Features (Task 6.4)', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  describe('Focus management', () => {
    it('should focus first input when modal opens', async () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      
      await waitFor(() => {
        expect(nameInput).toHaveFocus();
      }, { timeout: 200 });
    });

    it('should restore focus to trigger element when modal closes', async () => {
      // Create a button that will open the modal
      const triggerButton = document.createElement('button');
      triggerButton.textContent = 'Open Modal';
      document.body.appendChild(triggerButton);
      triggerButton.focus();
      
      expect(triggerButton).toHaveFocus();
      
      // Render modal as open
      const { rerender } = render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      // Wait for focus to move to first input
      await waitFor(() => {
        const nameInput = screen.getByLabelText(/^name$/i);
        expect(nameInput).toHaveFocus();
      }, { timeout: 200 });
      
      // Close modal
      rerender(<SuccessStoryModal isOpen={false} onClose={mockOnClose} />);
      
      // Focus should be restored to trigger button
      await waitFor(() => {
        expect(triggerButton).toHaveFocus();
      });
      
      // Cleanup
      document.body.removeChild(triggerButton);
    });
  });

  describe('Keyboard interactions', () => {
    it('should close modal when Escape key is pressed', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fireEvent.keyDown(document, { key: 'Escape' });
      
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should not close modal when other keys are pressed', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fireEvent.keyDown(document, { key: 'Enter' });
      fireEvent.keyDown(document, { key: 'Space' });
      fireEvent.keyDown(document, { key: 'Tab' });
      
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Focus trap', () => {
    it('should have all focusable elements within modal', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      // Verify all expected focusable elements are present
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyTextarea = screen.getByRole('textbox', { name: /success story/i });
      const checkbox = screen.getByLabelText(/i give permission/i);
      const submitButton = screen.getByRole('button', { name: /send story/i });
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      const closeButton = screen.getByRole('button', { name: /close modal/i });
      
      expect(nameInput).toBeInTheDocument();
      expect(emailInput).toBeInTheDocument();
      expect(storyTextarea).toBeInTheDocument();
      expect(checkbox).toBeInTheDocument();
      expect(submitButton).toBeInTheDocument();
      expect(cancelButton).toBeInTheDocument();
      expect(closeButton).toBeInTheDocument();
    });

    it('should not close modal when Tab key is pressed', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fireEvent.keyDown(document, { key: 'Tab' });
      
      // Modal should still be open (onClose not called)
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should not close modal when Shift+Tab is pressed', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
      
      // Modal should still be open (onClose not called)
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Click outside to close', () => {
    it('should close modal when clicking on backdrop', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      // Find the backdrop (the outer div with role="dialog")
      const backdrop = screen.getByRole('dialog');
      
      // Click on the backdrop
      fireEvent.click(backdrop);
      
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should not close modal when clicking inside modal content', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      
      // Click inside the modal
      fireEvent.click(nameInput);
      
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('ARIA attributes', () => {
    it('should have role="dialog" on modal container', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should have aria-modal="true" on modal container', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby pointing to modal title', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const dialog = screen.getByRole('dialog');
      const title = screen.getByText('Share Your Success Story');
      
      expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
      expect(title).toHaveAttribute('id', 'modal-title');
    });

    it('should have aria-label on close button', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toHaveAttribute('aria-label', 'Close modal');
    });
  });

  describe('Body scroll prevention', () => {
    it('should prevent body scroll when modal is open', () => {
      const { rerender } = render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      expect(document.body.style.overflow).toBe('hidden');
      
      // Close modal
      rerender(<SuccessStoryModal isOpen={false} onClose={mockOnClose} />);
      
      expect(document.body.style.overflow).toBe('unset');
    });
  });

  describe('Modal visibility', () => {
    it('should not render when isOpen is false', () => {
      render(<SuccessStoryModal isOpen={false} onClose={mockOnClose} />);
      
      const dialog = screen.queryByRole('dialog');
      expect(dialog).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });
});
