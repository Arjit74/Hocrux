import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Github, 
  Twitter, 
  Mail, 
  Heart,
  ExternalLink
} from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="py-16 px-6 bg-secondary/30 border-t border-border/50">
      <div className="max-w-7xl mx-auto">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Section */}
          <div className="md:col-span-2">
            <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              SignBridge
            </h3>
            <p className="text-muted-foreground mb-6 leading-relaxed max-w-md">
              Real-time sign language translation for video calls. Breaking communication barriers with cutting-edge AI technology.
            </p>
            <div className="flex gap-4">
              <Button variant="ghost" size="icon" className="hover:bg-primary/20 hover:text-primary">
                <Github className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-primary/20 hover:text-primary">
                <Twitter className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon" className="hover:bg-primary/20 hover:text-primary">
                <Mail className="h-5 w-5" />
              </Button>
            </div>
          </div>
          
          {/* Quick Links */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Product</h4>
            <ul className="space-y-3">
              <li>
                <a href="#features" className="text-muted-foreground hover:text-primary transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="text-muted-foreground hover:text-primary transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#tech-stack" className="text-muted-foreground hover:text-primary transition-colors">
                  Technology
                </a>
              </li>
              <li>
                <a href="#download" className="text-muted-foreground hover:text-primary transition-colors">
                  Download
                </a>
              </li>
            </ul>
          </div>
          
          {/* Resources */}
          <div>
            <h4 className="font-semibold text-foreground mb-4">Resources</h4>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
                  Documentation
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
                  GitHub Repository
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-primary transition-colors flex items-center gap-1">
                  Support
                  <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                  Privacy Policy
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        {/* Team Section */}
        <div className="border-t border-border/50 pt-12 mb-12">
          <div className="text-center mb-8">
            <h4 className="text-xl font-semibold text-foreground mb-4">Built by Team</h4>
            <p className="text-muted-foreground">
              A passionate team of 4 developers committed to making communication accessible for everyone.
            </p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-4">
            <Badge className="bg-gradient-primary text-white border-none">
              🧑‍💻 Frontend Developer
            </Badge>
            <Badge className="bg-gradient-secondary text-white border-none">
              🤖 AI/ML Engineer
            </Badge>
            <Badge className="bg-accent text-white border-none">
              🎨 UI/UX Designer
            </Badge>
            <Badge className="bg-primary text-white border-none">
              🔧 Backend Developer
            </Badge>
          </div>
        </div>
        
        {/* Bottom Footer */}
        <div className="border-t border-border/50 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-muted-foreground">
            © {currentYear} SignBridge. Built with accessibility in mind.
          </div>
          
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            Made with <Heart className="h-4 w-4 text-red-500" /> for the deaf and hard of hearing community
          </div>
        </div>
      </div>
    </footer>
  );
}