import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommunityEngagementCard } from '@/components/dashboard/CommunityEngagementCard';

// Mock TestimonialForm to avoid complex modal logic in unit tests
jest.mock('@/components/features/TestimonialForm', () => ({
  TestimonialForm: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? (
      <div data-testid="testimonial-modal">
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

describe('CommunityEngagementCard', () => {
  it('renders "Community & Engagement" heading', () => {
    render(<CommunityEngagementCard />);
    expect(
      screen.getByRole('heading', { level: 3, name: 'Community & Engagement' })
    ).toBeInTheDocument();
  });

  describe('community links', () => {
    it('renders Discord link as external', () => {
      render(<CommunityEngagementCard />);
      const discordLink = screen.getByLabelText('Join our Discord community (opens in new tab)');
      expect(discordLink).toBeInTheDocument();
      expect(discordLink).toHaveAttribute('href', 'https://discord.gg/devsecblueprint');
      expect(discordLink).toHaveAttribute('target', '_blank');
      expect(discordLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders Raise an Issue link as external', () => {
      render(<CommunityEngagementCard />);
      const issueLink = screen.getByLabelText('Raise an issue on GitHub (opens in new tab)');
      expect(issueLink).toBeInTheDocument();
      expect(issueLink).toHaveAttribute('href', 'https://github.com/devsecblueprint/devsecblueprint/issues');
      expect(issueLink).toHaveAttribute('target', '_blank');
      expect(issueLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders Star on GitHub link as external', () => {
      render(<CommunityEngagementCard />);
      const starLink = screen.getByLabelText('Star the project on GitHub (opens in new tab)');
      expect(starLink).toBeInTheDocument();
      expect(starLink).toHaveAttribute('href', 'https://github.com/devsecblueprint/devsecblueprint');
      expect(starLink).toHaveAttribute('target', '_blank');
      expect(starLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders Donate link as external', () => {
      render(<CommunityEngagementCard />);
      const donateLink = screen.getByLabelText('Sponsor the project on GitHub (opens in new tab)');
      expect(donateLink).toBeInTheDocument();
      expect(donateLink).toHaveAttribute('href', 'https://github.com/sponsors/devsecblueprint');
      expect(donateLink).toHaveAttribute('target', '_blank');
      expect(donateLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders Merch Store link as external', () => {
      render(<CommunityEngagementCard />);
      const merchLink = screen.getByLabelText('Visit the merch store (opens in new tab)');
      expect(merchLink).toBeInTheDocument();
      expect(merchLink).toHaveAttribute('href', 'https://shop.devsecblueprint.com/');
      expect(merchLink).toHaveAttribute('target', '_blank');
      expect(merchLink).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('renders all 6 community action items', () => {
      render(<CommunityEngagementCard />);
      expect(screen.getByText('Discord')).toBeInTheDocument();
      expect(screen.getByText('Raise an Issue')).toBeInTheDocument();
      expect(screen.getByText('Share Your Success Story')).toBeInTheDocument();
      expect(screen.getByText('Star on GitHub')).toBeInTheDocument();
      expect(screen.getByText('Donate')).toBeInTheDocument();
      expect(screen.getByText('Merch Store')).toBeInTheDocument();
    });
  });

  describe('testimonial modal', () => {
    it('opens testimonial modal when "Share Your Success Story" is clicked', () => {
      render(<CommunityEngagementCard />);
      const storyButton = screen.getByLabelText('Share your success story (opens modal)');
      expect(screen.queryByTestId('testimonial-modal')).not.toBeInTheDocument();

      fireEvent.click(storyButton);
      expect(screen.getByTestId('testimonial-modal')).toBeInTheDocument();
    });

    it('closes testimonial modal when close is triggered', () => {
      render(<CommunityEngagementCard />);
      const storyButton = screen.getByLabelText('Share your success story (opens modal)');
      fireEvent.click(storyButton);

      expect(screen.getByTestId('testimonial-modal')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Close'));
      expect(screen.queryByTestId('testimonial-modal')).not.toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('marks decorative icons as aria-hidden', () => {
      const { container } = render(<CommunityEngagementCard />);
      const hiddenElements = container.querySelectorAll('[aria-hidden="true"]');
      expect(hiddenElements.length).toBeGreaterThan(0);
    });

    it('does not accept capstoneData props', () => {
      // Type-level check: component accepts no props
      render(<CommunityEngagementCard />);
      expect(screen.getByRole('heading', { level: 3 })).toBeInTheDocument();
    });
  });
});
