export interface VoiceControlProps {
  isListening: boolean;
  isProcessing: boolean;
  disabled?: boolean;
  onStart: () => void;
  onStop: () => void;
  className?: string;
}
