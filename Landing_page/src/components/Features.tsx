import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Video, 
  Hand, 
  MessageSquare, 
  Volume2, 
  Chrome, 
  Layers3,
  FileText,
  Globe
} from "lucide-react";
import featuresImage from "@/assets/features-grid.jpg";

const features = [
  {
    icon: Video,
    title: "Live Webcam Detection",
    description: "Real-time sign language capture using advanced computer vision and MediaPipe technology.",
    color: "bg-gradient-primary"
  },
  {
    icon: Hand,
    title: "Gesture Recognition",
    description: "AI-powered hand gesture analysis with 95%+ accuracy for common sign language expressions.",
    color: "bg-gradient-secondary"
  },
  {
    icon: MessageSquare,
    title: "Instant Text Translation",
    description: "Seamless conversion of sign language to readable text displayed as overlay during calls.",
    color: "bg-gradient-primary"
  },
  {
    icon: Volume2,
    title: "Text-to-Speech",
    description: "Optional voice synthesis so other participants can hear the translated sign language.",
    color: "bg-gradient-secondary"
  },
  {
    icon: Chrome,
    title: "One-Click Extension",
    description: "Simple Chrome extension that works across Google Meet, Zoom Web, and MS Teams.",
    color: "bg-gradient-primary"
  },
  {
    icon: Layers3,
    title: "Modern 3D Interface",
    description: "Beautiful, non-intrusive overlay that enhances rather than disrupts your video calls.",
    color: "bg-gradient-secondary"
  },
  {
    icon: FileText,
    title: "Sign Log History",
    description: "Optional conversation logging to review important meeting translations later.",
    color: "bg-gradient-primary"
  },
  {
    icon: Globe,
    title: "Multi-language TTS",
    description: "Text-to-speech support in multiple languages for global accessibility.",
    color: "bg-gradient-secondary"
  }
];

export default function Features() {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-background to-secondary/20">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <Badge className="mb-6 bg-accent text-white border-none">
            ✨ Core Features
          </Badge>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Powerful Features for
            <br />
            Seamless Communication
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            SignBridge combines cutting-edge AI technology with intuitive design to make sign language accessible to everyone in digital meetings.
          </p>
        </div>
        
        {/* Feature Image */}
        <div className="mb-16 relative">
          <img 
            src={featuresImage} 
            alt="SignBridge features visualization" 
            className="w-full max-w-4xl mx-auto rounded-2xl shadow-hero"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent rounded-2xl"></div>
        </div>
        
        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="group bg-gradient-card border-border/50 hover:shadow-card transition-smooth hover:scale-105"
            >
              <CardContent className="p-8 text-center">
                <div className={`w-16 h-16 ${feature.color} rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:shadow-glow transition-smooth`}>
                  <feature.icon className="h-8 w-8 text-white" />
                </div>
                
                <h3 className="text-xl font-semibold mb-4 text-foreground">
                  {feature.title}
                </h3>
                
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}