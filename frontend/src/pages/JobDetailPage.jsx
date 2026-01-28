import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import { 
  Briefcase, Building2, Calendar, MapPin, Users, IndianRupee, 
  ExternalLink, ArrowLeft, GraduationCap, Clock, Loader2, FileText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const JobDetailPage = () => {
  const { id, slug, '*': restSlug } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  // Determine the identifier (id or slug)
  const identifier = id || (slug ? (restSlug ? `${slug}/${restSlug}` : slug) : '');

  useEffect(() => {
    if (identifier) {
      fetchJob();
    }
  }, [identifier]);

  const fetchJob = async () => {
    try {
      // Try by slug first if it looks like a slug (contains /)
      let res;
      if (identifier.includes('/')) {
        res = await axios.get(`${API}/jobs/slug/${identifier}`);
      } else {
        res = await axios.get(`${API}/jobs/${identifier}`);
      }
      setJob(res.data);
    } catch (err) {
      console.error('Error fetching job:', err);
      toast.error('नौकरी की जानकारी लोड नहीं हो पाई');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (!user) {
      toast.error('कृपया पहले लॉगिन करें');
      navigate('/login');
      return;
    }

    setApplying(true);
    try {
      const appRes = await axios.post(`${API}/applications`, {
        item_type: 'job',
        item_id: job.id,
        user_details: {
          name: user.name,
          phone: user.phone,
          email: user.email
        }
      });

      // Create payment order
      const paymentRes = await axios.post(`${API}/payments/create-order`, {
        application_id: appRes.data.id,
        amount: 20, // Service fee
        return_url: `${window.location.origin}/payment-success`
      });

      // Redirect to Cashfree payment
      if (paymentRes.data.payment_session_id) {
        const cashfree = window.Cashfree?.({
          mode: 'production'
        });
        if (cashfree) {
          cashfree.checkout({
            paymentSessionId: paymentRes.data.payment_session_id,
            redirectTarget: '_self'
          });
        } else {
          // Fallback: Open Cashfree checkout in new tab
          window.open(`https://payments.cashfree.com/forms//${paymentRes.data.payment_session_id}`, '_blank');
          toast.success('भुगतान पेज खुल गया है');
        }
      }
    } catch (err) {
      console.error('Apply error:', err);
      toast.error(err.response?.data?.detail || 'आवेदन में त्रुटि हुई');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <Briefcase className="w-16 h-16 mb-4 text-muted-foreground" />
        <h2 className="text-xl font-semibold mb-2">नौकरी नहीं मिली</h2>
        <Link to="/jobs">
          <Button className="rounded-full">वापस जाएं</Button>
        </Link>
      </div>
    );
  }

  const getCategoryColor = (category) => {
    const colors = {
      government: 'bg-blue-100 text-blue-800',
      railway: 'bg-orange-100 text-orange-800',
      bank: 'bg-green-100 text-green-800',
      ssc: 'bg-purple-100 text-purple-800',
      upsc: 'bg-red-100 text-red-800',
    };
    return colors[category] || colors.government;
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-secondary text-white py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <Button 
            variant="ghost" 
            className="text-white/70 hover:text-white mb-4 -ml-2"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            वापस जाएं
          </Button>
          
          <Badge className={`${getCategoryColor(job.category)} mb-4`}>
            {job.category?.toUpperCase()}
          </Badge>
          
          <h1 className="text-2xl md:text-3xl font-bold mb-2" style={{ fontFamily: 'Outfit' }}>
            {job.title_hi || job.title}
          </h1>
          
          <div className="flex items-center gap-2 text-white/80">
            <Building2 className="w-5 h-5" />
            <span className="text-lg">{job.organization_hi || job.organization}</span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-6">
            {/* Key Info */}
            <Card>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <Users className="w-6 h-6 mx-auto mb-2 text-primary" />
                    <div className="text-2xl font-bold">{job.vacancies || '—'}</div>
                    <p className="text-sm text-muted-foreground">कुल पद</p>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <MapPin className="w-6 h-6 mx-auto mb-2 text-primary" />
                    <div className="text-lg font-bold">{job.state === 'all' ? 'भारत' : job.state}</div>
                    <p className="text-sm text-muted-foreground">स्थान</p>
                  </div>
                  <div className="text-center p-4 bg-muted/50 rounded-lg">
                    <IndianRupee className="w-6 h-6 mx-auto mb-2 text-primary" />
                    <div className="text-lg font-bold">{job.salary || '—'}</div>
                    <p className="text-sm text-muted-foreground">वेतन</p>
                  </div>
                  <div className="text-center p-4 bg-destructive/10 rounded-lg">
                    <Clock className="w-6 h-6 mx-auto mb-2 text-destructive" />
                    <div className="text-lg font-bold text-destructive">{job.last_date}</div>
                    <p className="text-sm text-muted-foreground">अंतिम तिथि</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  विवरण
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-line hindi-text">
                  {job.description_hi || job.description}
                </p>
              </CardContent>
            </Card>

            {/* Qualification */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <GraduationCap className="w-5 h-5" />
                  योग्यता
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-line hindi-text">
                  {job.qualification_hi || job.qualification}
                </p>
                {job.age_limit && (
                  <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                    <p className="text-sm">
                      <strong>आयु सीमा:</strong> {job.age_limit}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Apply Card */}
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle>आवेदन करें</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>सेवा शुल्क</span>
                    <span className="font-medium">₹20</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>सरकारी शुल्क</span>
                    <span className="font-medium">₹0</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-bold">
                    <span>कुल</span>
                    <span className="text-primary">₹20</span>
                  </div>
                </div>

                <Button 
                  className="w-full rounded-full gap-2" 
                  size="lg"
                  onClick={handleApply}
                  disabled={applying}
                  data-testid="apply-job-btn"
                >
                  {applying ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      प्रक्रिया में...
                    </>
                  ) : (
                    <>
                      <IndianRupee className="w-5 h-5" />
                      ₹20 में आवेदन करें
                    </>
                  )}
                </Button>

                {job.apply_link && (
                  <a href={job.apply_link} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline" className="w-full rounded-full gap-2">
                      <ExternalLink className="w-4 h-4" />
                      आधिकारिक वेबसाइट
                    </Button>
                  </a>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetailPage;
