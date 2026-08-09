import { VoiceStatus as VSComp } from './components/VoiceStatus';
import { VoiceError as VEComp } from './components/VoiceError';
import { VoiceStatus as VSType, VoiceError as VEType } from './types/voice';

export type VoiceStatus = VSType;
export type VoiceError = VEType;

export const VoiceStatus = VSComp;
export const VoiceError = VEComp;

export { VoiceControl } from './components/VoiceControl';
export { VoiceVisualizer } from './components/VoiceVisualizer';
export { TranscriptPanel } from './components/TranscriptPanel';
export { ListenerControl } from './components/ListenerControl';

export type { 
  ListenerStatus, 
  Transcript, 
  VoiceSession, 
  VoiceCapabilities, 
  VoiceState 
} from './types';

export * from './state';
export * from './services';
export * from './hooks';
