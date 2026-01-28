import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import { User, GraduationCap, MapPin, Calendar, Briefcase, Loader2, Save, Sparkles } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const EDUCATION_LEVELS = [
  { value: '10th', label: '10वीं पास', labelEn: '10th Pass' },
  { value: '12th', label: '12वीं पास', labelEn: '12th Pass' },
  { value: 'graduate', label: 'स्नातक', labelEn: 'Graduate' },
  { value: 'post_graduate', label: 'परास्नातक', labelEn: 'Post Graduate' },
];

const STATES = [
  { value: 'all', label: 'संपूर्ण भारत', labelEn: 'All India' },
  { value: 'bihar', label: 'बिहार', labelEn: 'Bihar' },
  { value: 'jharkhand', label: 'झारखंड', labelEn: 'Jharkhand' },
  { value: 'up', label: 'उत्तर प्रदेश', labelEn: 'Uttar Pradesh' },
  { value: 'mp', label: 'मध्य प्रदेश', labelEn: 'Madhya Pradesh' },
  { value: 'rajasthan', label: 'राजस्थान', labelEn: 'Rajasthan' },
  { value: 'maharashtra', label: 'महाराष्ट्र', labelEn: 'Maharashtra' },
  { value: 'wb', label: 'पश्चिम बंगाल', labelEn: 'West Bengal' },
];

const CATEGORIES = [
  { value: 'government', label: 'सरकारी नौकरी', labelEn: 'Government' },
  { value: 'railway', label: 'रेलवे', labelEn: 'Railway' },
  { value: 'bank', label: 'बैंक', labelEn: 'Bank' },
  { value: 'ssc', label: 'SSC', labelEn: 'SSC' },
  { value: 'upsc', label: 'UPSC', labelEn: 'UPSC' },
  { value: 'police', label: 'पुलिस', labelEn: 'Police' },
  { value: 'defence', label: 'रक्षा', labelEn: 'Defence' },
  { value: 'state', label: 'राज्य', labelEn: 'State' },
];

const ProfilePreferencesPage = () => {
  const { user, fetchUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    education_level: '',
    state: '',
    age: '',
    preferred_categories: [],
  });

  useEffect(() => {
    if (user) {
      setForm({
        name: user.name || '',
        email: user.email || '',
        education_level: user.education_level || '',
        state: user.state || '',
        age: user.age?.toString() || '',
        preferred_categories: user.preferred_categories || [],
      });
    }
  }, [user]);

  const handleCategoryToggle = (category) => {
    setForm(prev => ({
      ...prev,
      preferred_categories: prev.preferred_categories.includes(category)
        ? prev.preferred_categories.filter(c => c !== category)
        : [...prev.preferred_categories, category]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const payload = {
        ...form,
        age: form.age ? parseInt(form.age) : null,
      };
      
      await axios.put(`${API}/profile/preferences`, payload);
      toast.success('प्रोफ़ाइल अपडेट हो गई!');
      fetchUser();
    } catch (err) {
      console.error('Profile update error:', err);
      toast.error('अपडेट में त्रुटि हुई');
    } finally {
      setLoading(false);
    }
  };

  const profileComplete = form.education_level && form.state && form.age;

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-3" style={{ fontFamily: 'Outfit' }}>
            <User className="w-8 h-8 text-primary" />
            प्रोफ़ाइल सेटिंग्स
          </h1>
          <p className="text-muted-foreground mt-1">
            बेहतर नौकरी सुझाव पाने के लिए अपनी जानकारी अपडेट करें
          </p>
        </div>

        {/* Profile Completeness */}
        {!profileComplete && (
          <Card className="mb-6 border-primary/30 bg-primary/5">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">प्रोफ़ाइल पूरी करें</h3>
                <p className="text-sm text-muted-foreground">
                  AI-powered नौकरी सुझाव पाने के लिए अपनी शिक्षा, राज्य और आयु भरें
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit}>
          {/* Basic Info */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                बुनियादी जानकारी
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">पूरा नाम</Label>
                  <Input
                    id="name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="अपना नाम"
                    data-testid="profile-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">ईमेल</Label>
                  <Input
                    id="email"
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="email@example.com"
                    data-testid="profile-email-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Education & Location */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5" />
                शिक्षा और स्थान
              </CardTitle>
              <CardDescription>
                इन जानकारियों से हम आपके लिए उपयुक्त नौकरियां ढूंढ सकते हैं
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid sm:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>शिक्षा स्तर *</Label>
                  <Select 
                    value={form.education_level} 
                    onValueChange={(v) => setForm({ ...form, education_level: v })}
                  >
                    <SelectTrigger data-testid="profile-education-select">
                      <SelectValue placeholder="चुनें" />
                    </SelectTrigger>
                    <SelectContent>
                      {EDUCATION_LEVELS.map((level) => (
                        <SelectItem key={level.value} value={level.value}>
                          {level.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>राज्य *</Label>
                  <Select 
                    value={form.state} 
                    onValueChange={(v) => setForm({ ...form, state: v })}
                  >
                    <SelectTrigger data-testid="profile-state-select">
                      <SelectValue placeholder="चुनें" />
                    </SelectTrigger>
                    <SelectContent>
                      {STATES.map((state) => (
                        <SelectItem key={state.value} value={state.value}>
                          {state.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="age">आयु (वर्ष) *</Label>
                  <Input
                    id="age"
                    type="number"
                    min="18"
                    max="60"
                    value={form.age}
                    onChange={(e) => setForm({ ...form, age: e.target.value })}
                    placeholder="जैसे: 25"
                    data-testid="profile-age-input"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Job Preferences */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5" />
                पसंदीदा श्रेणियां
              </CardTitle>
              <CardDescription>
                वे श्रेणियां चुनें जिनमें आप नौकरी खोज रहे हैं
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {CATEGORIES.map((cat) => (
                  <div
                    key={cat.value}
                    onClick={() => handleCategoryToggle(cat.value)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      form.preferred_categories.includes(cat.value)
                        ? 'bg-primary/10 border-primary'
                        : 'bg-muted/30 border-border hover:border-primary/50'
                    }`}
                    data-testid={`category-${cat.value}`}
                  >
                    <div className="flex items-center gap-2">
                      <Checkbox 
                        checked={form.preferred_categories.includes(cat.value)}
                        className="pointer-events-none"
                      />
                      <div>
                        <p className="font-medium text-sm">{cat.label}</p>
                        <p className="text-xs text-muted-foreground">{cat.labelEn}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button 
              type="submit" 
              size="lg"
              className="rounded-full px-8 gap-2"
              disabled={loading}
              data-testid="save-profile-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  सेव हो रहा है...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  प्रोफ़ाइल सेव करें
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfilePreferencesPage;
