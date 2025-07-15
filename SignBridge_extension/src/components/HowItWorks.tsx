import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Camera, 
  Brain, 
  MessageSquare, 
  ArrowRight,
  Play
} from "lucide-react";
import demoImage from "@/assets/demo-interface.jpg";

const steps = [
  {
    number: "01",
    icon: Camera,
    title: "Sign Detection",
    description: "User makes sign language gestures in front of their webcam during a video call.",
    color: "bg-gradient-primary"
  },
  {
    number: "02", 
    icon: Brain,
    title: "AI Processing",
    description: "Our MediaPipe-powered AI analyzes hand movements and recognizes sign language patterns in real-time.",
    color: "bg-gradient-secondary"
  },
  {
    number: "03",
    icon: MessageSquare,
    title: "Translation Output",
    description: "Translated text appears as overlay on the video call, with optional text-to-speech for other participants.",
    color: "bg-accent"
  }
];

export default function HowItWorks() {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-secondary/20 to-background">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <Badge className="mb-6 bg-gradient-primary text-white border-none">
            🔬 How It Works
          </Badge>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Three Simple Steps to
            <br />
            Break Communication Barriers
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            SignBridge works seamlessly in the background, providing real-time translation without interrupting your video call experience.
          </p>
        </div>
        
        {/* Steps Process */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              <Card className="group bg-gradient-card border-border/50 hover:shadow-card transition-smooth hover:scale-105 h-full">
                <CardContent className="p-8 text-center">
                  <div className="relative mb-6">
                    <div className={`w-20 h-20 ${step.color} rounded-3xl flex items-center justify-center mx-auto group-hover:shadow-glow transition-smooth`}>
                      <step.icon className="h-10 w-10 text-white" />
                    </div>
                    <div className="absolute -top-4 -right-4 w-12 h-12 bg-foreground text-background rounded-full flex items-center justify-center text-lg font-bold">
                      {step.number}
                    </div>
                  </div>
                  
                  <h3 className="text-2xl font-semibold mb-4 text-foreground">
                    {step.title}
                  </h3>
                  
                  <p className="text-muted-foreground leading-relaxed">
                    {step.description}
                  </p>
                </CardContent>
              </Card>
              
              {/* Arrow between steps */}
              {index < steps.length - 1 && (
                <div className="hidden lg:flex absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center shadow-glow">
                    <ArrowRight className="h-4 w-4 text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Demo Video Section */}
        <div className="relative rounded-3xl overflow-hidden shadow-hero max-w-5xl mx-auto">
          <img 
            src={demoImage} 
            alt="SignBridge demo interface" 
            className="w-full h-auto"
          />
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center group cursor-pointer hover:bg-black/30 transition-smooth">
            <Button variant="hero" size="lg" className="text-2xl px-12 py-6 h-auto group-hover:scale-110 transition-bounce">
              <Play className="mr-4 h-8 w-8" />
              Watch Live Demo
            </Button>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <p className="text-muted-foreground">
            See SignBridge in action with a real video call scenario
          </p>
        </div>
      </div>
    </section>
  );
}