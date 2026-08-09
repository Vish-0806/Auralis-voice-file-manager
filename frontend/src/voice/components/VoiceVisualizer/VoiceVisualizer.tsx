import React from 'react';
import { VoiceVisualizerProps } from './VoiceVisualizer.types';

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  status,
  className = ''
}) => {
  const isListening = status === 'LISTENING';
  const isProcessing = status === 'PROCESSING' || status === 'TRANSCRIBING';
  const isError = status === 'ERROR' || status === 'DISCONNECTED';

  // Generate 5 bars for the wave
  const bars = Array.from({ length: 5 });

  return (
    <div 
      className={`voice-visualizer d-flex align-items-center justify-content-center gap-1 ${className}`}
      style={{ height: '40px', minWidth: '80px' }}
      aria-hidden="true"
    >
      <style>{`
        @keyframes voiceWave {
          0%, 100% { transform: scaleY(0.3); }
          50% { transform: scaleY(1.0); }
        }
        @keyframes voiceProcessing {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1.0; }
        }
        .voice-bar {
          width: 4px;
          height: 100%;
          background-color: var(--bs-primary, #0d6efd);
          border-radius: 2px;
          transform-origin: center;
          transition: background-color 0.3s ease, transform 0.3s ease;
        }
        .voice-bar-listening-0 { animation: voiceWave 1s ease-in-out infinite; animation-delay: 0.1s; }
        .voice-bar-listening-1 { animation: voiceWave 1s ease-in-out infinite; animation-delay: 0.25s; }
        .voice-bar-listening-2 { animation: voiceWave 1s ease-in-out infinite; animation-delay: 0.4s; }
        .voice-bar-listening-3 { animation: voiceWave 1s ease-in-out infinite; animation-delay: 0.25s; }
        .voice-bar-listening-4 { animation: voiceWave 1s ease-in-out infinite; animation-delay: 0.1s; }

        .voice-bar-processing {
          animation: voiceProcessing 1.5s ease-in-out infinite;
          background-color: var(--bs-info, #0dcaf0);
        }
        .voice-bar-processing-0 { animation-delay: 0.1s; }
        .voice-bar-processing-1 { animation-delay: 0.3s; }
        .voice-bar-processing-2 { animation-delay: 0.5s; }
        .voice-bar-processing-3 { animation-delay: 0.7s; }
        .voice-bar-processing-4 { animation-delay: 0.9s; }

        .voice-bar-error {
          background-color: var(--bs-danger, #dc3545);
          transform: scaleY(0.15);
        }
        .voice-bar-idle {
          background-color: var(--bs-gray-400, #ced4da);
          transform: scaleY(0.2);
        }
        @media (prefers-reduced-motion: reduce) {
          .voice-bar {
            animation: none !important;
            transform: scaleY(0.3) !important;
            opacity: 1 !important;
          }
        }
      `}</style>
      
      {bars.map((_, index) => {
        let barClass = 'voice-bar-idle';
        if (isListening) {
          barClass = `voice-bar-listening-${index}`;
        } else if (isProcessing) {
          barClass = `voice-bar-processing voice-bar-processing-${index}`;
        } else if (isError) {
          barClass = 'voice-bar-error';
        }

        return (
          <div 
            key={index} 
            className={`voice-bar ${barClass}`}
            data-testid={`voice-bar-${index}`}
          />
        );
      })}
    </div>
  );
};
export default VoiceVisualizer;
