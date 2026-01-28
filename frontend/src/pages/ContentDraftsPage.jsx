import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  FileEdit, Trash2, Check, X, Loader2, RefreshCw, Sparkles, 
  ExternalLink, Eye, Globe, Send
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const ContentDraftsPage = () => {
  const { user } = useAuth();
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [rewriting, setRewriting] = useState(null);
  const [publishing, setPublishing] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    fetchDrafts();
  }, [activeTab]);

  const fetchDrafts = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/content-drafts?status=${activeTab}&limit=50`);
      setDrafts(res.data.drafts || []);
    } catch (err) {
      console.error('Error fetching drafts:', err);
      toast.error('ड्राफ्ट लोड नहीं हो पाए');
    } finally {
      setLoading(false);
    }
  };

  const handleRewrite = async (draftId) => {
    setRewriting(draftId);
    try {
      const res = await axios.post(`${API}/admin/content-drafts/${draftId}/rewrite`);
      toast.success('AI ने content rewrite कर दिया!');
      fetchDrafts();
      if (selectedDraft?.id === draftId) {
        setSelectedDraft(res.data.draft);
      }
    } catch (err) {
      toast.error('Rewrite में त्रुटि हुई');
    } finally {
      setRewriting(null);
    }
  };

  const handlePublish = async (draftId) => {
    setPublishing(draftId);
    try {
      const res = await axios.post(`${API}/admin/content-drafts/${draftId}/publish`);
      toast.success(`पब्लिश हो गया! Slug: ${res.data.slug}`);
      fetchDrafts();
      setEditDialogOpen(false);
    } catch (err) {
      toast.error('पब्लिश में त्रुटि हुई');
    } finally {
      setPublishing(null);
    }
  };

  const handleDelete = async (draftId) => {
    if (!confirm('क्या आप इस ड्राफ्ट को हटाना चाहते हैं?')) return;
    
    try {
      await axios.delete(`${API}/admin/content-drafts/${draftId}`);
      toast.success('ड्राफ्ट हटा दिया गया');
      fetchDrafts();
      setEditDialogOpen(false);
    } catch (err) {
      toast.error('हटाने में त्रुटि हुई');
    }
  };

  const handleUpdateDraft = async () => {
    if (!selectedDraft) return;
    
    try {
      await axios.put(`${API}/admin/content-drafts/${selectedDraft.id}`, selectedDraft);
      toast.success('ड्राफ्ट अपडेट हो गया');
      fetchDrafts();
    } catch (err) {
      toast.error('अपडेट में त्रुटि हुई');
    }
  };

  const openEditDialog = (draft) => {
    setSelectedDraft({ ...draft });
    setEditDialogOpen(true);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3" style={{ fontFamily: 'Outfit' }}>
              <FileEdit className="w-8 h-8 text-primary" />
              Content Drafts
            </h1>
            <p className="text-muted-foreground mt-1">
              Scraped content को review और edit करें, फिर publish करें
            </p>
          </div>
          <Button onClick={fetchDrafts} variant="outline" className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList>
            <TabsTrigger value="pending" className="gap-2">
              Pending Review
              <Badge variant="secondary" className="ml-1">
                {activeTab === 'pending' ? drafts.length : ''}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="published">Published</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Drafts List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : drafts.length > 0 ? (
          <div className="space-y-4">
            {drafts.map((draft) => (
              <Card key={draft.id} className="hover:shadow-md transition-all">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant={draft.is_rewritten ? 'default' : 'secondary'}>
                          {draft.is_rewritten ? (
                            <><Sparkles className="w-3 h-3 mr-1" /> AI Rewritten</>
                          ) : (
                            'Original'
                          )}
                        </Badge>
                        <Badge variant="outline">{draft.category}</Badge>
                        <Badge variant="outline">{draft.state}</Badge>
                      </div>
                      
                      <h3 className="font-bold text-lg mb-1 line-clamp-1">
                        {draft.title_hi || draft.title}
                      </h3>
                      
                      <p className="text-sm text-muted-foreground mb-2">
                        {draft.organization_hi || draft.organization || 'Unknown Source'}
                      </p>
                      
                      <p className="text-sm text-muted-foreground line-clamp-2 hindi-text">
                        {draft.description_hi || draft.description || 'No description'}
                      </p>
                      
                      <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                        <span>Slug: <code className="bg-muted px-1 rounded">{draft.slug || 'auto'}</code></span>
                        {draft.source_url && (
                          <a 
                            href={draft.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 hover:text-primary"
                          >
                            <ExternalLink className="w-3 h-3" /> Source
                          </a>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex flex-col gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => openEditDialog(draft)}
                        className="gap-1"
                      >
                        <Eye className="w-4 h-4" /> Edit
                      </Button>
                      
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleRewrite(draft.id)}
                        disabled={rewriting === draft.id}
                        className="gap-1"
                      >
                        {rewriting === draft.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Sparkles className="w-4 h-4" />
                        )}
                        AI Rewrite
                      </Button>
                      
                      {draft.status === 'pending' && (
                        <Button 
                          size="sm"
                          onClick={() => handlePublish(draft.id)}
                          disabled={publishing === draft.id}
                          className="gap-1"
                        >
                          {publishing === draft.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                          Publish
                        </Button>
                      )}
                      
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => handleDelete(draft.id)}
                        className="gap-1"
                      >
                        <Trash2 className="w-4 h-4" /> Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="text-center py-16">
            <CardContent>
              <FileEdit className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-semibold mb-2">कोई ड्राफ्ट नहीं</h3>
              <p className="text-muted-foreground">
                Admin Panel से "Scrape Jobs" बटन दबाकर content scrape करें
              </p>
            </CardContent>
          </Card>
        )}

        {/* Edit Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Content Edit करें</DialogTitle>
              <DialogDescription>
                Content को अपने format में edit करें और publish करें। AI Rewrite से copyright-safe content बनाएं।
              </DialogDescription>
            </DialogHeader>
            
            {selectedDraft && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  {selectedDraft.is_rewritten && (
                    <Badge className="bg-green-100 text-green-800">
                      <Sparkles className="w-3 h-3 mr-1" /> AI Rewritten
                    </Badge>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Title (English)</Label>
                    <Input 
                      value={selectedDraft.title || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, title: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>शीर्षक (हिंदी)</Label>
                    <Input 
                      value={selectedDraft.title_hi || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, title_hi: e.target.value})}
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Custom URL Slug</Label>
                  <Input 
                    value={selectedDraft.slug || ''}
                    onChange={(e) => setSelectedDraft({...selectedDraft, slug: e.target.value})}
                    placeholder="e.g., br/bihar-railway-group-d-2025"
                  />
                  <p className="text-xs text-muted-foreground">
                    Final URL: /jobs/{selectedDraft.slug || 'auto-generated'}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Organization</Label>
                    <Input 
                      value={selectedDraft.organization || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, organization: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>संगठन (हिंदी)</Label>
                    <Input 
                      value={selectedDraft.organization_hi || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, organization_hi: e.target.value})}
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Description (Write in your own words - Copyright Safe)</Label>
                  <Textarea 
                    value={selectedDraft.description || ''}
                    onChange={(e) => setSelectedDraft({...selectedDraft, description: e.target.value})}
                    rows={4}
                    placeholder="अपने शब्दों में लिखें..."
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>विवरण (हिंदी)</Label>
                  <Textarea 
                    value={selectedDraft.description_hi || ''}
                    onChange={(e) => setSelectedDraft({...selectedDraft, description_hi: e.target.value})}
                    rows={4}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Meta Description (SEO)</Label>
                  <Input 
                    value={selectedDraft.meta_description || ''}
                    onChange={(e) => setSelectedDraft({...selectedDraft, meta_description: e.target.value})}
                    placeholder="150 characters for SEO"
                    maxLength={160}
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select 
                      value={selectedDraft.category}
                      onValueChange={(v) => setSelectedDraft({...selectedDraft, category: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="government">Government</SelectItem>
                        <SelectItem value="railway">Railway</SelectItem>
                        <SelectItem value="bank">Bank</SelectItem>
                        <SelectItem value="ssc">SSC</SelectItem>
                        <SelectItem value="upsc">UPSC</SelectItem>
                        <SelectItem value="police">Police</SelectItem>
                        <SelectItem value="defence">Defence</SelectItem>
                        <SelectItem value="state">State</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>State</Label>
                    <Select 
                      value={selectedDraft.state}
                      onValueChange={(v) => setSelectedDraft({...selectedDraft, state: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All India</SelectItem>
                        <SelectItem value="bihar">Bihar</SelectItem>
                        <SelectItem value="jharkhand">Jharkhand</SelectItem>
                        <SelectItem value="up">Uttar Pradesh</SelectItem>
                        <SelectItem value="mp">Madhya Pradesh</SelectItem>
                        <SelectItem value="rajasthan">Rajasthan</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Vacancies</Label>
                    <Input 
                      type="number"
                      value={selectedDraft.vacancies || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, vacancies: parseInt(e.target.value) || 0})}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Last Date</Label>
                    <Input 
                      value={selectedDraft.last_date || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, last_date: e.target.value})}
                      placeholder="e.g., 31 Jan 2025"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Apply Link</Label>
                    <Input 
                      value={selectedDraft.apply_link || ''}
                      onChange={(e) => setSelectedDraft({...selectedDraft, apply_link: e.target.value})}
                    />
                  </div>
                </div>
                
                {selectedDraft.source_url && (
                  <div className="bg-muted/50 p-3 rounded-lg">
                    <p className="text-xs text-muted-foreground">
                      <strong>Source Reference:</strong>{' '}
                      <a href={selectedDraft.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                        {selectedDraft.source_url}
                      </a>
                    </p>
                  </div>
                )}
                
                <div className="flex justify-between pt-4 border-t">
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      onClick={() => handleRewrite(selectedDraft.id)}
                      disabled={rewriting === selectedDraft.id}
                      className="gap-2"
                    >
                      {rewriting === selectedDraft.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4" />
                      )}
                      AI Rewrite (Copyright Safe)
                    </Button>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={handleUpdateDraft}>
                      Save Draft
                    </Button>
                    <Button 
                      onClick={() => handlePublish(selectedDraft.id)}
                      disabled={publishing === selectedDraft.id}
                      className="gap-2"
                    >
                      {publishing === selectedDraft.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                      Publish Now
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default ContentDraftsPage;
