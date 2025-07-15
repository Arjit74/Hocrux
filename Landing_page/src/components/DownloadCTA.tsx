import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { 
  Chrome, 
  Download, 
  Github, 
  Star,
  Users,
  Shield
} from "lucide-react";

export default function DownloadCTA() {
  return (
    <section className="py-24 px-6 bg-gradient-hero relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-20 w-32 h-32 bg-gradient-primary rounded-full opacity-20 animate-float"></div>
        <div className="absolute bottom-20 right-20 w-24 h-24 bg-gradient-secondary rounded-full opacity-30 animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute top-1/2 left-10 w-16 h-16 bg-accent rounded-full opacity-25 animate-float" style={{ animationDelay: '4s' }}></div>
      </div>
      
      <div className="max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-12">
          <Badge className="mb-6 bg-gradient-primary text-white border-none animate-pulse-glow">
            🚀 Ready to Launch
          </Badge>
          
          <h2 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-white via-primary to-accent bg-clip-text text-transparent">
            Get SignBridge Today
          </h2>
          
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Join thousands of users making their video calls more accessible. 
            Install SignBridge and start breaking communication barriers today.
          </p>
        </div>
        
        {/* Download Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Chrome Web Store */}
          <Card className="bg-gradient-card border-border/50 hover:shadow-hero transition-smooth group">
            <CardContent className="p-8 text-center">
              <div className="w-20 h-20 bg-gradient-primary rounded-3xl flex items-center justify-center mx-auto mb-6 group-hover:shadow-glow transition-smooth">
                <Chrome className="h-10 w-10 text-white" />
              </div>
              
              <h3 className="text-2xl font-semibold mb-4 text-foreground">
                Chrome Extension
              </h3>
              
              <p className="text-muted-foreground mb-6 leading-relaxed">
                One-click installation from the Chrome Web Store. Works immediately with Google Meet, Zoom Web, and Microsoft Teams.
              </p>
              
              <Button variant="chrome" size="lg" className="w-full text-lg py-4 h-auto group-hover:scale-105 transition-smooth">
                <Chrome className="mr-3 h-6 w-6" />
                Add to Chrome - Free
              </Button>
              
              <div className="flex justify-center gap-6 mt-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 text-yellow-400" />
                  4.9/5 Rating
                </div>
                <div className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  10K+ Users
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* GitHub Repository */}
          <Card className="bg-gradient-card border-border/50 hover:shadow-hero transition-smooth group">
            <CardContent className="p-8 text-center">
              <div className="w-20 h-20 bg-gradient-secondary rounded-3xl flex items-center justify-center mx-auto mb-6 group-hover:shadow-glow transition-smooth">
                <Github className="h-10 w-10 text-white" />
              </div>
              
              <h3 className="text-2xl font-semibold mb-4 text-foreground">
                Open Source
              </h3>
              
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Explore the code, contribute to development, or build your own version. SignBridge is open source and community-driven.
              </p>
              
              <Button variant="glow" size="lg" className="w-full text-lg py-4 h-auto group-hover:scale-105 transition-smooth">
                <Github className="mr-3 h-6 w-6" />
                View on GitHub
              </Button>
              
              <div className="flex justify-center gap-6 mt-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 text-yellow-400" />
                  500+ Stars
                </div>
                <div className="flex items-center gap-1">
                  <Shield className="h-4 w-4" />
                  MIT License
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Features Highlight */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="p-6">
            <div className="w-12 h-12 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <h4 className="font-semibold text-foreground mb-2">Privacy First</h4>
            <p className="text-sm text-muted-foreground">All processing happens locally. No data leaves your device.</p>
          </div>
          
          <div className="p-6">
            <div className="w-12 h-12 bg-gradient-secondary rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Download className="h-6 w-6 text-white" />
            </div>
            <h4 className="font-semibold text-foreground mb-2">Easy Setup</h4>
            <p className="text-sm text-muted-foreground">Install in seconds, works immediately with all major video platforms.</p>
          </div>
          
          <div className="p-6">
            <div className="w-12 h-12 bg-accent rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Users className="h-6 w-6 text-white" />
            </div>
            <h4 className="font-semibold text-foreground mb-2">Community Driven</h4>
            <p className="text-sm text-muted-foreground">Built by the community, for the community. Join us in making communication accessible.</p>
          </div>
        </div>
      </div>
    </section>
  );
}