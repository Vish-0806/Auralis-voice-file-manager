import { 
  useVoiceStore, 
  selectVoiceStatus, 
  selectVoiceTranscript, 
  selectVoicePartialTranscript, 
  selectVoiceFinalTranscript, 
  selectVoiceError, 
  selectVoiceLatestResult 
} from '../state';
import { voiceController } from '../services/voiceController';

export const useVoice = () => {
  const status = useVoiceStore(selectVoiceStatus);
  const transcript = useVoiceStore(selectVoiceTranscript);
  const partialTranscript = useVoiceStore(selectVoicePartialTranscript);
  const finalTranscript = useVoiceStore(selectVoiceFinalTranscript);
  const error = useVoiceStore(selectVoiceError);
  const latestResult = useVoiceStore(selectVoiceLatestResult);
  
  const isListening = status === 'LISTENING';
  const isProcessing = status === 'PROCESSING' || status === 'TRANSCRIBING';

  const startListening = () => voiceController.startListening();
  const stopListening = () => voiceController.stopListening();
  const clearError = useVoiceStore((state) => state.clearError);
  const reset = useVoiceStore((state) => state.reset);

  return {
    status,
    transcript,
    partialTranscript,
    finalTranscript,
    error,
    isListening,
    isProcessing,
    latestResult,
    startListening,
    stopListening,
    clearError,
    reset,
  };
};
export default useVoice;
