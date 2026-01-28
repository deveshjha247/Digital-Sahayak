import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Eye, EyeOff, Phone, Lock, User, Mail, Loader2 } from 'lucide-react';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    password: '',
    language: 'hi'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.phone || !form.password) {
      toast.error('कृपया सभी आवश्यक फ़ील्ड भरें');
      return;
    }

    if (form.phone.length !== 10) {
      toast.error('कृपया सही 10 अंकों का मोबाइल नंबर डालें');
      return;
    }

    if (form.password.length < 6) {
      toast.error('पासवर्ड कम से कम 6 अक्षर का होना चाहिए');
      return;
    }
    
    setLoading(true);
    try {
      await register(form);
      toast.success('रजिस्ट्रेशन सफल! स्वागत है!');
      navigate('/dashboard');
    } catch (err) {
      console.error('Register error:', err);
      toast.error(err.response?.data?.detail || 'रजिस्ट्रेशन विफल। कृपया पुनः प्रयास करें।');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Image */}
      <div className="hidden lg:flex flex-1 bg-primary items-center justify-center p-12">
        <div className="max-w-lg text-white text-center">
          <div className="w-24 h-24 rounded-2xl bg-white/20 mx-auto mb-8 flex items-center justify-center">
            <span className="text-4xl font-bold">DS</span>
          </div>
          <h2 className="text-3xl font-bold mb-4" style={{ fontFamily: 'Outfit' }}>
            Digital Sahayak से जुड़ें
          </h2>
          <p className="text-white/80 text-lg hindi-text">
            रजिस्टर करें और पाएं:<br/>
            ✓ नौकरी अलर्ट सीधे WhatsApp पर<br/>
            ✓ ₹20 में आवेदन सेवा<br/>
            ✓ सुरक्षित दस्तावेज़ भंडारण
          </p>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <Link to="/" className="inline-flex items-center gap-2 mb-8">
              <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
                <span className="text-white font-bold text-xl">DS</span>
              </div>
            </Link>
            <h1 className="text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
              नया खाता बनाएं
            </h1>
            <p className="text-muted-foreground mt-2">
              मुफ्त में रजिस्टर करें
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name">पूरा नाम *</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="name"
                  type="text"
                  placeholder="अपना पूरा नाम डालें"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="pl-10"
                  data-testid="register-name-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">मोबाइल नंबर *</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="phone"
                  type="tel"
                  placeholder="10 अंकों का मोबाइल नंबर"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                  className="pl-10"
                  maxLength={10}
                  data-testid="register-phone-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">ईमेल (वैकल्पिक)</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="yourname@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="pl-10"
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">पासवर्ड *</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="कम से कम 6 अक्षर"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="pl-10 pr-10"
                  data-testid="register-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>पसंदीदा भाषा</Label>
              <Select value={form.language} onValueChange={(v) => setForm({ ...form, language: v })}>
                <SelectTrigger data-testid="register-language-select">
                  <SelectValue placeholder="भाषा चुनें" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hi">हिंदी</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button 
              type="submit" 
              className="w-full rounded-full" 
              size="lg"
              disabled={loading}
              data-testid="register-submit-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  रजिस्टर हो रहा है...
                </>
              ) : (
                'रजिस्टर करें'
              )}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            पहले से खाता है?{' '}
            <Link to="/login" className="text-primary font-semibold hover:underline">
              लॉगिन करें
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
