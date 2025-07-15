import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Mic, MicOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onSendAudio: (audioBlob: Blob) => void;
  disabled?: boolean;
}

const ChatInput = ({ onSendMessage, onSendAudio, disabled }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        onSendAudio(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('🎤 Microphone access error:', error);
      alert('❌ Unable to access microphone. Please check your browser settings.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const toggleRecording = () => {
    isRecording ? stopRecording() : startRecording();
  };

  useEffect(() => {
    return () => {
      if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
      }
    };
  }, [mediaRecorder, isRecording]);

  return (
    <div className="border-t border-border bg-card/80 backdrop-blur-sm p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-3 items-end">
          {/* Voice Recording Button */}
          <Button
            variant={isRecording ? "destructive" : "voice"}
            size="icon"
            onClick={toggleRecording}
            disabled={disabled}
            className={cn("shrink-0 shadow-input", isRecording && "animate-bounce-gentle")}
            title={isRecording ? "Stop recording" : "Start voice recording"}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about agriculture..."
              disabled={disabled || isRecording}
              className={cn(
                "pr-12 rounded-2xl border-2 shadow-input",
                "focus:border-primary focus:shadow-elegant transition-all duration-300",
                "bg-background/90 backdrop-blur-sm"
              )}
            />

            {/* Send Button */}
            <Button
              variant="send"
              size="icon-sm"
              onClick={handleSend}
              disabled={!message.trim() || disabled || isRecording}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl"
              title="Send message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="mt-3 flex items-center justify-center gap-2 text-destructive animate-fade-in">
            <div className="w-2 h-2 bg-destructive rounded-full animate-ping"></div>
            <span className="text-sm font-medium">Recording audio...</span>
          </div>
        )}

        {/* Helpful Hint */}
        <div className="mt-2 text-center">
          <p className="text-xs text-muted-foreground">
            Press Enter to send • Click mic to record voice • Get answers in any language
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
