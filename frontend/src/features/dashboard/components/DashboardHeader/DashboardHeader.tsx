import React from 'react';

export const DashboardHeader: React.FC = () => {
  const hours = new Date().getHours();
  let greeting = 'Good morning';
  if (hours >= 12 && hours < 17) greeting = 'Good afternoon';
  if (hours >= 17) greeting = 'Good evening';

  return (
    <div className="card border-0 bg-primary text-white p-4 shadow-sm mb-4 position-relative overflow-hidden rounded-4">
      {/* Decorative backdrop shapes */}
      <div 
        className="position-absolute bg-white opacity-10 rounded-circle" 
        style={{ width: '300px', height: '300px', right: '-100px', top: '-100px' }} 
      />
      <div 
        className="position-absolute bg-white opacity-5 rounded-circle" 
        style={{ width: '150px', height: '150px', right: '150px', bottom: '-50px' }} 
      />
      
      <div className="position-relative z-1">
        <h4 className="display-6 fw-bold mb-2">{greeting}, User</h4>
        <p className="lead mb-0 text-white-50 fs-6">
          Welcome to the Auralis Workspace. Speak commands or stage document buffers to manage your files.
        </p>
      </div>
    </div>
  );
};
export default DashboardHeader;
