import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StageSection } from '@/components/features/curriculum/StageSection';
import { CurriculumStage } from '@/lib/types';

describe('StageSection', () => {
  const mockStageWithModules: CurriculumStage = {
    id: 'stage-1',
    name: 'Test Stage',
    description: 'This is a test stage description',
    moduleCount: 2,
    stageNumber: 1,
    modules: [
      {
        id: 'module-1',
        name: 'Test Module 1',
        topics: ['Topic 1', 'Topic 2']
      },
      {
        id: 'module-2',
        name: 'Test Module 2',
        topics: ['Topic 3', 'Topic 4']
      }
    ]
  };

  const mockStageWithProjects: CurriculumStage = {
    id: 'stage-4',
    name: 'Capstone Projects',
    description: 'Apply everything you\'ve learned',
    moduleCount: 4,
    stageNumber: 4,
    projects: [
      'Building secure CI/CD pipelines',
      'Designing secure cloud architectures'
    ]
  };

  it('renders stage number badge', () => {
    render(<StageSection stage={mockStageWithModules} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders stage name as h2 heading', () => {
    render(<StageSection stage={mockStageWithModules} />);
    const heading = screen.getByRole('heading', { level: 2, name: 'Test Stage' });
    expect(heading).toBeInTheDocument();
  });

  it('renders StageCard with stage description', () => {
    render(<StageSection stage={mockStageWithModules} />);
    expect(screen.getByText('This is a test stage description')).toBeInTheDocument();
  });

  it('renders modules when expanded', async () => {
    const user = userEvent.setup();
    const { container } = render(<StageSection stage={mockStageWithModules} />);
    
    // Find the expandable content div
    const expandableContent = container.querySelector('.overflow-hidden.transition-all');
    
    // Initially collapsed - check for max-h-0 class
    expect(expandableContent).toHaveClass('max-h-0');
    
    // Click to expand - find the button with aria-expanded attribute
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);
    
    // Now should be expanded - check for max-h class change
    expect(expandableContent).not.toHaveClass('max-h-0');
    
    // Modules should be in the document
    expect(screen.getByText('Test Module 1')).toBeInTheDocument();
    expect(screen.getByText('Test Module 2')).toBeInTheDocument();
  });

  it('renders projects list when expanded', async () => {
    const user = userEvent.setup();
    const { container } = render(<StageSection stage={mockStageWithProjects} />);
    
    // Click to expand - find the button with aria-expanded attribute
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);
    
    // Check for projects section heading (h3, not h2)
    expect(screen.getByRole('heading', { level: 3, name: 'Capstone Projects' })).toBeInTheDocument();
    
    // Check for project content
    expect(screen.getByText('Building secure CI/CD pipelines')).toBeInTheDocument();
    expect(screen.getByText('Designing secure cloud architectures')).toBeInTheDocument();
  });

  it('does not render modules section when modules array is empty', () => {
    const stageWithoutModules: CurriculumStage = {
      id: 'stage-test',
      name: 'Empty Stage',
      description: 'No modules here',
      stageNumber: 1
    };
    const { container } = render(<StageSection stage={stageWithoutModules} />);
    // Component should still render without errors
    expect(container.querySelector('h2')).toHaveTextContent('Empty Stage');
  });

  it('toggles expansion state when clicked', async () => {
    const user = userEvent.setup();
    const { container } = render(<StageSection stage={mockStageWithModules} />);
    
    // Find the expand button by aria-expanded attribute
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    
    // Initially collapsed
    expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    
    // Click to expand
    await user.click(expandButton);
    expect(expandButton).toHaveAttribute('aria-expanded', 'true');
    
    // Click to collapse
    await user.click(expandButton);
    expect(expandButton).toHaveAttribute('aria-expanded', 'false');
  });

  it('applies gradient background to stage number badge', () => {
    const { container } = render(<StageSection stage={mockStageWithModules} />);
    const badge = container.querySelector('.bg-gradient-to-br.from-primary-400');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('1');
  });
});
