import { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Volume2, Languages } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp?: string;
  language?: string;
  englishText?: string;
  audioUrl?: string;
}

export function ChatMessage({
  message,
  isUser,
  timestamp,
  language,
  englishText,
  audioUrl,
}: ChatMessageProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showEnglish, setShowEnglish] = useState(false);
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [translatedGreeting, setTranslatedGreeting] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayAudio = () => {
    if (!audioUrl) return;

    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    audio.play();

    setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => setIsPlaying(false);
  };

  const handleTranslateToggle = () => {
    setShowEnglish((prev) => !prev);
  };

  const handleTranslateGreeting = async (targetLang: string) => {
    try {
      const res = await fetch(
        `http://localhost:8000/translate-from-english?text=${encodeURIComponent(
          message
        )}&target_lang=${targetLang}`
      );
      const data = await res.json();
      if (data.translated_text) {
        setTranslatedGreeting(data.translated_text);
        setShowLangDropdown(false);
      }
    } catch (err) {
      alert('❌ Translation failed');
    }
  };

  return (
    <div
      className={cn(
        'flex w-full mb-4 animate-fade-in',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[70%] rounded-2xl px-4 py-3 shadow-message transition-all duration-300 hover:shadow-elegant relative',
          isUser
            ? 'bg-user-message text-user-message-foreground animate-slide-in-right ml-auto'
            : 'bg-bot-message text-bot-message-foreground animate-slide-in-left'
        )}
      >
        <div className="flex items-start gap-2">
          {!isUser && (
            <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-primary-foreground font-semibold text-sm shrink-0">
              🌱
            </div>
          )}
          <div className="flex-1">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {translatedGreeting || (showEnglish && englishText) || message}
            </p>
            {timestamp && <p className="text-xs opacity-70 mt-1">{timestamp}</p>}
          </div>
        </div>

        {/* Controls only for bot messages */}
        {!isUser && (
          <div className="flex gap-2 mt-3 pt-2 border-t border-border/20">
            {/* 🔊 Speaker Button */}
            {audioUrl && (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={handlePlayAudio}
                className={cn(
                  'hover:bg-primary/10 hover:text-primary transition-all',
                  isPlaying && 'animate-bounce-gentle'
                )}
                title={isPlaying ? 'Stop voice' : 'Play voice'}
              >
                <Volume2 className="h-4 w-4" />
              </Button>
            )}

            {/* 🌐 Translate Button */}
            {englishText ? (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={handleTranslateToggle}
                className="hover:bg-accent/10 hover:text-accent transition-all"
                title="Translate to English"
              >
                <Languages className="h-4 w-4" />
              </Button>
            ) : (
              message.length > 100 && (
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => setShowLangDropdown((prev) => !prev)}
                    className="hover:bg-accent/10 hover:text-accent transition-all"
                    title="Translate"
                  >
                    <Languages className="h-4 w-4" />
                  </Button>
                  {showLangDropdown && (
                    <div className="absolute bottom-full mb-2 left-0 z-10 bg-white border rounded shadow-lg w-40">
                      {[
                        { code: 'hi', name: 'Hindi' },
                        { code: 'bn', name: 'Bengali' },
                        { code: 'te', name: 'Telugu' },
                        { code: 'mr', name: 'Marathi' },
                        { code: 'ta', name: 'Tamil' },
                        { code: 'gu', name: 'Gujarati' },
                        { code: 'kn', name: 'Kannada' },
                        { code: 'ml', name: 'Malayalam' },
                        { code: 'pa', name: 'Punjabi' },
                      ].map((lang) => (
                        <button
                          key={lang.code}
                          onClick={() => handleTranslateGreeting(lang.code)}
                          className="w-full px-4 py-2 text-left hover:bg-gray-100"
                        >
                          {lang.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}
