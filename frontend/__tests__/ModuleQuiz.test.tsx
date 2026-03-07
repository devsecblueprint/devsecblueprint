/**
 * ModuleQuiz Component Tests
 * 
 * Tests for the ModuleQuiz component including:
 * - Quiz rendering
 * - Answer selection
 * - Submission handling
 * - Result display (passed and failed)
 * - Milestone modal display
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ModuleQuiz } from '@/components/ModuleQuiz';
import { QuizData } from '@/lib/utils/quizParser';
import { apiClient } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    post: jest.fn(),
  },
}));

const mockQuizData: QuizData = {
  moduleId: 'test-module',
  passingScore: 70,
  questions: [
    {
      id: 'q1',
      text: 'What is 2 + 2?',
      options: [
        { key: 'A', text: '3' },
        { key: 'B', text: '4' },
        { key: 'C', text: '5' },
        { key: 'D', text: '6' },
      ],
    },
    {
      id: 'q2',
      text: 'What is the capital of France?',
      options: [
        { key: 'A', text: 'London' },
        { key: 'B', text: 'Berlin' },
        { key: 'C', text: 'Paris' },
        { key: 'D', text: 'Madrid' },
      ],
    },
  ],
};

describe('ModuleQuiz - Passed Result Display', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should trigger MilestoneModal when quiz passes', async () => {
    const mockResponse = {
      data: {
        passed: true,
        score: 100,
        passing_score: 70,
        already_completed: false,
        current_streak: 5,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers for all questions
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]); // Select B for q1
    fireEvent.click(optionButtons[6]); // Select C for q2

    // Submit the quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for the results to appear
    await waitFor(() => {
      expect(screen.getByText('Quiz Passed!')).toBeInTheDocument();
    });

    // Verify score is displayed
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should display score in results', async () => {
    const mockResponse = {
      data: {
        passed: true,
        score: 85,
        passing_score: 70,
        already_completed: false,
        current_streak: 3,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers and submit
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]);
    fireEvent.click(optionButtons[6]);
    
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results and verify score
    await waitFor(() => {
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('should call onQuizComplete when modal closes', async () => {
    const mockOnQuizComplete = jest.fn();
    const mockResponse = {
      data: {
        passed: true,
        score: 100,
        passing_score: 70,
        already_completed: false,
        current_streak: 5,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
        onQuizComplete={mockOnQuizComplete}
      />
    );

    // Select answers and submit
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]);
    fireEvent.click(optionButtons[6]);
    
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Quiz Passed!')).toBeInTheDocument();
    });

    // Click Continue Learning button
    const continueButton = screen.getByText('Continue Learning');
    fireEvent.click(continueButton);

    // Verify onQuizComplete was called
    expect(mockOnQuizComplete).toHaveBeenCalledTimes(1);
  });

  it('should show results when quiz fails', async () => {
    const mockResponse = {
      data: {
        passed: false,
        score: 50,
        passing_score: 70,
        already_completed: false,
        current_streak: 0,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: false,
            correct_answer: 'C',
            explanation: 'Paris is the capital of France.',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers and submit
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]);
    fireEvent.click(optionButtons[5]); // Wrong answer
    
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Quiz Not Passed')).toBeInTheDocument();
    });

    // Verify results are shown (not modal)
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('Retry Quiz')).toBeInTheDocument();
  });
});

describe('ModuleQuiz - Quiz Retry Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should reset answer selections when retaking quiz after failed attempt', async () => {
    const mockResponse = {
      data: {
        passed: false,
        score: 50,
        passing_score: 70,
        already_completed: false,
        current_streak: 0,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: false,
            correct_answer: 'C',
            explanation: 'Paris is the capital of France.',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers and submit
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]); // Select B for q1
    fireEvent.click(optionButtons[5]); // Select B for q2 (wrong)

    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Quiz Not Passed')).toBeInTheDocument();
    });

    // Click retry button
    const retryButton = screen.getByText('Retry Quiz');
    fireEvent.click(retryButton);

    // Verify quiz state is reset
    expect(screen.queryByText('Quiz Not Passed')).not.toBeInTheDocument();
    expect(screen.getByText('Submit Quiz')).toBeInTheDocument();
    
    // Submit button should be disabled (no answers selected)
    expect(screen.getByText('Submit Quiz')).toBeDisabled();
  });

  it('should allow immediate retry after viewing failed results', async () => {
    const mockResponse = {
      data: {
        passed: false,
        score: 50,
        passing_score: 70,
        already_completed: false,
        current_streak: 0,
        results: [
          {
            question_id: 'q1',
            correct: false,
            correct_answer: 'B',
            explanation: 'The answer is 4.',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Submit quiz with answers
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[0]); // Wrong answer
    fireEvent.click(optionButtons[6]); // Correct answer

    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Quiz Not Passed')).toBeInTheDocument();
    });

    // Verify retry button is immediately available
    const retryButton = screen.getByText('Retry Quiz');
    expect(retryButton).toBeInTheDocument();
    expect(retryButton).not.toBeDisabled();
  });

  it('should reset answer selections when retaking quiz after passed attempt', async () => {
    const mockResponse = {
      data: {
        passed: true,
        score: 100,
        passing_score: 70,
        already_completed: false,
        current_streak: 5,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers and submit
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]); // Select B for q1
    fireEvent.click(optionButtons[6]); // Select C for q2

    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for modal to appear
    await waitFor(() => {
      expect(screen.getByTestId('milestone-modal')).toBeInTheDocument();
    });

    // Close the modal
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    // Verify quiz state is reset
    await waitFor(() => {
      expect(screen.queryByTestId('milestone-modal')).not.toBeInTheDocument();
    });
    
    // Submit button should be disabled (no answers selected after reset)
    expect(screen.getByText('Submit Quiz')).toBeDisabled();
  });

  it('should clear error messages when retrying quiz', async () => {
    const mockResponse = {
      data: {
        passed: false,
        score: 50,
        passing_score: 70,
        already_completed: false,
        current_streak: 0,
        results: [
          {
            question_id: 'q1',
            correct: false,
            correct_answer: 'B',
            explanation: 'The answer is 4.',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Submit quiz
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[0]);
    fireEvent.click(optionButtons[6]);

    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('Quiz Not Passed')).toBeInTheDocument();
    });

    // Click retry
    const retryButton = screen.getByText('Retry Quiz');
    fireEvent.click(retryButton);

    // Verify error/result messages are cleared
    expect(screen.queryByText('Quiz Not Passed')).not.toBeInTheDocument();
    expect(screen.queryByText(/Your Score:/)).not.toBeInTheDocument();
  });
});

describe('ModuleQuiz - Completed Module Display', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display completed state indicator when module is already completed', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={85}
      />
    );

    // Verify completed indicator is shown
    expect(screen.getByText('Module Completed')).toBeInTheDocument();
    expect(screen.getByText(/Best Score:/)).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  it('should show user\'s previous best score', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={92}
      />
    );

    // Verify best score is displayed
    expect(screen.getByText(/Best Score:/)).toBeInTheDocument();
    expect(screen.getByText(/92%/)).toBeInTheDocument();
  });

  it('should allow user to retake quiz to improve score', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={70}
      />
    );

    // Verify quiz is not locked - questions should be interactive
    const optionButtons = screen.getAllByRole('button');
    
    // Should be able to select answers
    fireEvent.click(optionButtons[1]);
    
    // Submit button should be available (though disabled until all answered)
    expect(screen.getByText('Submit Quiz')).toBeInTheDocument();
  });

  it('should NOT lock or disable quiz after completion', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={100}
      />
    );

    // Verify all option buttons are not disabled
    const optionButtons = screen.getAllByRole('button').filter(btn => 
      btn.textContent?.includes('A.') || 
      btn.textContent?.includes('B.') || 
      btn.textContent?.includes('C.') || 
      btn.textContent?.includes('D.')
    );
    
    optionButtons.forEach(button => {
      expect(button).not.toBeDisabled();
    });
  });

  it('should clearly indicate when this is a retake attempt', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={75}
      />
    );

    // Initially no retake indicator
    expect(screen.queryByText(/Retake Attempt:/)).not.toBeInTheDocument();

    // Select an answer to start retaking
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]);

    // Now retake indicator should appear
    expect(screen.getByText(/Retake Attempt:/)).toBeInTheDocument();
    expect(screen.getByText(/This is a retake to improve your score/)).toBeInTheDocument();
  });

  it('should NOT display attempt counters', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={80}
      />
    );

    // Verify no attempt counter text is present (like "Attempt 1 of 3" or "2 attempts remaining")
    expect(screen.queryByText(/attempt \d+ of \d+/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\d+ attempts? remaining/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/tries/i)).not.toBeInTheDocument();
  });

  it('should NOT display cooldown periods', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={80}
      />
    );

    // Verify no cooldown text is present
    expect(screen.queryByText(/cooldown/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/wait/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/available in/i)).not.toBeInTheDocument();
  });

  it('should show message that user can retake quiz', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={88}
      />
    );

    // Verify retake message is shown
    expect(screen.getByText(/You can retake this quiz to improve your score/)).toBeInTheDocument();
  });

  it('should not show completed indicator when module is not completed', () => {
    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Verify completed indicator is not shown
    expect(screen.queryByText('Module Completed')).not.toBeInTheDocument();
    expect(screen.queryByText(/Best Score:/)).not.toBeInTheDocument();
  });

  it('should hide retake indicator after quiz is submitted', async () => {
    const mockResponse = {
      data: {
        passed: true,
        score: 100,
        passing_score: 70,
        already_completed: true,
        current_streak: 5,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: null,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={true}
        bestScore={75}
      />
    );

    // Select answers to trigger retake indicator
    const optionButtons = screen.getAllByRole('button');
    fireEvent.click(optionButtons[1]);
    fireEvent.click(optionButtons[6]);

    // Verify retake indicator appears
    expect(screen.getByText(/Retake Attempt:/)).toBeInTheDocument();

    // Submit the quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for submission to complete
    await waitFor(() => {
      expect(screen.getByTestId('milestone-modal')).toBeInTheDocument();
    });

    // Retake indicator should be hidden after submission
    expect(screen.queryByText(/Retake Attempt:/)).not.toBeInTheDocument();
  });
});


describe('ModuleQuiz - Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display user-friendly message for 404 quiz not found error', async () => {
    const mockResponse = {
      data: undefined,
      error: 'Quiz not found: test-module',
      statusCode: 404,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers
    const optionB = screen.getByText(/4/);
    const optionC = screen.getByText(/Paris/);
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/This quiz is not available/)).toBeInTheDocument();
      expect(screen.getByText(/Please contact support if this problem persists/)).toBeInTheDocument();
    });

    // Verify milestone modal is not shown
    expect(screen.queryByTestId('milestone-modal')).not.toBeInTheDocument();
  });

  it('should display user-friendly message for 503 registry unavailable error', async () => {
    const mockResponse = {
      data: undefined,
      error: 'Service temporarily unavailable',
      statusCode: 503,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers
    const optionB = screen.getByText(/4/);
    const optionC = screen.getByText(/Paris/);
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/The quiz service is temporarily unavailable/)).toBeInTheDocument();
      expect(screen.getByText(/Please try again in a few moments/)).toBeInTheDocument();
    });

    // Verify milestone modal is not shown
    expect(screen.queryByTestId('milestone-modal')).not.toBeInTheDocument();
  });

  it('should display generic error message for other errors', async () => {
    const mockResponse = {
      data: undefined,
      error: 'Invalid request',
      statusCode: 400,
    };

    (apiClient.post as jest.Mock).mockResolvedValue(mockResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers
    const optionB = screen.getByText(/4/);
    const optionC = screen.getByText(/Paris/);
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Invalid request')).toBeInTheDocument();
    });

    // Verify milestone modal is not shown
    expect(screen.queryByTestId('milestone-modal')).not.toBeInTheDocument();
  });

  it('should handle network errors gracefully', async () => {
    (apiClient.post as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers
    const optionB = screen.getByText(/4/);
    const optionC = screen.getByText(/Paris/);
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Verify milestone modal is not shown
    expect(screen.queryByTestId('milestone-modal')).not.toBeInTheDocument();
  });

  it('should allow retry after error', async () => {
    const mockErrorResponse = {
      data: undefined,
      error: 'Service temporarily unavailable',
      statusCode: 503,
    };

    const mockSuccessResponse = {
      data: {
        passed: true,
        score: 100,
        passing_score: 70,
        already_completed: false,
        current_streak: 1,
        results: [
          {
            question_id: 'q1',
            correct: true,
            correct_answer: 'B',
            explanation: 'Correct!',
          },
          {
            question_id: 'q2',
            correct: true,
            correct_answer: 'C',
            explanation: 'Correct!',
          },
        ],
      },
      error: undefined,
    };

    // First call fails, second succeeds
    (apiClient.post as jest.Mock)
      .mockResolvedValueOnce(mockErrorResponse)
      .mockResolvedValueOnce(mockSuccessResponse);

    render(
      <ModuleQuiz
        quizData={mockQuizData}
        moduleId="test-module"
        isCompleted={false}
      />
    );

    // Select answers
    const optionB = screen.getByText(/4/);
    const optionC = screen.getByText(/Paris/);
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz (first attempt - fails)
    const submitButton = screen.getByText('Submit Quiz');
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/The quiz service is temporarily unavailable/)).toBeInTheDocument();
    });

    // Select answers again
    fireEvent.click(optionB);
    fireEvent.click(optionC);

    // Submit quiz again (second attempt - succeeds)
    const retrySubmitButton = screen.getByText('Submit Quiz');
    fireEvent.click(retrySubmitButton);

    // Wait for milestone modal
    await waitFor(() => {
      expect(screen.getByTestId('milestone-modal')).toBeInTheDocument();
    });

    // Verify error message is cleared
    expect(screen.queryByText(/The quiz service is temporarily unavailable/)).not.toBeInTheDocument();
  });
});
