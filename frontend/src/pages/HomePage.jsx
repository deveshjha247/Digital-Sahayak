import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import JobCard from '../components/JobCard';
import YojanaCard from '../components/YojanaCard';
import { 
  Briefcase, Building2, FileText, Users, ArrowRight, CheckCircle2, 
  Zap, Shield, MessageCircle, Star, TrendingUp, Clock, Home, Search,
  GraduationCap, Award, ClipboardList, BookOpen, Phone
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const HomePage = () => {
  const [jobs, setJobs] = useState([]);
  const [yojanas, setYojanas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [jobsRes, yojanaRes] = await Promise.all([
        axios.get(`${API}/jobs?limit=6`),
        axios.get(`${API}/yojana?limit=4`)
      ]);
      setJobs(jobsRes.data.jobs || []);
      setYojanas(yojanaRes.data.yojanas || []);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: Zap,
      title: 'तेज़ आवेदन',
      titleEn: 'Quick Apply',
      desc: 'एक क्लिक में आवेदन करें, AI की मदद से फॉर्म भरें',
      color: 'text-primary'
    },
    {
      icon: MessageCircle,
      title: 'WhatsApp अलर्ट',
      titleEn: 'WhatsApp Alerts',
      desc: 'नई नौकरी और योजना की जानकारी सीधे WhatsApp पर पाएं',
      color: 'text-[#25D366]'
    },
    {
      icon: Shield,
      title: 'सुरक्षित भुगतान',
      titleEn: 'Secure Payment',
      desc: 'Cashfree के साथ UPI, कार्ड, नेट बैंकिंग से भुगतान',
      color: 'text-accent'
    },
    {
      icon: FileText,
      title: 'डॉक्यूमेंट स्टोर',
      titleEn: 'Document Storage',
      desc: 'DigiLocker जैसा सुरक्षित दस्तावेज़ भंडारण',
      color: 'text-blue-500'
    }
  ];

  const stats = [
    { value: '10K+', label: 'नौकरी अलर्ट', icon: Briefcase },
    { value: '500+', label: 'सरकारी योजनाएं', icon: Building2 },
    { value: '1L+', label: 'सफल आवेदन', icon: CheckCircle2 },
    { value: '₹20', label: 'सेवा शुल्क मात्र', icon: TrendingUp }
  ];

  const quickLinks = [
    { href: '/', label: 'Home', labelHi: 'होम', icon: Home, color: 'bg-blue-500' },
    { href: '/yojana', label: 'Government Scheme', labelHi: 'सरकारी योजना', icon: Building2, color: 'bg-green-500' },
    { href: '/jobs', label: 'Latest Jobs', labelHi: 'नई नौकरियां', icon: Briefcase, color: 'bg-orange-500' },
    { href: '/results', label: 'Results', labelHi: 'रिजल्ट', icon: Award, color: 'bg-purple-500' },
    { href: '/admit-card', label: 'Admit Card', labelHi: 'एडमिट कार्ड', icon: FileText, color: 'bg-red-500' },
    { href: '/answer-key', label: 'Answer Key', labelHi: 'आंसर की', icon: ClipboardList, color: 'bg-teal-500' },
    { href: '/syllabus', label: 'Syllabus', labelHi: 'सिलेबस', icon: BookOpen, color: 'bg-indigo-500' },
    { href: '/search', label: 'Search', labelHi: 'खोजें', icon: Search, color: 'bg-yellow-500' },
    { href: '/contact', label: 'Contact Us', labelHi: 'संपर्क करें', icon: Phone, color: 'bg-pink-500' }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-secondary via-secondary to-secondary/95 text-white">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
          }} />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28 relative">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div>
                <Badge className="bg-primary/20 text-primary-foreground border-primary/30 mb-4">
                  🇮🇳 भारत का पहला AI-सहायक प्लेटफॉर्म
                </Badge>
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight" style={{ fontFamily: 'Outfit' }}>
                  <span className="text-primary">डिजिटल</span> सहायक
                </h1>
                <p className="text-xl md:text-2xl mt-4 text-white/80 hindi-text">
                  सरकारी नौकरी और योजना का <span className="text-primary font-semibold">वन-क्लिक</span> आवेदन
                </p>
              </div>

              <p className="text-lg text-white/70 hindi-text leading-relaxed">
                अब किसी भी सरकारी नौकरी या योजना के लिए आवेदन करना हुआ आसान। 
                WhatsApp पर अलर्ट पाएं, ₹20 में आवेदन करवाएं।
              </p>

              <div className="flex flex-wrap gap-4">
                <Link to="/jobs">
                  <Button size="lg" className="rounded-full px-8 gap-2 text-lg shadow-lg shadow-primary/30" data-testid="hero-jobs-btn">
                    <Briefcase className="w-5 h-5" />
                    नौकरी देखें
                  </Button>
                </Link>
                <Link to="/yojana">
                  <Button size="lg" variant="outline" className="rounded-full px-8 gap-2 text-lg border-white/30 text-white hover:bg-white/10" data-testid="hero-yojana-btn">
                    <Building2 className="w-5 h-5" />
                    योजनाएं देखें
                  </Button>
                </Link>
              </div>

              <div className="flex items-center gap-6 pt-4">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="w-10 h-10 rounded-full bg-primary/20 border-2 border-secondary flex items-center justify-center">
                      <Users className="w-4 h-4 text-primary" />
                    </div>
                  ))}
                </div>
                <div>
                  <div className="flex items-center gap-1 text-yellow-400">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star key={i} className="w-4 h-4 fill-current" />
                    ))}
                  </div>
                  <p className="text-sm text-white/60">1 लाख+ खुश उपयोगकर्ता</p>
                </div>
              </div>
            </div>

            {/* Hero Image/Illustration */}
            <div className="hidden md:block relative">
              <div className="absolute -top-20 -right-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-20 -left-20 w-72 h-72 bg-accent/20 rounded-full blur-3xl" />
              <div className="relative bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 bg-white/10 rounded-xl">
                    <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                      <Briefcase className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold">नई नौकरी अलर्ट!</p>
                      <p className="text-sm text-white/60">Railway Group D - 5000 पद</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-white/10 rounded-xl">
                    <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <p className="font-semibold">PM आवास योजना</p>
                      <p className="text-sm text-white/60">आवेदन शुरू - अभी अप्लाई करें</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-[#25D366]/20 rounded-xl">
                    <div className="w-12 h-12 rounded-full bg-[#25D366]/30 flex items-center justify-center">
                      <MessageCircle className="w-6 h-6 text-[#25D366]" />
                    </div>
                    <div>
                      <p className="font-semibold">WhatsApp से जुड़ें</p>
                      <p className="text-sm text-white/60">+91 6200184827</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Wave Divider */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 120L60 110C120 100 240 80 360 75C480 70 600 80 720 85C840 90 960 90 1080 85C1200 80 1320 70 1380 65L1440 60V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="hsl(var(--background))" />
          </svg>
        </div>
      </section>

      {/* Quick Navigation Section */}
      <section className="py-8 -mt-6 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-card rounded-2xl shadow-xl border border-border/50 p-6">
            <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-4">
              {quickLinks.map((link, idx) => (
                <Link 
                  key={idx} 
                  to={link.href}
                  className="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-muted transition-all duration-200 group"
                >
                  <div className={`w-12 h-12 rounded-full ${link.color} flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg`}>
                    <link.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium text-foreground leading-tight">{link.label}</p>
                    <p className="text-[10px] text-muted-foreground">{link.labelHi}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, idx) => (
              <div key={idx} className="text-center p-6 bg-card rounded-2xl shadow-sm hover:shadow-md transition-all">
                <stat.icon className="w-8 h-8 mx-auto mb-3 text-primary" />
                <div className="text-3xl font-bold text-primary" style={{ fontFamily: 'Outfit' }}>{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <Badge className="bg-primary/10 text-primary mb-4">हमारी सेवाएं</Badge>
            <h2 className="text-3xl md:text-4xl font-bold" style={{ fontFamily: 'Outfit' }}>
              क्यों चुनें <span className="text-primary">Digital Sahayak</span>
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <div 
                key={idx}
                className="bg-card p-6 rounded-2xl border border-border/50 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                <div className={`w-14 h-14 rounded-xl bg-muted flex items-center justify-center mb-4 ${feature.color}`}>
                  <feature.icon className="w-7 h-7" />
                </div>
                <h3 className="font-bold text-lg mb-1">{feature.title}</h3>
                <p className="text-xs text-muted-foreground mb-2">{feature.titleEn}</p>
                <p className="text-sm text-muted-foreground hindi-text">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Latest Jobs Section */}
      <section className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <Badge className="bg-primary/10 text-primary mb-2">नई नौकरियां</Badge>
              <h2 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
                ताज़ा नौकरी अलर्ट
              </h2>
            </div>
            <Link to="/jobs">
              <Button variant="outline" className="rounded-full gap-2" data-testid="view-all-jobs-btn">
                सभी देखें <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-card rounded-xl p-6 animate-pulse">
                  <div className="h-4 bg-muted rounded w-1/4 mb-4" />
                  <div className="h-6 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-4 bg-muted rounded w-1/2 mb-4" />
                  <div className="h-20 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : jobs.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-card rounded-2xl">
              <Briefcase className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg text-muted-foreground">अभी कोई नौकरी उपलब्ध नहीं है</p>
              <p className="text-sm text-muted-foreground mt-1">जल्द ही नई नौकरियां जोड़ी जाएंगी</p>
            </div>
          )}
        </div>
      </section>

      {/* Latest Yojana Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <Badge className="bg-accent/10 text-accent mb-2">सरकारी योजनाएं</Badge>
              <h2 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
                लोकप्रिय योजनाएं
              </h2>
            </div>
            <Link to="/yojana">
              <Button variant="outline" className="rounded-full gap-2" data-testid="view-all-yojana-btn">
                सभी देखें <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="grid md:grid-cols-2 gap-6">
              {[1, 2].map((i) => (
                <div key={i} className="bg-card rounded-xl p-6 animate-pulse">
                  <div className="h-4 bg-muted rounded w-1/4 mb-4" />
                  <div className="h-6 bg-muted rounded w-3/4 mb-2" />
                  <div className="h-4 bg-muted rounded w-1/2 mb-4" />
                  <div className="h-20 bg-muted rounded" />
                </div>
              ))}
            </div>
          ) : yojanas.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-6">
              {yojanas.map((yojana) => (
                <YojanaCard key={yojana.id} yojana={yojana} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-card rounded-2xl">
              <Building2 className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg text-muted-foreground">अभी कोई योजना उपलब्ध नहीं है</p>
              <p className="text-sm text-muted-foreground mt-1">जल्द ही नई योजनाएं जोड़ी जाएंगी</p>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-card border-t py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
                  <span className="text-white font-bold">DS</span>
                </div>
                <div>
                  <span className="font-bold">Digital Sahayak</span>
                  <p className="text-xs text-muted-foreground">डिजिटल सहायक</p>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                भारत का पहला AI-सहायक सरकारी नौकरी और योजना आवेदन प्लेटफॉर्म।
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">त्वरित लिंक</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link to="/jobs" className="hover:text-primary transition-colors">नौकरी अलर्ट</Link></li>
                <li><Link to="/yojana" className="hover:text-primary transition-colors">सरकारी योजनाएं</Link></li>
                <li><Link to="/dashboard" className="hover:text-primary transition-colors">डैशबोर्ड</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">सहायता</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary transition-colors">कैसे काम करता है?</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">अक्सर पूछे जाने वाले प्रश्न</a></li>
                <li><a href="#" className="hover:text-primary transition-colors">संपर्क करें</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">संपर्क</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-[#25D366]" />
                  +91 6200184827
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
            <p>© 2025 Digital Sahayak. सर्वाधिकार सुरक्षित।</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
