/**
 * Unit tests for NavDropdown (desktop + mobile variants).
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { NavDropdown } from '@/components/layout/NavDropdown';

let pathnameValue = '/';
jest.mock('next/navigation', () => ({ usePathname: () => pathnameValue }));

const items = [
  { label: 'About Us', href: '/about' },
  { label: 'FAQ', href: '/about/faq' },
];

beforeEach(() => {
  pathnameValue = '/';
});

describe('desktop variant', () => {
  it('opens the menu on button click and shows items', () => {
    render(<NavDropdown items={items} label="About" isActive={false} />);
    fireEvent.click(screen.getByRole('button', { name: /about/i }));
    expect(screen.getByRole('menuitem', { name: 'About Us' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'FAQ' })).toBeInTheDocument();
  });

  it('opens on mouse enter and closes on mouse leave', () => {
    const { container } = render(<NavDropdown items={items} label="About" isActive={false} />);
    const wrapper = container.firstChild as HTMLElement;
    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole('menu')).toBeInTheDocument();
    fireEvent.mouseLeave(wrapper);
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('calls onNavigate and closes when an item is clicked', () => {
    const onNavigate = jest.fn();
    render(<NavDropdown items={items} label="About" isActive={false} onNavigate={onNavigate} />);
    fireEvent.click(screen.getByRole('button', { name: /about/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'FAQ' }));
    expect(onNavigate).toHaveBeenCalled();
  });

  it('closes on Escape', () => {
    render(<NavDropdown items={items} label="About" isActive={false} />);
    const btn = screen.getByRole('button', { name: /about/i });
    fireEvent.click(btn);
    expect(screen.getByRole('menu')).toBeInTheDocument();
    fireEvent.keyDown(btn, { key: 'Escape' });
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('marks the active item based on pathname', () => {
    pathnameValue = '/about/faq';
    render(<NavDropdown items={items} label="About" isActive />);
    fireEvent.click(screen.getByRole('button', { name: /about/i }));
    const faq = screen.getByRole('menuitem', { name: 'FAQ' });
    expect(faq.className).toMatch(/text-primary-500/);
  });
});

describe('mobile variant', () => {
  it('expands and collapses the section', () => {
    render(<NavDropdown items={items} label="About" isActive={false} isMobile />);
    const toggle = screen.getByRole('button', { name: /about/i });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menuitem', { name: 'About Us' })).toBeInTheDocument();
  });
});
