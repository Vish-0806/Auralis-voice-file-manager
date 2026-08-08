import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Input } from '@/components';

describe('Input Component', () => {
  it('should render correctly with label', () => {
    render(<Input label="Username" placeholder="Enter username" />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter username')).toBeInTheDocument();
  });

  it('should display helper text when provided', () => {
    render(<Input label="Password" helperText="Must be 8 characters long" />);
    expect(screen.getByText('Must be 8 characters long')).toBeInTheDocument();
  });

  it('should display error message and mark input invalid', () => {
    render(<Input label="Email" error="Invalid email address" />);
    const errorText = screen.getByText('Invalid email address');
    const input = screen.getByLabelText('Email');
    expect(errorText).toBeInTheDocument();
    expect(input).toHaveClass('is-invalid');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('should call onChange handler when value updates', () => {
    let value = '';
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      value = e.target.value;
    };
    render(<Input label="Name" onChange={handleChange} />);
    const input = screen.getByLabelText('Name');
    fireEvent.change(input, { target: { value: 'Alice' } });
    expect(value).toBe('Alice');
  });
});
