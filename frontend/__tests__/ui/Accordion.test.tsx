/**
 * Unit tests for the Accordion component.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { Accordion } from '@/components/ui/Accordion';

const items = [
  { id: 'a', trigger: 'First', content: 'First content' },
  { id: 'b', trigger: 'Second', content: 'Second content' },
  { id: 'c', trigger: 'Third', content: 'Third content' },
];

function triggers() {
  return items.map((it) => screen.getByRole('button', { name: it.trigger }));
}

it('renders all triggers collapsed by default', () => {
  render(<Accordion items={items} />);
  triggers().forEach((t) => expect(t).toHaveAttribute('aria-expanded', 'false'));
});

it('opens an item on click and closes it on second click', () => {
  render(<Accordion items={items} />);
  const [first] = triggers();
  fireEvent.click(first);
  expect(first).toHaveAttribute('aria-expanded', 'true');
  fireEvent.click(first);
  expect(first).toHaveAttribute('aria-expanded', 'false');
});

it('only keeps one item open at a time', () => {
  render(<Accordion items={items} />);
  const [first, second] = triggers();
  fireEvent.click(first);
  fireEvent.click(second);
  expect(first).toHaveAttribute('aria-expanded', 'false');
  expect(second).toHaveAttribute('aria-expanded', 'true');
});

it('opens the item specified by defaultOpenId', () => {
  render(<Accordion items={items} defaultOpenId="b" />);
  expect(screen.getByRole('button', { name: 'Second' })).toHaveAttribute('aria-expanded', 'true');
});

it('toggles with Enter and Space keys', () => {
  render(<Accordion items={items} />);
  const [first] = triggers();
  fireEvent.keyDown(first, { key: 'Enter' });
  expect(first).toHaveAttribute('aria-expanded', 'true');
  fireEvent.keyDown(first, { key: ' ' });
  expect(first).toHaveAttribute('aria-expanded', 'false');
});

it('moves focus with ArrowDown / ArrowUp (wrapping)', () => {
  render(<Accordion items={items} />);
  const [first, second, third] = triggers();
  first.focus();
  fireEvent.keyDown(first, { key: 'ArrowDown' });
  expect(second).toHaveFocus();
  fireEvent.keyDown(second, { key: 'ArrowUp' });
  expect(first).toHaveFocus();
  // ArrowUp from first wraps to last
  fireEvent.keyDown(first, { key: 'ArrowUp' });
  expect(third).toHaveFocus();
});

it('jumps to first/last with Home / End', () => {
  render(<Accordion items={items} />);
  const [first, , third] = triggers();
  first.focus();
  fireEvent.keyDown(first, { key: 'End' });
  expect(third).toHaveFocus();
  fireEvent.keyDown(third, { key: 'Home' });
  expect(first).toHaveFocus();
});
