import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { CheckCircle2, XCircle, Loader2, Home } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = React.useState('verifying');
  const [paymentInfo, setPaymentInfo] = React.useState(null);

  const orderId = searchParams.get('order_id');

  useEffect(() => {
    if (orderId) {
      verifyPayment();
    } else {
      setStatus('error');
    }
  }, [orderId]);

  const verifyPayment = async () => {
    try {
      const res = await axios.get(`${API}/payments/verify/${orderId}`);
      setPaymentInfo(res.data);
      if (res.data.status === 'PAID') {
        setStatus('success');
        toast.success('भुगतान सफल!');
      } else if (res.data.status === 'FAILED') {
        setStatus('failed');
        toast.error('भुगतान विफल');
      } else {
        setStatus('pending');
      }
    } catch (err) {
      console.error('Payment verify error:', err);
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8 text-center">
          {status === 'verifying' && (
            <>
              <Loader2 className="w-16 h-16 mx-auto mb-4 animate-spin text-primary" />
              <h2 className="text-xl font-bold mb-2">भुगतान सत्यापित हो रहा है...</h2>
              <p className="text-muted-foreground">कृपया प्रतीक्षा करें</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2 text-green-600">भुगतान सफल!</h2>
              <p className="text-muted-foreground mb-4">
                आपका आवेदन प्राप्त हो गया है। हम जल्द ही इसे प्रोसेस करेंगे।
              </p>
              {paymentInfo && (
                <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left">
                  <p className="text-sm"><strong>Order ID:</strong> {paymentInfo.order_id}</p>
                  <p className="text-sm"><strong>Amount:</strong> ₹{paymentInfo.amount}</p>
                </div>
              )}
              <div className="space-y-3">
                <Button className="w-full rounded-full" onClick={() => navigate('/dashboard')} data-testid="goto-dashboard-btn">
                  डैशबोर्ड देखें
                </Button>
                <Button variant="outline" className="w-full rounded-full" onClick={() => navigate('/')}>
                  <Home className="w-4 h-4 mr-2" />
                  होम पेज
                </Button>
              </div>
            </>
          )}

          {status === 'failed' && (
            <>
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="w-10 h-10 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2 text-red-600">भुगतान विफल</h2>
              <p className="text-muted-foreground mb-6">
                भुगतान पूरा नहीं हो सका। कृपया पुनः प्रयास करें।
              </p>
              <Button className="w-full rounded-full" onClick={() => navigate('/dashboard')}>
                पुनः प्रयास करें
              </Button>
            </>
          )}

          {status === 'pending' && (
            <>
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-yellow-100 flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-yellow-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2 text-yellow-600">भुगतान प्रक्रिया में</h2>
              <p className="text-muted-foreground mb-6">
                आपका भुगतान प्रोसेस हो रहा है। कृपया कुछ समय बाद चेक करें।
              </p>
              <Button className="w-full rounded-full" onClick={verifyPayment}>
                स्थिति जांचें
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                <XCircle className="w-10 h-10 text-gray-600" />
              </div>
              <h2 className="text-xl font-bold mb-2">कुछ गलत हुआ</h2>
              <p className="text-muted-foreground mb-6">
                भुगतान स्थिति की जांच नहीं हो पाई।
              </p>
              <Button className="w-full rounded-full" onClick={() => navigate('/dashboard')}>
                डैशबोर्ड देखें
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentSuccessPage;
