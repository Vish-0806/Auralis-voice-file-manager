import { VoiceError as VoiceErrorType } from '../../types/voice';

export interface VoiceErrorProps {
  error?: VoiceErrorType | null;
  onClear?: () => void;
  className?: string;
}
