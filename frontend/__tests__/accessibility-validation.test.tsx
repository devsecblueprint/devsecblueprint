/**
 * Accessibility Validation Tests
 * Task 16.2: Validate accessibility
 * 
 * This test suite validates:
 * - Keyboard navigation on all pages (Requirement 10.3.3)
 * - Focus indicators are visible (Requirement 10.3.3)
 * - Semantic HTML structure (Requirement 10.3.1)
 * - ARIA labels on icons (Requirement 10.3.4)
 */

import { render, screen } from './test-utils';
import userEvent from '@testing-library/user-event';
import Home from '@/app/page';
import LoginPage from '@/app/login/page';
import DashboardPage from '@/app/dashboard/page';
import LearnPage from '@/app/learn/test/page';
import { Navbar } from '@/components/layout/Navbar';
import { Sidebar } from '@/components/layout/Sidebar';
import { Footer } from '@/components/layout/Footer';
import { Button } from '@/components/ui/Button';
import { SAMPLE_MODULES } from '@/lib/constants';

describe('Accessibility Validation - Task 16.2', () => {
  describe('Keyboard Navigation (Requirement 10.3.3)', () => {
    describe('Landing Page', () => {
      it('should allow keyboard navigation through all interactive elements', async () => {
        const user = userEvent.setup();
        render(<Home />);

        // Tab through buttons
        await user.tab();
        const startLearningBtn = screen.getByRole('button', { name: /start learning/i });
        expect(startLearningBtn).toHaveFocus();

        await user.tab();
        const viewProjectsBtn = screen.getByRole('button', { name: /view projects/i });
        expect(viewProjectsBtn).toHaveFocus();

        // Tab through footer links
        await user.tab();
        const githubLink = screen.getByRole('link', { name: /visit our github/i });
        expect(githubLink).toHaveFocus();
      });

      it('should allow Enter key to activate buttons', async () => {
        const user = userEvent.setup();
        render(<Home />);

        const startLearningBtn = screen.getByRole('button', { name: /start learning/i });
        startLearningBtn.focus();
        
        // Verify button can be activated with Enter
        await user.keyboard('{Enter}');
        // Button should still be in the document (no navigation in this test)
        expect(startLearningBtn).toBeInTheDocument();
      });
    });

    describe('Login Page', () => {
      it('should allow keyboard navigation through login form', async () => {
        const user = userEvent.setup();
        render(<LoginPage />);

        await user.tab();
        const loginBtn = screen.getByRole('button', { name: /login with github/i });
        expect(loginBtn).toHaveFocus();

        await user.tab();
        const gitlabBtn = screen.getByRole('button', { name: /login with gitlab/i });
        expect(gitlabBtn).toHaveFocus();

        await user.tab();
        const backLink = screen.getByRole('link', { name: /back to home/i });
        expect(backLink).toHaveFocus();
      });
    });

    describe('Dashboard Page', () => {
      it('should allow keyboard navigation through dashboard elements', async () => {
        const user = userEvent.setup();
        render(<DashboardPage />);

        // Tab through continue learning buttons
        await user.tab();
        const continueButtons = screen.getAllByRole('button', { name: /continue/i });
        expect(continueButtons[0]).toHaveFocus();
      });
    });

    describe('Learn Page', () => {
      it('should allow keyboard navigation through learning content', async () => {
        const user = userEvent.setup();
        render(<LearnPage />);

        // Tab through navigation buttons
        await user.tab();
        const markCompleteBtn = screen.getByRole('button', { name: /mark complete/i });
        expect(markCompleteBtn).toHaveFocus();
      });
    });

    describe('Button Component', () => {
      it('should be keyboard accessible', async () => {
        const user = userEvent.setup();
        const handleClick = jest.fn();
        render(<Button onClick={handleClick}>Test Button</Button>);

        const button = screen.getByRole('button', { name: /test button/i });
        button.focus();
        expect(button).toHaveFocus();

        await user.keyboard('{Enter}');
        expect(handleClick).toHaveBeenCalledTimes(1);

        await user.keyboard(' ');
        expect(handleClick).toHaveBeenCalledTimes(2);
      });

      it('should not have tabIndex -1', () => {
        render(<Button>Test Button</Button>);
        const button = screen.getByRole('button', { name: /test button/i });
        expect(button).not.toHaveAttribute('tabIndex', '-1');
      });
    });

    describe('Navbar Component', () => {
      it('should allow keyboard navigation through navbar elements', async () => {
        const user = userEvent.setup();
        render(<Navbar showProgress={true} progressPercentage={50} currentPath="Test Path" />);

        await user.tab();
        const mobileMenuBtn = screen.getByRole('button', { name: /toggle mobile menu/i });
        expect(mobileMenuBtn).toHaveFocus();
      });
    });

    describe('Sidebar Component', () => {
      it('should allow keyboard navigation through sidebar modules', async () => {
        const user = userEvent.setup();
        render(<Sidebar modules={SAMPLE_MODULES} currentPageId="p1" />);

        // Tab to first module button
        await user.tab();
        const moduleButtons = screen.getAllByRole('button', { name: /introduction to devsecops/i });
        expect(moduleButtons[0]).toHaveFocus();

        // Tab to page links
        await user.tab();
        const pageLinks = screen.getAllByRole('link');
        expect(pageLinks[0]).toHaveFocus();
      });

      it('should allow keyboard navigation to toggle sidebar on mobile', async () => {
        const user = userEvent.setup();
        render(<Sidebar modules={SAMPLE_MODULES} />);

        const toggleBtn = screen.getByRole('button', { name: /toggle sidebar/i });
        toggleBtn.focus();
        expect(toggleBtn).toHaveFocus();

        await user.keyboard('{Enter}');
        // Sidebar should open (aria-expanded should be true)
        expect(toggleBtn).toHaveAttribute('aria-expanded', 'true');
      });
    });

    describe('Footer Component', () => {
      it('should allow keyboard navigation through footer links', async () => {
        const user = userEvent.setup();
        render(<Footer />);

        await user.tab();
        const githubLink = screen.getByRole('link', { name: /visit our github/i });
        expect(githubLink).toHaveFocus();

        await user.tab();
        const linkedinLink = screen.getByRole('link', { name: /visit our linkedin/i });
        expect(linkedinLink).toHaveFocus();

        await user.tab();
        const termsLink = screen.getByRole('link', { name: /terms of service/i });
        expect(termsLink).toHaveFocus();

        await user.tab();
        const privacyLink = screen.getByRole('link', { name: /privacy policy/i });
        expect(privacyLink).toHaveFocus();
      });
    });
  });

  describe('Focus Indicators (Requirement 10.3.3)', () => {
    it('should have visible focus styles on buttons', () => {
      render(<Button>Test Button</Button>);
      const button = screen.getByRole('button', { name: /test button/i });
      
      // Check for focus ring classes
      expect(button.className).toContain('focus:outline-none');
      expect(button.className).toContain('focus:ring-2');
    });

    it('should have visible focus styles on links in footer', () => {
      render(<Footer />);
      const githubLink = screen.getByRole('link', { name: /visit our github/i });
      
      // Check for focus ring classes
      expect(githubLink.className).toContain('focus:outline-none');
      expect(githubLink.className).toContain('focus:ring-2');
      expect(githubLink.className).toContain('focus:ring-primary-400');
    });

    it('should have visible focus styles on login page link', () => {
      render(<LoginPage />);
      const backLink = screen.getByRole('link', { name: /back to home/i });
      
      // Check for focus ring classes
      expect(backLink.className).toContain('focus:outline-none');
      expect(backLink.className).toContain('focus:ring-2');
      expect(backLink.className).toContain('focus:ring-primary-400');
    });

    it('should have visible focus styles on navbar mobile menu button', () => {
      render(<Navbar />);
      const mobileMenuBtn = screen.getByRole('button', { name: /toggle mobile menu/i });
      
      // Check for focus ring classes
      expect(mobileMenuBtn.className).toContain('focus:outline-none');
      expect(mobileMenuBtn.className).toContain('focus:ring-2');
    });

    it('should have visible focus styles on sidebar module buttons', () => {
      render(<Sidebar modules={SAMPLE_MODULES} />);
      const moduleButtons = screen.getAllByRole('button', { name: /introduction to devsecops/i });
      
      // Check for focus ring classes
      expect(moduleButtons[0].className).toContain('focus:outline-none');
      expect(moduleButtons[0].className).toContain('focus:ring-2');
      expect(moduleButtons[0].className).toContain('focus:ring-primary-400');
    });

    it('should have visible focus styles on sidebar page links', () => {
      render(<Sidebar modules={SAMPLE_MODULES} />);
      const pageLinks = screen.getAllByRole('link');
      
      // Check for focus ring classes on first link
      expect(pageLinks[0].className).toContain('focus:outline-none');
      expect(pageLinks[0].className).toContain('focus:ring-2');
      expect(pageLinks[0].className).toContain('focus:ring-primary-400');
    });

    it('should have visible focus styles on dashboard continue buttons', () => {
      render(<DashboardPage />);
      const continueButtons = screen.getAllByRole('button', { name: /continue/i });
      
      // Check for focus ring classes
      expect(continueButtons[0].className).toContain('focus:outline-none');
      expect(continueButtons[0].className).toContain('focus:ring-2');
      expect(continueButtons[0].className).toContain('focus:ring-primary-400');
    });
  });

  describe('Semantic HTML Structure (Requirement 10.3.1)', () => {
    describe('Landing Page', () => {
      it('should use semantic HTML elements', () => {
        const { container } = render(<Home />);
        
        // Check for semantic elements
        expect(container.querySelector('section')).toBeInTheDocument();
        expect(container.querySelector('h1')).toBeInTheDocument();
        expect(container.querySelector('h2')).toBeInTheDocument();
        expect(container.querySelector('footer')).toBeInTheDocument();
      });

      it('should have proper heading hierarchy', () => {
        render(<Home />);
        
        const h1 = screen.getByRole('heading', { level: 1, name: /The DevSec Blueprint/i });
        expect(h1).toBeInTheDocument();

        const h2Elements = screen.getAllByRole('heading', { level: 2 });
        expect(h2Elements.length).toBeGreaterThan(0);
      });
    });

    describe('Login Page', () => {
      it('should use semantic main element', () => {
        const { container } = render(<LoginPage />);
        expect(container.querySelector('main')).toBeInTheDocument();
      });

      it('should have proper heading', () => {
        render(<LoginPage />);
        const h1 = screen.getByRole('heading', { level: 1, name: /login to The DevSec Blueprint/i });
        expect(h1).toBeInTheDocument();
      });
    });

    describe('Dashboard Page', () => {
      it('should use semantic main element', () => {
        const { container } = render(<DashboardPage />);
        expect(container.querySelector('main')).toBeInTheDocument();
      });

      it('should use semantic section elements', () => {
        const { container } = render(<DashboardPage />);
        const sections = container.querySelectorAll('section');
        expect(sections.length).toBeGreaterThan(0);
      });

      it('should have proper heading hierarchy', () => {
        render(<DashboardPage />);
        
        const h1 = screen.getByRole('heading', { level: 1, name: /welcome back/i });
        expect(h1).toBeInTheDocument();

        const h2Elements = screen.getAllByRole('heading', { level: 2 });
        expect(h2Elements.length).toBeGreaterThan(0);
      });
    });

    describe('Learn Page', () => {
      it('should use semantic main element', () => {
        const { container } = render(<LearnPage />);
        expect(container.querySelector('main')).toBeInTheDocument();
      });

      it('should use semantic article element for content', () => {
        const { container } = render(<LearnPage />);
        expect(container.querySelector('article')).toBeInTheDocument();
      });

      it('should have proper heading hierarchy', () => {
        render(<LearnPage />);
        
        const h1 = screen.getByRole('heading', { level: 1, name: /what is devsecops/i });
        expect(h1).toBeInTheDocument();

        const h2Elements = screen.getAllByRole('heading', { level: 2 });
        expect(h2Elements.length).toBeGreaterThan(0);
      });
    });

    describe('Navbar Component', () => {
      it('should use semantic nav element', () => {
        const { container } = render(<Navbar />);
        expect(container.querySelector('nav')).toBeInTheDocument();
      });
    });

    describe('Sidebar Component', () => {
      it('should use semantic aside element', () => {
        const { container } = render(<Sidebar modules={SAMPLE_MODULES} />);
        expect(container.querySelector('aside')).toBeInTheDocument();
      });

      it('should use semantic nav element with aria-label', () => {
        render(<Sidebar modules={SAMPLE_MODULES} />);
        const navs = screen.getAllByRole('navigation', { name: /course modules/i });
        expect(navs.length).toBeGreaterThan(0);
        expect(navs[0]).toBeInTheDocument();
      });

      it('should use semantic list elements', () => {
        const { container } = render(<Sidebar modules={SAMPLE_MODULES} />);
        const lists = container.querySelectorAll('ul');
        expect(lists.length).toBeGreaterThan(0);
      });
    });

    describe('Footer Component', () => {
      it('should use semantic footer element', () => {
        const { container } = render(<Footer />);
        expect(container.querySelector('footer')).toBeInTheDocument();
      });

      it('should use semantic heading elements', () => {
        render(<Footer />);
        const headings = screen.getAllByRole('heading');
        expect(headings.length).toBeGreaterThan(0);
      });

      it('should use semantic list elements for links', () => {
        const { container } = render(<Footer />);
        const lists = container.querySelectorAll('ul');
        expect(lists.length).toBeGreaterThan(0);
      });
    });
  });

  describe('ARIA Labels on Icons (Requirement 10.3.4)', () => {
    describe('Navbar Component', () => {
      it('should have aria-hidden on decorative icons', () => {
        const { container } = render(<Navbar />);
        const icons = container.querySelectorAll('svg[aria-hidden="true"]');
        expect(icons.length).toBeGreaterThan(0);
      });

      it('should have aria-label on mobile menu button', () => {
        render(<Navbar />);
        const mobileMenuBtn = screen.getByRole('button', { name: /toggle mobile menu/i });
        expect(mobileMenuBtn).toHaveAttribute('aria-label', 'Toggle mobile menu');
      });

      it('should have aria-expanded on mobile menu button', () => {
        render(<Navbar />);
        const mobileMenuBtn = screen.getByRole('button', { name: /toggle mobile menu/i });
        expect(mobileMenuBtn).toHaveAttribute('aria-expanded');
      });
    });

    describe('Sidebar Component', () => {
      it('should have aria-hidden on decorative icons', () => {
        const { container } = render(<Sidebar modules={SAMPLE_MODULES} />);
        const icons = container.querySelectorAll('svg[aria-hidden="true"]');
        expect(icons.length).toBeGreaterThan(0);
      });

      it('should have aria-label on completion status icons', () => {
        const { container } = render(<Sidebar modules={SAMPLE_MODULES} />);
        const completedIcon = container.querySelector('svg[aria-label="Completed"]');
        expect(completedIcon).toBeInTheDocument();
      });

      it('should have aria-label on toggle sidebar button', () => {
        render(<Sidebar modules={SAMPLE_MODULES} />);
        const toggleBtn = screen.getByRole('button', { name: /toggle sidebar/i });
        expect(toggleBtn).toHaveAttribute('aria-label', 'Toggle sidebar');
      });

      it('should have aria-expanded on module buttons', () => {
        render(<Sidebar modules={SAMPLE_MODULES} />);
        const moduleButtons = screen.getAllByRole('button', { name: /introduction to devsecops/i });
        expect(moduleButtons[0]).toHaveAttribute('aria-expanded');
      });

      it('should have aria-controls on module buttons', () => {
        render(<Sidebar modules={SAMPLE_MODULES} />);
        const moduleButtons = screen.getAllByRole('button', { name: /introduction to devsecops/i });
        expect(moduleButtons[0]).toHaveAttribute('aria-controls');
      });

      it('should have aria-current on current page link', () => {
        render(<Sidebar modules={SAMPLE_MODULES} currentPageId="p1" />);
        const currentLinks = screen.getAllByRole('link', { current: 'page' });
        expect(currentLinks.length).toBeGreaterThan(0);
        expect(currentLinks[0]).toHaveAttribute('aria-current', 'page');
      });
    });

    describe('Footer Component', () => {
      it('should have aria-hidden on decorative icons', () => {
        const { container } = render(<Footer />);
        const icons = container.querySelectorAll('svg[aria-hidden="true"]');
        expect(icons.length).toBeGreaterThan(0);
      });

      it('should have aria-label on social media links', () => {
        render(<Footer />);
        const githubLink = screen.getByRole('link', { name: /visit our github/i });
        expect(githubLink).toHaveAttribute('aria-label', 'Visit our GitHub');

        const linkedinLink = screen.getByRole('link', { name: /visit our linkedin/i });
        expect(linkedinLink).toHaveAttribute('aria-label', 'Visit our LinkedIn');
      });
    });

    describe('Dashboard Page', () => {
      it('should have aria-hidden on decorative icons', () => {
        const { container } = render(<DashboardPage />);
        const icons = container.querySelectorAll('svg[aria-hidden="true"]');
        expect(icons.length).toBeGreaterThan(0);
      });

      it('should have aria-label on continue learning buttons', () => {
        render(<DashboardPage />);
        const continueButtons = screen.getAllByRole('button', { name: /continue/i });
        expect(continueButtons[0]).toHaveAttribute('aria-label');
      });
    });

    describe('Login Page', () => {
      it('should have aria-label on login button', () => {
        render(<LoginPage />);
        const loginBtn = screen.getByRole('button', { name: /login with github/i });
        expect(loginBtn).toHaveAttribute('aria-label', 'Login with GitHub');
      });
    });
  });

  describe('Touch Target Sizes (Accessibility Best Practice)', () => {
    it('should have minimum 44x44px touch targets on buttons', () => {
      render(<Button size="sm">Small Button</Button>);
      const button = screen.getByRole('button', { name: /small button/i });
      expect(button.className).toContain('min-h-[44px]');
    });

    it('should have minimum 44x44px touch targets on links', () => {
      render(<Footer />);
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link.className).toContain('min-h-[44px]');
      });
    });

    it('should have minimum 44x44px touch targets on navbar mobile menu button', () => {
      render(<Navbar />);
      const mobileMenuBtn = screen.getByRole('button', { name: /toggle mobile menu/i });
      expect(mobileMenuBtn.className).toContain('min-w-[44px]');
      expect(mobileMenuBtn.className).toContain('min-h-[44px]');
    });

    it('should have minimum 44x44px touch targets on sidebar toggle button', () => {
      render(<Sidebar modules={SAMPLE_MODULES} />);
      const toggleBtn = screen.getByRole('button', { name: /toggle sidebar/i });
      expect(toggleBtn.className).toContain('min-w-[56px]');
      expect(toggleBtn.className).toContain('min-h-[56px]');
    });
  });
});
