import React from 'react';
import { Mic, Activity, Loader2 } from 'lucide-react';

export default function VoiceButton({ status, onClick }) {
  const isListening = status === 'listening';
  const isProcessing = status === 'processing';
  
  return (
    <div className="voice-button-container glass-panel">
      <div className="pulse-wrapper">
        {/* Animated Background Pulse Ripple rings when listening */}
        {isListening && (
          <>
            <div className="pulse-ring ring-1" />
            <div className="pulse-ring ring-2" />
            <div className="pulse-ring ring-3" />
          </>
        )}
        
        <button
          onClick={isProcessing || isListening ? undefined : onClick}
          disabled={isProcessing}
          className={`mic-trigger-btn ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''}`}
          title={isListening ? 'Listening...' : isProcessing ? 'Processing...' : 'Click to say command'}
        >
          {isProcessing ? (
            <Loader2 className="spinner-icon" size={32} />
          ) : isListening ? (
            <Mic className="mic-icon animate-pop" size={32} />
          ) : (
            <Mic className="mic-icon" size={32} />
          )}
        </button>
      </div>

      <div className="waveform-container">
        {isListening ? (
          <div className="waveform">
            <span className="wave-bar bar-1"></span>
            <span className="wave-bar bar-2"></span>
            <span className="wave-bar bar-3"></span>
            <span className="wave-bar bar-4"></span>
            <span className="wave-bar bar-5"></span>
            <span className="wave-bar bar-6"></span>
            <span className="wave-bar bar-7"></span>
          </div>
        ) : isProcessing ? (
          <div className="processing-text">
            <span>Analyzing speech...</span>
          </div>
        ) : (
          <div className="idle-text">
            <span>Click the mic to speak a command</span>
          </div>
        )}
      </div>

      <style>{`
        .voice-button-container {
          padding: 2rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 1.5rem;
          min-height: 250px;
        }

        .pulse-wrapper {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 140px;
          height: 140px;
        }

        .mic-trigger-btn {
          width: 100px;
          height: 100px;
          border-radius: 50%;
          border: none;
          background: linear-gradient(135deg, var(--accent-violet) 0%, #6d28d9 100%);
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 32px 0 rgba(139, 92, 246, 0.4);
          transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          z-index: 5;
          position: relative;
        }

        .mic-trigger-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 12px 40px 0 rgba(139, 92, 246, 0.6);
          background: linear-gradient(135deg, #9d6eff 0%, #7c3aed 100%);
        }

        .mic-trigger-btn:active {
          transform: scale(0.95);
        }

        .mic-trigger-btn.listening {
          background: linear-gradient(135deg, var(--accent-rose) 0%, #be123c 100%);
          box-shadow: 0 0 40px 10px rgba(244, 63, 94, 0.5);
          animation: pulse-glow-listening 2s infinite;
        }

        .mic-trigger-btn.processing {
          background: linear-gradient(135deg, var(--bg-secondary) 0%, #1e293b 100%);
          box-shadow: none;
          border: 2px solid var(--glass-border);
          cursor: not-allowed;
        }

        .mic-icon {
          transition: var(--transition-smooth);
        }

        .spinner-icon {
          animation: spin-slow 1.2s linear infinite;
          color: var(--accent-violet);
        }

        .animate-pop {
          animation: pop-icon 0.3s ease-out;
        }

        @keyframes pop-icon {
          0% { transform: scale(0.7); }
          100% { transform: scale(1); }
        }

        /* Pulse Rings */
        .pulse-ring {
          position: absolute;
          width: 100px;
          height: 100px;
          border-radius: 50%;
          background-color: var(--accent-rose);
          opacity: 0;
          z-index: 1;
          pointer-events: none;
        }

        .ring-1 {
          animation: ripple-pulse 2s cubic-bezier(0.1, 0.8, 0.3, 1) infinite;
        }

        .ring-2 {
          animation: ripple-pulse 2s cubic-bezier(0.1, 0.8, 0.3, 1) infinite;
          animation-delay: 0.6s;
        }

        .ring-3 {
          animation: ripple-pulse 2s cubic-bezier(0.1, 0.8, 0.3, 1) infinite;
          animation-delay: 1.2s;
        }

        @keyframes ripple-pulse {
          0% {
            transform: scale(1);
            opacity: 0.6;
          }
          100% {
            transform: scale(2.2);
            opacity: 0;
          }
        }

        /* Soundwave */
        .waveform-container {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 24px;
          width: 100%;
        }

        .waveform {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          height: 20px;
        }

        .wave-bar {
          width: 3px;
          height: 100%;
          background-color: var(--accent-rose);
          border-radius: var(--radius-full);
          animation: soundwave-bar 1.2s ease-in-out infinite;
        }

        .bar-1 { animation-delay: 0.1s; }
        .bar-2 { animation-delay: 0.3s; }
        .bar-3 { animation-delay: 0.5s; }
        .bar-4 { animation-delay: 0.2s; }
        .bar-5 { animation-delay: 0.4s; }
        .bar-6 { animation-delay: 0.6s; }
        .bar-7 { animation-delay: 0.15s; }

        .idle-text, .processing-text {
          font-size: 0.85rem;
          color: var(--text-secondary);
          text-align: center;
        }

        .processing-text span {
          color: var(--accent-amber);
          font-weight: 500;
        }
      `}</style>
    </div>
  );
}
