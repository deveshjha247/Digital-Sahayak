import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Briefcase, Building2, Users, IndianRupee, Plus, Loader2, 
  BarChart3, FileText, Settings, Trash2, Edit, RefreshCw, Globe
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const AdminPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [jobDialogOpen, setJobDialogOpen] = useState(false);
  const [yojanaDialogOpen, setYojanaDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [jobForm, setJobForm] = useState({
    title: '', title_hi: '', organization: '', organization_hi: '',
    description: '', description_hi: '', qualification: '', qualification_hi: '',
    vacancies: '', salary: '', age_limit: '', last_date: '',
    apply_link: '', category: 'government', state: 'all'
  });

  const [yojanaForm, setYojanaForm] = useState({
    name: '', name_hi: '', ministry: '', ministry_hi: '',
    description: '', description_hi: '', benefits: '', benefits_hi: '',
    eligibility: '', eligibility_hi: '', documents_required: '',
    apply_link: '', category: 'welfare', state: 'all',
    govt_fee: '', service_fee: '20'
  });

  useEffect(() => {
    if (!user?.is_admin) {
      toast.error('Admin access required');
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [statsRes, appsRes] = await Promise.all([
        axios.get(`${API}/admin/stats`),
        axios.get(`${API}/admin/applications?limit=20`)
      ]);
      setStats(statsRes.data);
      setApplications(appsRes.data.applications || []);
    } catch (err) {
      console.error('Error fetching admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API}/jobs`, {
        ...jobForm,
        vacancies: parseInt(jobForm.vacancies) || 0
      });
      toast.success('नौकरी अलर्ट जोड़ी गई!');
      setJobDialogOpen(false);
      setJobForm({
        title: '', title_hi: '', organization: '', organization_hi: '',
        description: '', description_hi: '', qualification: '', qualification_hi: '',
        vacancies: '', salary: '', age_limit: '', last_date: '',
        apply_link: '', category: 'government', state: 'all'
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'त्रुटि हुई');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateYojana = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await axios.post(`${API}/yojana`, {
        ...yojanaForm,
        documents_required: yojanaForm.documents_required.split('\n').filter(d => d.trim()),
        govt_fee: parseFloat(yojanaForm.govt_fee) || 0,
        service_fee: parseFloat(yojanaForm.service_fee) || 20
      });
      toast.success('योजना जोड़ी गई!');
      setYojanaDialogOpen(false);
      setYojanaForm({
        name: '', name_hi: '', ministry: '', ministry_hi: '',
        description: '', description_hi: '', benefits: '', benefits_hi: '',
        eligibility: '', eligibility_hi: '', documents_required: '',
        apply_link: '', category: 'welfare', state: 'all',
        govt_fee: '', service_fee: '20'
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'त्रुटि हुई');
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async (appId, status) => {
    try {
      await axios.put(`${API}/admin/applications/${appId}/status`, { status });
      toast.success('स्थिति अपडेट की गई');
      fetchData();
    } catch (err) {
      toast.error('अपडेट में त्रुटि');
    }
  };

  const handleScrapeJobs = async () => {
    setScraping(true);
    try {
      await axios.post(`${API}/admin/scrape-jobs`);
      toast.success('Job scraping शुरू हो गई! कुछ समय बाद रिफ्रेश करें।');
      // Wait a bit and refresh
      setTimeout(() => {
        fetchData();
      }, 5000);
    } catch (err) {
      toast.error('Scraping में त्रुटि हुई');
    } finally {
      setScraping(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold" style={{ fontFamily: 'Outfit' }}>
              Admin Dashboard
            </h1>
            <p className="text-muted-foreground">Manage jobs, yojanas, and applications</p>
          </div>
          <div className="flex gap-3">
            <Dialog open={jobDialogOpen} onOpenChange={setJobDialogOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full gap-2" data-testid="add-job-btn">
                  <Plus className="w-4 h-4" />
                  Add Job
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>नई नौकरी जोड़ें</DialogTitle>
                  <DialogDescription>नई नौकरी अलर्ट बनाएं</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateJob} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Title (English)</Label>
                      <Input value={jobForm.title} onChange={(e) => setJobForm({...jobForm, title: e.target.value})} required />
                    </div>
                    <div>
                      <Label>शीर्षक (हिंदी)</Label>
                      <Input value={jobForm.title_hi} onChange={(e) => setJobForm({...jobForm, title_hi: e.target.value})} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Organization</Label>
                      <Input value={jobForm.organization} onChange={(e) => setJobForm({...jobForm, organization: e.target.value})} required />
                    </div>
                    <div>
                      <Label>संगठन (हिंदी)</Label>
                      <Input value={jobForm.organization_hi} onChange={(e) => setJobForm({...jobForm, organization_hi: e.target.value})} />
                    </div>
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Textarea value={jobForm.description} onChange={(e) => setJobForm({...jobForm, description: e.target.value})} rows={3} required />
                  </div>
                  <div>
                    <Label>Qualification</Label>
                    <Textarea value={jobForm.qualification} onChange={(e) => setJobForm({...jobForm, qualification: e.target.value})} rows={2} required />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Vacancies</Label>
                      <Input type="number" value={jobForm.vacancies} onChange={(e) => setJobForm({...jobForm, vacancies: e.target.value})} />
                    </div>
                    <div>
                      <Label>Salary</Label>
                      <Input value={jobForm.salary} onChange={(e) => setJobForm({...jobForm, salary: e.target.value})} placeholder="e.g., 25000-50000" />
                    </div>
                    <div>
                      <Label>Age Limit</Label>
                      <Input value={jobForm.age_limit} onChange={(e) => setJobForm({...jobForm, age_limit: e.target.value})} placeholder="e.g., 18-35" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Last Date</Label>
                      <Input value={jobForm.last_date} onChange={(e) => setJobForm({...jobForm, last_date: e.target.value})} placeholder="e.g., 31 Jan 2025" required />
                    </div>
                    <div>
                      <Label>Category</Label>
                      <Select value={jobForm.category} onValueChange={(v) => setJobForm({...jobForm, category: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="government">Government</SelectItem>
                          <SelectItem value="railway">Railway</SelectItem>
                          <SelectItem value="bank">Bank</SelectItem>
                          <SelectItem value="ssc">SSC</SelectItem>
                          <SelectItem value="upsc">UPSC</SelectItem>
                          <SelectItem value="state">State</SelectItem>
                          <SelectItem value="defence">Defence</SelectItem>
                          <SelectItem value="police">Police</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Apply Link</Label>
                    <Input value={jobForm.apply_link} onChange={(e) => setJobForm({...jobForm, apply_link: e.target.value})} placeholder="https://..." required />
                  </div>
                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Create Job
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            <Dialog open={yojanaDialogOpen} onOpenChange={setYojanaDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="rounded-full gap-2" data-testid="add-yojana-btn">
                  <Plus className="w-4 h-4" />
                  Add Yojana
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>नई योजना जोड़ें</DialogTitle>
                  <DialogDescription>नई सरकारी योजना बनाएं</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateYojana} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Name (English)</Label>
                      <Input value={yojanaForm.name} onChange={(e) => setYojanaForm({...yojanaForm, name: e.target.value})} required />
                    </div>
                    <div>
                      <Label>नाम (हिंदी)</Label>
                      <Input value={yojanaForm.name_hi} onChange={(e) => setYojanaForm({...yojanaForm, name_hi: e.target.value})} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Ministry</Label>
                      <Input value={yojanaForm.ministry} onChange={(e) => setYojanaForm({...yojanaForm, ministry: e.target.value})} required />
                    </div>
                    <div>
                      <Label>मंत्रालय (हिंदी)</Label>
                      <Input value={yojanaForm.ministry_hi} onChange={(e) => setYojanaForm({...yojanaForm, ministry_hi: e.target.value})} />
                    </div>
                  </div>
                  <div>
                    <Label>Description</Label>
                    <Textarea value={yojanaForm.description} onChange={(e) => setYojanaForm({...yojanaForm, description: e.target.value})} rows={3} required />
                  </div>
                  <div>
                    <Label>Benefits</Label>
                    <Textarea value={yojanaForm.benefits} onChange={(e) => setYojanaForm({...yojanaForm, benefits: e.target.value})} rows={2} required />
                  </div>
                  <div>
                    <Label>Eligibility</Label>
                    <Textarea value={yojanaForm.eligibility} onChange={(e) => setYojanaForm({...yojanaForm, eligibility: e.target.value})} rows={2} required />
                  </div>
                  <div>
                    <Label>Documents Required (one per line)</Label>
                    <Textarea value={yojanaForm.documents_required} onChange={(e) => setYojanaForm({...yojanaForm, documents_required: e.target.value})} rows={3} placeholder="Aadhaar Card&#10;Income Certificate&#10;..." />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Category</Label>
                      <Select value={yojanaForm.category} onValueChange={(v) => setYojanaForm({...yojanaForm, category: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="welfare">Welfare</SelectItem>
                          <SelectItem value="education">Education</SelectItem>
                          <SelectItem value="agriculture">Agriculture</SelectItem>
                          <SelectItem value="housing">Housing</SelectItem>
                          <SelectItem value="health">Health</SelectItem>
                          <SelectItem value="women">Women & Child</SelectItem>
                          <SelectItem value="pension">Pension</SelectItem>
                          <SelectItem value="employment">Employment</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Govt Fee (₹)</Label>
                      <Input type="number" value={yojanaForm.govt_fee} onChange={(e) => setYojanaForm({...yojanaForm, govt_fee: e.target.value})} placeholder="0" />
                    </div>
                    <div>
                      <Label>Service Fee (₹)</Label>
                      <Input type="number" value={yojanaForm.service_fee} onChange={(e) => setYojanaForm({...yojanaForm, service_fee: e.target.value})} placeholder="20" />
                    </div>
                  </div>
                  <div>
                    <Label>Apply Link</Label>
                    <Input value={yojanaForm.apply_link} onChange={(e) => setYojanaForm({...yojanaForm, apply_link: e.target.value})} placeholder="https://..." required />
                  </div>
                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                    Create Yojana
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <Users className="w-6 h-6 text-blue-500 mb-2" />
              <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
              <p className="text-sm text-muted-foreground">Total Users</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <Briefcase className="w-6 h-6 text-primary mb-2" />
              <div className="text-2xl font-bold">{stats?.total_jobs || 0}</div>
              <p className="text-sm text-muted-foreground">Jobs</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <Building2 className="w-6 h-6 text-accent mb-2" />
              <div className="text-2xl font-bold">{stats?.total_yojana || 0}</div>
              <p className="text-sm text-muted-foreground">Yojanas</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <FileText className="w-6 h-6 text-purple-500 mb-2" />
              <div className="text-2xl font-bold">{stats?.total_applications || 0}</div>
              <p className="text-sm text-muted-foreground">Applications</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <IndianRupee className="w-6 h-6 text-green-500 mb-2" />
              <div className="text-2xl font-bold">₹{stats?.total_revenue || 0}</div>
              <p className="text-sm text-muted-foreground">Revenue</p>
            </CardContent>
          </Card>
        </div>

        {/* Applications Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Applications</CardTitle>
            <CardDescription>Manage and process applications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {applications.map((app) => (
                <div 
                  key={app.id}
                  className="flex items-center justify-between p-4 bg-muted/30 rounded-lg"
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
                        {app.user_details?.name} • {app.user_details?.phone}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge className={app.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                      {app.payment_status === 'paid' ? 'Paid' : 'Pending'}
                    </Badge>
                    <Select 
                      value={app.application_status} 
                      onValueChange={(v) => handleUpdateStatus(app.id, v)}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="processing">Processing</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="rejected">Rejected</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              ))}
              {applications.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No applications yet
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPage;
