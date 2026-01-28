import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { 
  Briefcase, Building2, FileText, Clock, CheckCircle2, 
  AlertCircle, IndianRupee, ArrowRight, MessageCircle
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const DashboardPage = () => {
  const { user } = useAuth();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const res = await axios.get(`${API}/applications`);
      setApplications(res.data.applications || []);
    } catch (err) {
      console.error('Error fetching applications:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { label: 'भुगतान बाकी', className: 'badge-pending', icon: Clock },
      processing: { label: 'प्रक्रिया में', className: 'badge-processing', icon: AlertCircle },
      completed: { label: 'पूर्ण', className: 'badge-completed', icon: CheckCircle2 },
      rejected: { label: 'अस्वीकृत', className: 'badge-rejected', icon: AlertCircle }
    };
    const config = statusMap[status] || statusMap.pending;
    return (
      <Badge className={config.className}>
        <config.icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const stats = [
    { label: 'कुल आवेदन', value: applications.length, icon: FileText, color: 'text-blue-500' },
    { label: 'भुगतान बाकी', value: applications.filter(a => a.payment_status === 'pending').length, icon: Clock, color: 'text-yellow-500' },
    { label: 'प्रक्रिया में', value: applications.filter(a => a.application_status === 'processing').length, icon: AlertCircle, color: 'text-orange-500' },
    { label: 'पूर्ण', value: applications.filter(a => a.application_status === 'completed').length, icon: CheckCircle2, color: 'text-green-500' }
  ];

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
            नमस्ते, {user?.name}! 👋
          </h1>
          <p className="text-muted-foreground mt-1">
            आपके डैशबोर्ड में आपका स्वागत है
          </p>
        </div>

        {/* WhatsApp Connect Banner */}
        {!user?.whatsapp_connected && (
          <Card className="mb-8 bg-[#25D366]/10 border-[#25D366]/30">
            <CardContent className="flex items-center justify-between p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-[#25D366] flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold">WhatsApp से जुड़ें</h3>
                  <p className="text-sm text-muted-foreground">नई नौकरी और योजना की जानकारी सीधे पाएं</p>
                </div>
              </div>
              <a 
                href={`https://wa.me/916200184827?text=नमस्ते! मेरा नंबर ${user?.phone} है। मुझे Digital Sahayak से जोड़ें।`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button className="bg-[#25D366] hover:bg-[#25D366]/90 rounded-full gap-2" data-testid="connect-whatsapp-btn">
                  <MessageCircle className="w-4 h-4" />
                  जुड़ें
                </Button>
              </a>
            </CardContent>
          </Card>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, idx) => (
            <Card key={idx}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div className="text-2xl font-bold" style={{ fontFamily: 'Outfit' }}>{stat.value}</div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          <Link to="/jobs">
            <Card className="hover:shadow-md transition-all hover:-translate-y-1 cursor-pointer">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Briefcase className="w-7 h-7 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">नौकरी देखें</h3>
                  <p className="text-sm text-muted-foreground">नई सरकारी नौकरी अलर्ट</p>
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>
          <Link to="/yojana">
            <Card className="hover:shadow-md transition-all hover:-translate-y-1 cursor-pointer">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="w-14 h-14 rounded-xl bg-accent/10 flex items-center justify-center">
                  <Building2 className="w-7 h-7 text-accent" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">योजनाएं देखें</h3>
                  <p className="text-sm text-muted-foreground">सरकारी योजनाओं का लाभ उठाएं</p>
                </div>
                <ArrowRight className="w-5 h-5 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>
        </div>

        {/* Applications List */}
        <Card>
          <CardHeader>
            <CardTitle>मेरे आवेदन</CardTitle>
            <CardDescription>आपके सभी आवेदनों की स्थिति</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />
                ))}
              </div>
            ) : applications.length > 0 ? (
              <div className="space-y-4">
                {applications.map((app) => (
                  <div 
                    key={app.id}
                    className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                    data-testid={`application-${app.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        app.item_type === 'job' ? 'bg-primary/10' : 'bg-accent/10'
                      }`}>
                        {app.item_type === 'job' ? (
                          <Briefcase className="w-5 h-5 text-primary" />
                        ) : (
                          <Building2 className="w-5 h-5 text-accent" />
                        )}
                      </div>
                      <div>
                        <h4 className="font-medium">{app.item_title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {new Date(app.created_at).toLocaleDateString('hi-IN')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="flex items-center gap-1 font-medium">
                          <IndianRupee className="w-4 h-4" />
                          {app.total_fee}
                        </div>
                        <p className="text-xs text-muted-foreground">कुल शुल्क</p>
                      </div>
                      {getStatusBadge(app.application_status)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="font-semibold mb-2">अभी कोई आवेदन नहीं</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  नौकरी या योजना के लिए आवेदन करें
                </p>
                <div className="flex justify-center gap-3">
                  <Link to="/jobs">
                    <Button variant="outline" className="rounded-full gap-2">
                      <Briefcase className="w-4 h-4" />
                      नौकरी देखें
                    </Button>
                  </Link>
                  <Link to="/yojana">
                    <Button className="rounded-full gap-2">
                      <Building2 className="w-4 h-4" />
                      योजनाएं देखें
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
