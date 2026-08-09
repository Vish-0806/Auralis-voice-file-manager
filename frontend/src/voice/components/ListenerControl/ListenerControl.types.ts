export interface ListenerControlProps {
  isRunning: boolean;
  loading: boolean;
  onStart: () => void;
  onStop: () => void;
  onRefresh: () => void;
  className?: string;
}
