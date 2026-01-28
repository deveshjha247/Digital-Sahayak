import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import { 
  Building2, FileCheck, IndianRupee, ExternalLink, ArrowLeft, 
  CheckCircle2, Loader2, FileText, Users
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const YojanaDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [yojana, setYojana] = useState(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    fetchYojana();
  }, [id]);

  const fetchYojana = async () => {
    try {
      const res = await axios.get(`${API}/yojana/${id}`);
      setYojana(res.data);
    } catch (err) {
      console.error('Error fetching yojana:', err);
      toast.error('योजना की जानकारी लोड नहीं हो पाई');
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
        item_type: 'yojana',
        item_id: yojana.id,
        user_details: {
          name: user.name,
          phone: user.phone,
          email: user.email
        }
      });

      const totalFee = (yojana.service_fee || 20) + (yojana.govt_fee || 0);

      // Create payment order
      const paymentRes = await axios.post(`${API}/payments/create-order`, {
        application_id: appRes.data.id,
        amount: totalFee,
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
          window.open(`https://payments.cashfree.com/forms/${paymentRes.data.payment_session_id}`, '_blank');
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
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (!yojana) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <Building2 className="w-16 h-16 mb-4 text-muted-foreground" />
        <h2 className="text-xl font-semibold mb-2">योजना नहीं मिली</h2>
        <Link to="/yojana">
          <Button className="rounded-full">वापस जाएं</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-accent text-white py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <Button 
            variant="ghost" 
            className="text-white/70 hover:text-white mb-4 -ml-2"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            वापस जाएं
          </Button>
          
          <Badge className="bg-white/20 text-white mb-4">
            {yojana.category?.toUpperCase()}
          </Badge>
          
          <h1 className="text-2xl md:text-3xl font-bold mb-2" style={{ fontFamily: 'Outfit' }}>
            {yojana.name_hi || yojana.name}
          </h1>
          
          <div className="flex items-center gap-2 text-white/80">
            <Building2 className="w-5 h-5" />
            <span className="text-lg">{yojana.ministry_hi || yojana.ministry}</span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-6">
            {/* Description */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  योजना का विवरण
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-line hindi-text">
                  {yojana.description_hi || yojana.description}
                </p>
              </CardContent>
            </Card>

            {/* Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-accent">
                  <CheckCircle2 className="w-5 h-5" />
                  मुख्य लाभ
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-line hindi-text">
                  {yojana.benefits_hi || yojana.benefits}
                </p>
              </CardContent>
            </Card>

            {/* Eligibility */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  पात्रता
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground whitespace-pre-line hindi-text">
                  {yojana.eligibility_hi || yojana.eligibility}
                </p>
              </CardContent>
            </Card>

            {/* Documents */}
            {yojana.documents_required?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileCheck className="w-5 h-5" />
                    आवश्यक दस्तावेज़
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {yojana.documents_required.map((doc, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-muted-foreground">
                        <CheckCircle2 className="w-4 h-4 text-accent flex-shrink-0" />
                        {doc}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
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
                    <span className="font-medium">₹{yojana.service_fee || 20}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>सरकारी शुल्क</span>
                    <span className="font-medium">₹{yojana.govt_fee || 0}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-bold">
                    <span>कुल</span>
                    <span className="text-accent">₹{(yojana.service_fee || 20) + (yojana.govt_fee || 0)}</span>
                  </div>
                </div>

                <Button 
                  className="w-full rounded-full gap-2 bg-accent hover:bg-accent/90" 
                  size="lg"
                  onClick={handleApply}
                  disabled={applying}
                  data-testid="apply-yojana-btn"
                >
                  {applying ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      प्रक्रिया में...
                    </>
                  ) : (
                    <>
                      <IndianRupee className="w-5 h-5" />
                      ₹{(yojana.service_fee || 20) + (yojana.govt_fee || 0)} में आवेदन करें
                    </>
                  )}
                </Button>

                {yojana.apply_link && (
                  <a href={yojana.apply_link} target="_blank" rel="noopener noreferrer">
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

export default YojanaDetailPage;
