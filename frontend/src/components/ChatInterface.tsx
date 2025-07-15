import { useState, useRef, useEffect } from 'react';
import { ChatHeader } from './ChatHeader';
import { ChatMessage } from './ChatMessage';
import ChatInput from './ChatInput';
import { Button } from '@/components/ui/button';
import { RotateCcw, Sparkles } from 'lucide-react';
import { greetings } from '@/lib/greetings';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
  language?: string;
  englishText?: string;
  audioUrl?: string;
}

export function ChatInterface() {
  const defaultLang = 'en';
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: greetings[defaultLang],
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      language: defaultLang,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);
    // http://localhost:8000
    fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: content }),
    })
      .then((res) => res.json())
      .then((data) => {
        const botMessage: Message = {
          id: Date.now().toString(),
          content: data.response,
          englishText: data.english_response,
          audioUrl: data.audio_url,
          isUser: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          language: data.language || 'en',
        };
        setMessages((prev) => [...prev, botMessage]);
      })
      .catch((err) => {
        console.error("❌ Error:", err);
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: "❌ Failed to connect to AgriBot backend.",
          isUser: false,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          language: 'en',
        };
        setMessages((prev) => [...prev, errorMessage]);
      })
      .finally(() => {
        setIsTyping(false);
      });
  };

  const handleSendAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");
      // http://localhost:8000
      const res = await fetch("http://localhost:8000/speech-to-text", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Speech-to-text failed.");

      const transcription = data.transcription;
      if (transcription) handleSendMessage(transcription);
      else alert("Could not transcribe your voice.");
    } catch (error) {
      console.error("❌ Voice processing error:", error);
      alert("❌ Error transcribing audio.");
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        content: greetings[defaultLang],
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        language: defaultLang,
      },
    ]);
  };

  const suggestedQuestions = [
    "How do I improve soil fertility naturally?",
    "What's the best time to plant tomatoes?",
    "How can I control aphids organically?",
    "What are signs of nutrient deficiency in plants?",
  ];

  return (
    <div className="h-screen flex flex-col bg-gradient-background">
      <ChatHeader />
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message.content}
                isUser={message.isUser}
                timestamp={message.timestamp}
                language={message.language}
                englishText={message.englishText}
                audioUrl={message.audioUrl}
              />
            ))}
            {isTyping && (
              <div className="flex justify-start mb-4 animate-fade-in">
                <div className="bg-bot-message text-bot-message-foreground rounded-2xl px-4 py-3 shadow-message">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-primary-foreground font-semibold text-sm">🌱</div>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {messages.length === 1 && !isTyping && (
              <div className="mt-6 animate-fade-in">
                <p className="text-sm text-muted-foreground mb-3 text-center">
                  <Sparkles className="inline h-4 w-4 mr-1" />
                  Try asking about:
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {suggestedQuestions.map((q, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      size="sm"
                      onClick={() => handleSendMessage(q)}
                      className="text-left h-auto p-3"
                    >
                      {q}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input + Clear */}
      {messages.length > 1 && (
        <div className="px-4 pb-2">
          <div className="max-w-4xl mx-auto flex justify-center">
            <Button variant="ghost" size="sm" onClick={clearChat}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Clear Chat
            </Button>
          </div>
        </div>
      )}

      <ChatInput onSendMessage={handleSendMessage} onSendAudio={handleSendAudio} disabled={isTyping} />
    </div>
  );
}
