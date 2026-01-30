import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Send, 
  Plus, 
  MessageSquare, 
  Trash2, 
  Menu, 
  X, 
  Bot, 
  User, 
  Sparkles,
  ChevronLeft,
  MoreVertical,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { cn } from '../lib/utils';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Markdown-like formatting for AI responses
const formatMessage = (text) => {
  if (!text) return '';
  
  // Bold text
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Convert bullet points
  formatted = formatted.replace(/^• /gm, '<span class="text-primary">•</span> ');
  formatted = formatted.replace(/^- /gm, '<span class="text-primary">•</span> ');
  
  // Convert numbered lists
  formatted = formatted.replace(/^(\d+)[.)] /gm, '<span class="text-primary font-semibold">$1.</span> ');
  
  // Emojis with better styling
  formatted = formatted.replace(/([\u{1F300}-\u{1F9FF}])/gu, '<span class="text-xl">$1</span>');
  
  // Code blocks
  formatted = formatted.replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm font-mono">$1</code>');
  
  // Line breaks
  formatted = formatted.replace(/\n/g, '<br/>');
  
  return formatted;
};

// Single message component
const ChatMessage = ({ message, isUser, onCopy }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };
  
  return (
    <div className={cn(
      "group flex gap-3 px-4 py-6",
      isUser ? "bg-background" : "bg-muted/30"
    )}>
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser 
          ? "bg-primary text-primary-foreground" 
          : "bg-gradient-to-br from-orange-500 to-orange-600 text-white"
      )}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>
      
      {/* Content */}
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">
            {isUser ? 'You' : 'Digital Sahayak AI'}
          </span>
          {!isUser && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              AI
            </span>
          )}
        </div>
        
        <div 
          className="prose prose-sm max-w-none dark:prose-invert text-foreground leading-relaxed"
          dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
        />
        
        {/* Actions */}
        {!isUser && (
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={handleCopy}
            >
              {copied ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

// Typing indicator
const TypingIndicator = () => (
  <div className="flex gap-3 px-4 py-6 bg-muted/30">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
      <Bot className="w-4 h-4 text-white" />
    </div>
    <div className="flex items-center gap-1 pt-2">
      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  </div>
);

// Sidebar conversation item
const ConversationItem = ({ conv, isActive, onClick, onDelete }) => (
  <div
    className={cn(
      "group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors",
      isActive 
        ? "bg-primary/10 text-primary" 
        : "hover:bg-muted"
    )}
    onClick={onClick}
  >
    <MessageSquare className="w-4 h-4 flex-shrink-0" />
    <span className="flex-1 truncate text-sm">{conv.title || 'New Chat'}</span>
    <Button
      variant="ghost"
      size="icon"
      className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity"
      onClick={(e) => {
        e.stopPropagation();
        onDelete(conv.id);
      }}
    >
      <Trash2 className="w-3 h-3 text-destructive" />
    </Button>
  </div>
);

// Welcome screen
const WelcomeScreen = ({ onSuggestionClick }) => {
  const suggestions = [
    { icon: "📋", text: "PM-KISAN योजना के बारे में बताओ", category: "Schemes" },
    { icon: "💼", text: "SSC की jobs कैसे मिलेंगी?", category: "Jobs" },
    { icon: "📄", text: "Aadhar card बनवाने में help करो", category: "Documents" },
    { icon: "✅", text: "मैं किन योजनाओं के लिए eligible हूं?", category: "Eligibility" },
  ];
  
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center mb-6 shadow-lg">
        <Bot className="w-8 h-8 text-white" />
      </div>
      
      <h1 className="text-2xl font-bold mb-2">Digital Sahayak AI</h1>
      <p className="text-muted-foreground mb-8 max-w-md">
        नमस्ते! 🙏 मैं आपकी सरकारी योजनाओं, नौकरियों और documents में मदद कर सकता हूं।
      </p>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="flex items-start gap-3 p-4 rounded-xl border border-border hover:border-primary hover:bg-primary/5 transition-all text-left group"
            onClick={() => onSuggestionClick(suggestion.text)}
          >
            <span className="text-2xl">{suggestion.icon}</span>
            <div>
              <p className="text-sm font-medium group-hover:text-primary transition-colors">
                {suggestion.text}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{suggestion.category}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

// Main Chat Page Component
export default function AIChatPage() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  const [conversations, setConversations] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Check for mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  // Redirect if not logged in
  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);
  
  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);
  
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  
  // Load conversations
  const loadConversations = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_URL}/ai/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.success) {
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, [token]);
  
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);
  
  // Load specific conversation
  const loadConversation = async (convId) => {
    if (!token || !convId) return;
    
    try {
      const response = await fetch(`${API_URL}/ai/conversations/${convId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.success && data.conversation) {
        setCurrentConvId(convId);
        setMessages(data.conversation.messages || []);
        if (isMobile) setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };
  
  // Start new chat
  const startNewChat = () => {
    setCurrentConvId(null);
    setMessages([]);
    if (isMobile) setSidebarOpen(false);
    inputRef.current?.focus();
  };
  
  // Delete conversation
  const deleteConversation = async (convId) => {
    if (!token) return;
    
    try {
      await fetch(`${API_URL}/ai/conversations/${convId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setConversations(prev => prev.filter(c => c.id !== convId));
      
      if (currentConvId === convId) {
        startNewChat();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };
  
  // Send message
  const sendMessage = async (messageText = inputValue) => {
    if (!messageText.trim() || isLoading || !token) return;
    
    const userMessage = {
      role: 'user',
      content: messageText.trim(),
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_URL}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          message: messageText.trim(),
          conversation_id: currentConvId
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const aiMessage = {
          role: 'assistant',
          content: data.message,
          timestamp: data.timestamp
        };
        
        setMessages(prev => [...prev, aiMessage]);
        
        // Update conversation ID if new
        if (!currentConvId && data.conversation_id) {
          setCurrentConvId(data.conversation_id);
        }
        
        // Refresh conversation list
        loadConversations();
      } else {
        throw new Error(data.detail || 'Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'माफ़ कीजिए, कुछ गड़बड़ हो गई। कृपया फिर से कोशिश करें। 🙏',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  if (!user) return null;
  
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar Overlay for Mobile */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <div className={cn(
        "flex flex-col border-r border-border bg-muted/30 transition-all duration-300 z-50",
        isMobile 
          ? "fixed inset-y-0 left-0 w-72" 
          : "w-72",
        isMobile && !sidebarOpen && "-translate-x-full"
      )}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-border">
          <Button
            onClick={startNewChat}
            className="w-full justify-start gap-2"
            variant="outline"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </Button>
        </div>
        
        {/* Conversations List */}
        <ScrollArea className="flex-1 p-2">
          <div className="space-y-1">
            {conversations.map(conv => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isActive={conv.id === currentConvId}
                onClick={() => loadConversation(conv.id)}
                onDelete={deleteConversation}
              />
            ))}
            
            {conversations.length === 0 && (
              <p className="text-center text-muted-foreground text-sm py-8">
                No conversations yet
              </p>
            )}
          </div>
        </ScrollArea>
        
        {/* Sidebar Footer */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-medium">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.phone}</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </Button>
          
          <div className="flex items-center gap-2 flex-1">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-sm">Digital Sahayak AI</h1>
              <p className="text-xs text-muted-foreground">Always ready to help</p>
            </div>
          </div>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/dashboard')}
          >
            <ChevronLeft className="w-5 h-5" />
          </Button>
        </div>
        
        {/* Messages Area */}
        <ScrollArea className="flex-1">
          {messages.length === 0 ? (
            <WelcomeScreen onSuggestionClick={(text) => sendMessage(text)} />
          ) : (
            <div className="max-w-3xl mx-auto">
              {messages.map((msg, index) => (
                <ChatMessage
                  key={index}
                  message={msg}
                  isUser={msg.role === 'user'}
                />
              ))}
              
              {isLoading && <TypingIndicator />}
              
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </ScrollArea>
        
        {/* Input Area */}
        <div className="border-t border-border bg-background p-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Message Digital Sahayak AI..."
                  className="pr-12 py-6 text-base rounded-xl"
                  disabled={isLoading}
                />
                <Button
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg"
                  onClick={() => sendMessage()}
                  disabled={!inputValue.trim() || isLoading}
                >
                  {isLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
            
            <p className="text-xs text-muted-foreground text-center mt-3">
              Digital Sahayak AI आपकी सरकारी योजनाओं और नौकरियों में मदद करता है। 
              <span className="text-primary ml-1">🇮🇳</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
