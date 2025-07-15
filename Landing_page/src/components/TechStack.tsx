import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const technologies = [
  {
    name: "MediaPipe",
    description: "Hand gesture detection",
    logo: "🤲",
    category: "AI/ML"
  },
  {
    name: "TensorFlow.js",
    description: "Machine learning inference",
    logo: "🧠", 
    category: "AI/ML"
  },
  {
    name: "Chrome Extensions",
    description: "Cross-platform integration",
    logo: "🌐",
    category: "Platform"
  },
  {
    name: "WebRTC",
    description: "Real-time video processing",
    logo: "📹",
    category: "Video"
  },
  {
    name: "Three.js",
    description: "3D interface elements",
    logo: "🎯",
    category: "UI/UX"
  },
  {
    name: "Web Speech API",
    description: "Text-to-speech synthesis",
    logo: "🔊",
    category: "Audio"
  },
  {
    name: "JavaScript",
    description: "Core application logic",
    logo: "⚡",
    category: "Language"
  },
  {
    name: "CSS3",
    description: "Modern styling & animations",
    logo: "🎨",
    category: "Styling"
  }
];

const categories = ["AI/ML", "Platform", "Video", "Audio", "UI/UX", "Language", "Styling"];
const categoryColors = {
  "AI/ML": "bg-gradient-primary",
  "Platform": "bg-gradient-secondary", 
  "Video": "bg-accent",
  "Audio": "bg-primary",
  "UI/UX": "bg-gradient-primary",
  "Language": "bg-gradient-secondary",
  "Styling": "bg-accent"
};

export default function TechStack() {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-background to-secondary/20">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <Badge className="mb-6 bg-gradient-secondary text-white border-none">
            ⚙️ Technology Stack
          </Badge>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Built with Cutting-Edge
            <br />
            Web Technologies
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            SignBridge leverages the latest in AI, web APIs, and browser technologies to deliver a seamless real-time translation experience.
          </p>
        </div>
        
        {/* Tech Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {technologies.map((tech, index) => (
            <Card 
              key={index}
              className="group bg-gradient-card border-border/50 hover:shadow-card transition-smooth hover:scale-105 hover:rotate-1"
            >
              <CardContent className="p-6 text-center">
                <div className="text-4xl mb-4 group-hover:scale-110 transition-smooth">
                  {tech.logo}
                </div>
                
                <h3 className="text-lg font-semibold mb-2 text-foreground">
                  {tech.name}
                </h3>
                
                <p className="text-sm text-muted-foreground mb-4">
                  {tech.description}
                </p>
                
                <Badge 
                  className={`${categoryColors[tech.category as keyof typeof categoryColors]} text-white text-xs border-none`}
                >
                  {tech.category}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {/* Category Legend */}
        <div className="mt-16 flex flex-wrap justify-center gap-4">
          {categories.map((category) => (
            <div key={category} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${categoryColors[category as keyof typeof categoryColors]}`}></div>
              <span className="text-sm text-muted-foreground">{category}</span>
            </div>
          ))}
        </div>
        
        {/* Open Source Note */}
        <div className="mt-16 text-center">
          <Card className="max-w-2xl mx-auto bg-gradient-card border-border/50">
            <CardContent className="p-8">
              <h3 className="text-xl font-semibold mb-4 text-foreground">
                🌟 Open Source Project
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                SignBridge is built with open web standards and will be available on GitHub. 
                We believe in accessible technology that everyone can contribute to and improve.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}