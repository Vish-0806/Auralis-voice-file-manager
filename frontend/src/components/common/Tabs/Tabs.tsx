import React, { useState } from 'react';

export interface TabItem {
  key: string;
  label: string;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  defaultActiveKey?: string;
  onChange?: (key: string) => void;
  className?: string;
}

export const Tabs: React.FC<TabsProps> = ({
  items,
  defaultActiveKey,
  onChange,
  className = ''
}) => {
  const [activeKey, setActiveKey] = useState(
    defaultActiveKey || (items.length > 0 ? items[0].key : '')
  );

  const handleTabClick = (key: string) => {
    setActiveKey(key);
    onChange?.(key);
  };

  const activeTab = items.find((item) => item.key === activeKey);

  return (
    <div className={`auralis-tabs ${className}`.trim()}>
      <ul className="nav nav-tabs" role="tablist">
        {items.map((item) => {
          const isActive = item.key === activeKey;
          return (
            <li key={item.key} className="nav-item" role="presentation">
              <button
                className={`nav-link ${isActive ? 'active' : ''} ${
                  item.disabled ? 'disabled' : ''
                }`}
                role="tab"
                type="button"
                id={`tab-${item.key}`}
                aria-selected={isActive}
                aria-controls={`panel-${item.key}`}
                disabled={item.disabled}
                onClick={() => handleTabClick(item.key)}
              >
                {item.label}
              </button>
            </li>
          );
        })}
      </ul>
      <div className="tab-content pt-3">
        {activeTab && (
          <div
            className="tab-pane active"
            role="tabpanel"
            id={`panel-${activeTab.key}`}
            aria-labelledby={`tab-${activeTab.key}`}
          >
            {activeTab.content}
          </div>
        )}
      </div>
    </div>
  );
};
