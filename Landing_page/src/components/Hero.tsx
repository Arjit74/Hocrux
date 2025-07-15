import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Chrome, Play, Download } from "lucide-react";
import heroImage from "@/assets/hero-hands.jpg";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-hero">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <img 
          src={heroImage} 
          alt="Sign language gestures in 3D" 
          className="w-full h-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background/80 to-background/40"></div>
      </div>
      
      {/* Floating Elements */}
      <div className="absolute top-20 left-10 animate-float">
        <div className="w-16 h-16 bg-gradient-primary rounded-full shadow-glow opacity-60"></div>
      </div>
      <div className="absolute bottom-20 right-10 animate-float" style={{ animationDelay: '2s' }}>
        <div className="w-12 h-12 bg-gradient-secondary rounded-full shadow-glow opacity-40"></div>
      </div>
      <div className="absolute top-40 right-20 animate-float" style={{ animationDelay: '4s' }}>
        <div className="w-8 h-8 bg-accent rounded-full shadow-glow opacity-50"></div>
      </div>
      
      {/* Main Content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto px-6">
        <Badge className="mb-6 bg-gradient-secondary text-white border-none animate-pulse-glow">
          🚀 Chrome Extension • Real-Time Translation
        </Badge>
        
        <h1 className="text-6xl md:text-8xl font-bold mb-6 bg-gradient-to-r from-white via-primary to-accent bg-clip-text text-transparent leading-tight">
          SignBridge
        </h1>
        
        <p className="text-xl md:text-2xl text-muted-foreground mb-4 font-light">
          Real-Time Sign Language Translator
        </p>
        
        <p className="text-lg md:text-xl text-muted-foreground mb-12 max-w-3xl mx-auto leading-relaxed">
          Break communication barriers in online meetings. Our Chrome extension translates sign language to text and speech in real-time during Google Meet, Zoom, and Microsoft Teams calls.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
          <Button variant="chrome" size="lg" className="text-lg px-8 py-4 h-auto">
            <Chrome className="mr-3 h-6 w-6" />
            Add to Chrome
          </Button>
          
          <Button variant="glow" size="lg" className="text-lg px-8 py-4 h-auto">
            <Play className="mr-3 h-6 w-6" />
            Watch Demo
          </Button>
        </div>
        
        <div className="mt-12 flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary rounded-full"></div>
            Google Meet
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-accent rounded-full"></div>
            Zoom Web
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary rounded-full"></div>
            Microsoft Teams Web
          </div>
        </div>
      </div>
      
      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <div className="w-6 h-10 border-2 border-primary rounded-full flex justify-center">
          <div className="w-1 h-3 bg-primary rounded-full mt-2 animate-pulse"></div>
        </div>
      </div>
    </section>
  );
}