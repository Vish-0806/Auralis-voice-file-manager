import { VoiceCommandResponse } from '../../../services/api/voiceService';

export interface TranscriptPanelProps {
  partialTranscript?: string;
  finalTranscript?: string;
  latestResult?: VoiceCommandResponse | null;
  processing?: boolean;
  error?: string | null;
  className?: string;
}
