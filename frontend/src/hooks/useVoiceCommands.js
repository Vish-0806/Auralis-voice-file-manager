import { useState, useEffect, useCallback, useRef } from 'react';
import * as api from '../services/api';

export function useVoiceCommands() {
  const [listenerActive, setListenerActive] = useState(false);
  const [status, setStatus] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'success' | 'error'
  const [lastMessage, setLastMessage] = useState('Welcome! How can I help you?');
  const [pendingAction, setPendingAction] = useState(null); // { message, rawAction } or null
  const [searchResults, setSearchResults] = useState([]);
  const [history, setHistory] = useState([]);
  
  const pollingRef = useRef(null);

  // Sync listener status from backend
  const syncListenerStatus = useCallback(async () => {
    try {
      const data = await api.getListenerStatus();
      setListenerActive(data.running);
    } catch (error) {
      console.error('Failed to sync listener status:', error);
    }
  }, []);

  // Poll listener status periodically
  useEffect(() => {
    syncListenerStatus();
    
    pollingRef.current = setInterval(syncListenerStatus, 3000);
    
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [syncListenerStatus]);

  // Helper to add commands/results to history list
  const addToHistory = useCallback((type, command, apiResult, isError = false) => {
    const timestamp = new Date();
    const id = Date.now();
    
    let outcome = 'success';
    let summaryMessage = '';
    let parsedAction = null;
    let searchHits = [];

    if (isError) {
      outcome = 'error';
      summaryMessage = apiResult?.message || apiResult || 'An unexpected error occurred';
    } else {
      parsedAction = apiResult?.parsed_action;
      const resVal = apiResult?.result;

      // Extract result messages based on FastAPI structures
      if (resVal && typeof resVal === 'object') {
        if (resVal.status === 'pending_confirmation') {
          outcome = 'pending_confirmation';
          summaryMessage = resVal.message;
        } else if (resVal.status === 'success') {
          summaryMessage = resVal.message || 'Operation succeeded';
        } else if (resVal.results) {
          // Search results
          outcome = 'success';
          summaryMessage = `Found ${resVal.count} file(s)`;
          searchHits = resVal.results;
        } else if (resVal.status === 'error') {
          outcome = 'error';
          summaryMessage = resVal.message || 'Operation failed';
        } else {
          summaryMessage = JSON.stringify(resVal);
        }
      } else {
        summaryMessage = resVal || 'Command executed';
      }
      
      if (apiResult?.status === 'ignored') {
        outcome = 'ignored';
        summaryMessage = apiResult.message || 'Wake word not detected';
      } else if (apiResult?.status === 'awaiting_command') {
        outcome = 'awaiting_command';
        summaryMessage = apiResult.message || 'Awaiting command...';
      }
    }

    setHistory((prev) => [
      {
        id,
        timestamp,
        type,
        command: command || '(Audio Command)',
        outcome,
        action: parsedAction?.action || 'unknown',
        target: parsedAction?.target || '',
        destination: parsedAction?.destination || parsedAction?.location || '',
        summaryMessage,
      },
      ...prev,
    ]);

    // If search files were returned, update search results state
    if (searchHits.length > 0) {
      setSearchResults(searchHits);
    }

    return { outcome, summaryMessage, parsedAction };
  }, []);

  // Submit a text-based command
  const submitTextCommand = useCallback(async (commandText) => {
    if (!commandText || !commandText.trim()) return;
    
    setStatus('processing');
    setLastMessage('Processing command...');
    
    try {
      const result = await api.sendCommand(commandText);
      
      const { outcome, summaryMessage } = addToHistory('text', commandText, result);
      
      if (outcome === 'pending_confirmation') {
        setPendingAction({
          message: summaryMessage,
          rawAction: result.result.pending_action,
        });
        setStatus('idle');
      } else {
        setPendingAction(null);
        setStatus('success');
        setLastMessage(summaryMessage);
      }
    } catch (error) {
      setStatus('error');
      const errorMsg = error.message || 'Failed to process command';
      setLastMessage(errorMsg);
      addToHistory('text', commandText, errorMsg, true);
    }
  }, [addToHistory]);

  // Triggers one-off microphone listening on the backend
  const triggerVoiceListen = useCallback(async () => {
    setStatus('listening');
    setLastMessage('Listening to microphone...');
    
    try {
      const result = await api.triggerVoiceListen();
      
      // If voice request completed
      const recognized = result.recognized_text || result.command;
      const { outcome, summaryMessage } = addToHistory('voice', recognized, result);
      
      if (outcome === 'pending_confirmation') {
        setPendingAction({
          message: summaryMessage,
          rawAction: result.result.pending_action,
        });
        setStatus('idle');
      } else if (outcome === 'ignored') {
        setStatus('idle');
        setLastMessage(result.message || 'Wake word not detected.');
      } else if (outcome === 'awaiting_command') {
        setStatus('listening');
        setLastMessage('Awaiting command... Say something.');
      } else {
        setPendingAction(null);
        setStatus('success');
        setLastMessage(summaryMessage);
      }
    } catch (error) {
      setStatus('error');
      const errorMsg = error.message || 'Failed to capture voice command';
      setLastMessage(errorMsg);
      addToHistory('voice', null, errorMsg, true);
    }
  }, [addToHistory]);

  // Confirm or cancel a pending action
  const respondToConfirmation = useCallback(async (agree) => {
    if (!pendingAction) return;
    
    const commandText = agree ? 'yes' : 'no';
    await submitTextCommand(commandText);
  }, [pendingAction, submitTextCommand]);

  // Start or Stop continuous background listener
  const toggleContinuousListener = useCallback(async () => {
    const nextState = !listenerActive;
    setStatus('processing');
    
    try {
      if (nextState) {
        await api.startListener();
        setListenerActive(true);
        setLastMessage('Continuous voice listener started in background. Say the wake word to control files.');
      } else {
        await api.stopListener();
        setListenerActive(false);
        setLastMessage('Continuous voice listener stopped.');
      }
      setStatus('success');
    } catch (error) {
      setStatus('error');
      setLastMessage(error.message || 'Failed to update listener state');
    }
  }, [listenerActive]);

  // Clear states
  const clearHistory = useCallback(() => setHistory([]), []);
  const clearSearchResults = useCallback(() => setSearchResults([]), []);

  return {
    listenerActive,
    status,
    lastMessage,
    pendingAction,
    searchResults,
    history,
    triggerVoiceListen,
    submitTextCommand,
    respondToConfirmation,
    toggleContinuousListener,
    clearHistory,
    clearSearchResults,
    setSearchResults,
  };
}
