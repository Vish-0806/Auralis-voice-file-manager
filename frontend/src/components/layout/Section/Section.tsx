import React from 'react';

export interface SectionProps extends React.HTMLAttributes<HTMLElement> {
  py?: 0 | 1 | 2 | 3 | 4 | 5;
}

export const Section: React.FC<SectionProps> = ({
  py = 3,
  className = '',
  children,
  ...props
}) => {
  const classes = [`py-${py}`, className].filter(Boolean).join(' ');
  return (
    <section className={classes} {...props}>
      {children}
    </section>
  );
};
