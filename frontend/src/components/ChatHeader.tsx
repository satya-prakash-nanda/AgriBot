import { Sprout } from 'lucide-react';

export function ChatHeader() {
  return (
    <header className="border-b border-border bg-gradient-background shadow-elegant">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-elegant">
            <Sprout className="h-6 w-6 text-primary-foreground" />
          </div>
          
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              AgriBot Assistant
            </h1>
            <p className="text-muted-foreground">
              Your AI-powered agricultural companion
            </p>
          </div>
        </div>
        
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full border border-primary/20">
            🌾 Crop Management
          </span>
          <span className="px-3 py-1 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">
            ☀️ Weather Forecast
          </span>
          <span className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full border border-primary/20">
            🚜 Equipment Advice
          </span>
          <span className="px-3 py-1 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">
            📊 Mandi Prices
          </span>
          <span className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full border border-primary/20">
            🏛️ Government Schemes
          </span>
        </div>
      </div>
    </header>
  );
}