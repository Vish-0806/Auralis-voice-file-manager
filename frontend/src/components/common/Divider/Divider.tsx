import React from 'react';

export interface DividerProps extends React.HTMLAttributes<HTMLHRElement> {
  vertical?: boolean;
  margin?: 0 | 1 | 2 | 3 | 4 | 5;
}

export const Divider: React.FC<DividerProps> = ({
  vertical = false,
  margin = 3,
  className = '',
  ...props
}) => {
  if (vertical) {
    return (
      <div
        className={`vr mx-${margin} ${className}`.trim()}
        role="separator"
        {...props}
      />
    );
  }

  return (
    <hr
      className={`my-${margin} ${className}`.trim()}
      {...props}
    />
  );
};
