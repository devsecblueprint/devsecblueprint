import { render, screen } from '@testing-library/react';
import { CurriculumStages } from '@/components/features/curriculum/CurriculumStages';

describe('CurriculumStages', () => {
  it('renders all three learning stages', () => {
    render(<CurriculumStages />);
    
    // Verify all three stage names are present as h2 headings
    expect(screen.getByRole('heading', { level: 2, name: 'Know Before You Go' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'DevSecOps' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Cloud Security Development' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Capstone Projects' })).toBeInTheDocument();
  });

  it('renders "Choose Your Path" indicator for parallel paths', () => {
    render(<CurriculumStages />);
    
    expect(screen.getByText('Choose Your Path')).toBeInTheDocument();
  });

  it('renders stage numbers correctly', () => {
    const { container } = render(<CurriculumStages />);
    
    // Find stage number badges (they have specific gradient classes)
    const badges = container.querySelectorAll('.bg-gradient-to-br.from-primary-400');
    expect(badges.length).toBeGreaterThanOrEqual(3);
    
    // Verify stage 1 exists
    const stage1Badge = Array.from(badges).find(badge => badge.textContent === '1');
    expect(stage1Badge).toBeDefined();
    
    // Verify stage 2 exists (may appear twice for parallel paths)
    const stage2Badges = Array.from(badges).filter(badge => badge.textContent === '2');
    expect(stage2Badges.length).toBeGreaterThanOrEqual(1);
    
    // Verify stage 3 exists
    const stage3Badge = Array.from(badges).find(badge => badge.textContent === '3');
    expect(stage3Badge).toBeDefined();
  });

  it('renders stage descriptions', () => {
    render(<CurriculumStages />);
    
    expect(screen.getByText(/Essential prerequisites and foundational knowledge/)).toBeInTheDocument();
    expect(screen.getByText(/Integrating security into the development lifecycle/)).toBeInTheDocument();
    expect(screen.getByText(/Building secure applications in the cloud/)).toBeInTheDocument();
  });

  it('applies responsive padding and spacing classes', () => {
    const { container } = render(<CurriculumStages />);
    
    const outerDiv = container.firstChild;
    expect(outerDiv).toHaveClass('px-4', 'sm:px-6', 'py-8', 'sm:py-12');
  });

  it('renders StageSection components for each stage', () => {
    const { container } = render(<CurriculumStages />);
    
    // Each StageSection has a button for expansion
    const expandButtons = container.querySelectorAll('button[aria-expanded]');
    expect(expandButtons.length).toBeGreaterThanOrEqual(3);
  });

  it('renders parallel paths in grid layout', () => {
    const { container } = render(<CurriculumStages />);
    
    // Look for the grid container for parallel paths
    const gridContainer = container.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2');
    expect(gridContainer).toBeInTheDocument();
  });
});
