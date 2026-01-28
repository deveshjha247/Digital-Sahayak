import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Eye, EyeOff, Phone, Lock, Loader2 } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    phone: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.phone || !form.password) {
      toast.error('कृपया सभी फ़ील्ड भरें');
      return;
    }
    
    setLoading(true);
    try {
      await login(form.phone, form.password);
      toast.success('लॉगिन सफल!');
      navigate('/dashboard');
    } catch (err) {
      console.error('Login error:', err);
      toast.error(err.response?.data?.detail || 'लॉगिन विफल। कृपया पुनः प्रयास करें।');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <Link to="/" className="inline-flex items-center gap-2 mb-8">
              <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
                <span className="text-white font-bold text-xl">DS</span>
              </div>
            </Link>
            <h1 className="text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
              वापसी का स्वागत है!
            </h1>
            <p className="text-muted-foreground mt-2">
              अपने खाते में लॉगिन करें
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="phone">मोबाइल नंबर</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="phone"
                  type="tel"
                  placeholder="10 अंकों का मोबाइल नंबर"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="pl-10"
                  maxLength={10}
                  data-testid="login-phone-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">पासवर्ड</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="अपना पासवर्ड डालें"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="pl-10 pr-10"
                  data-testid="login-password-input"
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

            <Button 
              type="submit" 
              className="w-full rounded-full" 
              size="lg"
              disabled={loading}
              data-testid="login-submit-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  लॉगिन हो रहा है...
                </>
              ) : (
                'लॉगिन करें'
              )}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            खाता नहीं है?{' '}
            <Link to="/register" className="text-primary font-semibold hover:underline">
              रजिस्टर करें
            </Link>
          </p>

          {/* Demo Credentials */}
          <div className="bg-muted/50 rounded-lg p-4 text-center">
            <p className="text-sm text-muted-foreground mb-2">Demo Admin Login:</p>
            <p className="text-sm font-mono">Phone: 6200184827</p>
            <p className="text-sm font-mono">Password: admin123</p>
          </div>
        </div>
      </div>

      {/* Right Side - Image */}
      <div className="hidden lg:flex flex-1 bg-secondary items-center justify-center p-12">
        <div className="max-w-lg text-white text-center">
          <div className="w-24 h-24 rounded-2xl bg-primary/20 mx-auto mb-8 flex items-center justify-center">
            <span className="text-4xl font-bold text-primary">DS</span>
          </div>
          <h2 className="text-3xl font-bold mb-4" style={{ fontFamily: 'Outfit' }}>
            Digital Sahayak
          </h2>
          <p className="text-white/70 text-lg hindi-text">
            सरकारी नौकरी और योजना का वन-क्लिक आवेदन प्लेटफॉर्म
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
