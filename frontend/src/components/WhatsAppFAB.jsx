import React, { useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

const WhatsAppFAB = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [phone, setPhone] = useState('');

  const handleWhatsAppConnect = () => {
    const message = encodeURIComponent('नमस्ते! मुझे Digital Sahayak से जुड़ना है। कृपया मदद करें।');
    window.open(`https://wa.me/916200184827?text=${message}`, '_blank');
  };

  return (
    <>
      {/* FAB Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="whatsapp-fab"
        data-testid="whatsapp-fab"
        aria-label="WhatsApp Chat"
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <MessageCircle className="w-6 h-6" />
        )}
      </button>

      {/* Chat Popup */}
      {isOpen && (
        <div 
          className="fixed bottom-24 right-6 z-50 w-80 bg-card border rounded-2xl shadow-2xl overflow-hidden animate-slide-up"
          data-testid="whatsapp-popup"
        >
          {/* Header */}
          <div className="bg-[#25D366] p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                <MessageCircle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold">Digital Sahayak</h3>
                <p className="text-sm text-white/80">WhatsApp Support</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            <div className="bg-muted/50 p-3 rounded-lg">
              <p className="text-sm hindi-text">
                नमस्ते! 🙏 WhatsApp पर हमसे जुड़ें और पाएं:
              </p>
              <ul className="text-sm mt-2 space-y-1 text-muted-foreground">
                <li>✅ नौकरी अलर्ट तुरंत</li>
                <li>✅ योजना अपडेट</li>
                <li>✅ आवेदन में सहायता</li>
                <li>✅ 24/7 सपोर्ट</li>
              </ul>
            </div>

            <Button 
              onClick={handleWhatsAppConnect}
              className="w-full bg-[#25D366] hover:bg-[#25D366]/90 text-white rounded-full gap-2"
              data-testid="whatsapp-connect-btn"
            >
              <MessageCircle className="w-5 h-5" />
              WhatsApp पर चैट करें
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              या हमें सीधे मैसेज करें: <strong>+91 6200184827</strong>
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default WhatsAppFAB;
