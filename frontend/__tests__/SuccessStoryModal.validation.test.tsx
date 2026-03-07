import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { SuccessStoryModal } from '@/components/features/SuccessStoryModal';

describe('SuccessStoryModal - Form Validation (Task 6.2)', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  describe('Submit button disabled state', () => {
    it('should disable submit button when name is empty', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable submit button when email is invalid', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      // Fill valid name and story, but invalid email
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable submit button when email is missing @ symbol', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'invalidemail.com' } });
      fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable submit button when story is empty', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should disable submit button when story is less than 50 characters', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(storyInput, { target: { value: 'Short story' } }); // Less than 50 chars
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should enable submit button when all validation passes', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      // Fill all fields with valid data
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(storyInput, { 
        target: { value: 'This is a valid success story that is definitely longer than fifty characters required for validation.' } 
      });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Email validation regex', () => {
    it('should accept valid email formats', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      const validEmails = [
        'user@example.com',
        'test.user@example.com',
        'user+tag@example.co.uk',
        'user123@test-domain.com'
      ];
      
      validEmails.forEach(email => {
        fireEvent.change(nameInput, { target: { value: 'John Doe' } });
        fireEvent.change(emailInput, { target: { value: email } });
        fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
        
        const submitButton = screen.getByRole('button', { name: /send story/i });
        expect(submitButton).not.toBeDisabled();
      });
    });

    it('should reject invalid email formats', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      const invalidEmails = [
        'invalid',
        'invalid@',
        '@example.com',
        'invalid@.com',
        'invalid @example.com',
        'invalid@example'
      ];
      
      invalidEmails.forEach(email => {
        fireEvent.change(nameInput, { target: { value: 'John Doe' } });
        fireEvent.change(emailInput, { target: { value: email } });
        fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
        
        const submitButton = screen.getByRole('button', { name: /send story/i });
        expect(submitButton).toBeDisabled();
      });
    });
  });

  describe('Name validation', () => {
    it('should trim whitespace from name', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      // Name with only whitespace should be invalid
      fireEvent.change(nameInput, { target: { value: '   ' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Story validation', () => {
    it('should trim whitespace from story', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      // Story with only whitespace should be invalid
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(storyInput, { target: { value: '   ' } });
      
      const submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
    });

    it('should require exactly 50 characters minimum', () => {
      render(<SuccessStoryModal isOpen={true} onClose={mockOnClose} />);
      
      const nameInput = screen.getByLabelText(/^name$/i);
      const emailInput = screen.getByLabelText(/^email$/i);
      const storyInput = screen.getByRole('textbox', { name: /success story/i });
      
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      
      // 49 characters - should be invalid
      fireEvent.change(storyInput, { target: { value: 'A'.repeat(49) } });
      let submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).toBeDisabled();
      
      // 50 characters - should be valid
      fireEvent.change(storyInput, { target: { value: 'A'.repeat(50) } });
      submitButton = screen.getByRole('button', { name: /send story/i });
      expect(submitButton).not.toBeDisabled();
    });
  });
});
