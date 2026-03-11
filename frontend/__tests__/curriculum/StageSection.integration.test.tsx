import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StageSection } from '@/components/features/curriculum/StageSection';
import { CURRICULUM_STAGES } from '@/lib/curriculum-data';

describe('StageSection Integration with Real Data', () => {
  it('renders "Know Before You Go" stage correctly', async () => {
    const user = userEvent.setup();
    const stage = CURRICULUM_STAGES[0];
    const { container } = render(<StageSection stage={stage} />);

    // Verify stage name
    expect(screen.getByRole('heading', { level: 2, name: 'Know Before You Go' })).toBeInTheDocument();

    // Verify stage description
    expect(screen.getByText(/Essential prerequisites and foundational knowledge/)).toBeInTheDocument();

    // Expand to see modules - find the expand button
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);

    // Verify modules are rendered
    expect(screen.getByText('Prerequisites')).toBeVisible();
    expect(screen.getByText('Soft Skills')).toBeVisible();

    // Verify some topics
    expect(screen.getByText('Git and version control')).toBeVisible();
    expect(screen.getByText('Communication with engineering teams')).toBeVisible();
  });

  it('renders "DevSecOps" stage with all 6 modules', async () => {
    const user = userEvent.setup();
    const stage = CURRICULUM_STAGES[1];
    const { container } = render(<StageSection stage={stage} />);

    expect(screen.getByRole('heading', { level: 2, name: 'DevSecOps' })).toBeInTheDocument();

    // Expand to see modules
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);

    // Verify all 6 modules (using heading role for module names)
    expect(screen.getByRole('heading', { level: 3, name: 'What is the Secure SDLC?' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'What is Application Security?' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Secure Coding Overview' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'DevSecOps Fundamentals' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Threat Modeling Fundamentals' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Container Security Overview' })).toBeVisible();
  });

  it('renders "Cloud Security Development" stage with all 7 modules', async () => {
    const user = userEvent.setup();
    const stage = CURRICULUM_STAGES[2];
    const { container } = render(<StageSection stage={stage} />);

    expect(screen.getByRole('heading', { level: 2, name: 'Cloud Security Development' })).toBeInTheDocument();

    // Expand to see modules
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);

    // Verify all 7 modules (using heading role for module names)
    expect(screen.getByRole('heading', { level: 3, name: 'What is Cloud Security Development?' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'IAM Fundamentals' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'API Patterns and SDKs' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Secrets Management In The Cloud' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Cloud Logging and Monitoring' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'Serverless' })).toBeVisible();
    expect(screen.getByRole('heading', { level: 3, name: 'IaC Security' })).toBeVisible();
  });

  it('renders "Capstone Projects" stage with projects list', async () => {
    const user = userEvent.setup();
    const stage = CURRICULUM_STAGES[3];
    const { container } = render(<StageSection stage={stage} />);

    expect(screen.getByRole('heading', { level: 2, name: 'Capstone Projects' })).toBeInTheDocument();

    // Expand to see projects
    const expandButton = container.querySelector('button[aria-expanded]') as HTMLElement;
    await user.click(expandButton);

    // Verify projects section heading
    expect(screen.getByRole('heading', { level: 3, name: 'Capstone Projects' })).toBeVisible();

    // Verify all projects
    expect(screen.getByText('DevSecOps Capstone: Build an automated security pipeline')).toBeVisible();
    expect(screen.getByText('Cloud Security Development Capstone: Build a self-healing cloud environment')).toBeVisible();
  });

  it('displays correct stage numbers for all stages', () => {
    CURRICULUM_STAGES.forEach((stage) => {
      const { container } = render(<StageSection stage={stage} />);
      const badge = container.querySelector('.bg-gradient-to-br.from-primary-400');
      expect(badge).toHaveTextContent(String(stage.stageNumber));
    });
  });
});
