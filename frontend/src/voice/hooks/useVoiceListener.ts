import { 
  useVoiceStore, 
  selectListenerStatus, 
  selectListenerRunning, 
  selectVoiceError 
} from '../state';
import { voiceController } from '../services/voiceController';

export const useVoiceListener = () => {
  const listenerStatus = useVoiceStore(selectListenerStatus);
  const isRunning = useVoiceStore(selectListenerRunning);
  const error = useVoiceStore(selectVoiceError);
  const loading = listenerStatus === 'loading';

  const start = () => voiceController.startContinuousListener();
  const stop = () => voiceController.stopContinuousListener();
  const refresh = () => voiceController.refreshListenerStatus();

  return {
    listenerStatus,
    isRunning,
    loading,
    error,
    start,
    stop,
    refresh
  };
};
export default useVoiceListener;
