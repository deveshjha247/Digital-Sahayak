import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import JobCard from '../components/JobCard';
import { 
  Sparkles, Briefcase, AlertCircle, ArrowRight, User, 
  Loader2, RefreshCw, Target, TrendingUp
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const RecommendationsPage = () => {
  const { user } = useAuth();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState(null);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/recommendations?limit=10`);
      setRecommendations(res.data.recommendations || []);
      setUserProfile(res.data.user_profile);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const profileComplete = userProfile?.education_level && userProfile?.state && userProfile?.age;

  const getMatchColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-orange-600 bg-orange-100';
  };

  const getMatchLabel = (score) => {
    if (score >= 80) return 'उत्कृष्ट मैच';
    if (score >= 60) return 'अच्छा मैच';
    return 'संभावित मैच';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary to-primary/80 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="w-8 h-8" />
            <Badge className="bg-white/20 text-white">AI-Powered</Badge>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2" style={{ fontFamily: 'Outfit' }}>
            आपके लिए सुझाई गई नौकरियां
          </h1>
          <p className="text-white/80 max-w-2xl">
            आपकी शिक्षा, आयु और राज्य के आधार पर AI द्वारा चुनी गई सबसे उपयुक्त नौकरियां
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Profile Status */}
        {!profileComplete && (
          <Card className="mb-8 border-primary/30 bg-primary/5">
            <CardContent className="p-6">
              <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                  <User className="w-7 h-7 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg mb-1">प्रोफ़ाइल अधूरी है</h3>
                  <p className="text-muted-foreground mb-3">
                    बेहतर नौकरी सुझाव पाने के लिए अपनी शिक्षा, आयु और राज्य की जानकारी भरें।
                    पूरी प्रोफ़ाइल से 80%+ मैच वाली नौकरियां मिलती हैं।
                  </p>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 max-w-xs">
                      <Progress value={userProfile?.education_level ? 33 : 0 + userProfile?.state ? 33 : 0 + userProfile?.age ? 34 : 0} />
                    </div>
                    <Link to="/profile">
                      <Button className="rounded-full gap-2" data-testid="complete-profile-btn">
                        प्रोफ़ाइल पूरी करें <ArrowRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* User Profile Summary */}
        {profileComplete && (
          <Card className="mb-8">
            <CardContent className="p-6">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  <span className="font-medium">आपकी प्रोफ़ाइल:</span>
                </div>
                <Badge variant="outline" className="text-sm">
                  शिक्षा: {userProfile?.education_level === '10th' ? '10वीं' : 
                          userProfile?.education_level === '12th' ? '12वीं' :
                          userProfile?.education_level === 'graduate' ? 'स्नातक' : 'परास्नातक'}
                </Badge>
                <Badge variant="outline" className="text-sm">
                  राज्य: {userProfile?.state === 'all' ? 'भारत' : userProfile?.state}
                </Badge>
                <Badge variant="outline" className="text-sm">
                  आयु: {userProfile?.age} वर्ष
                </Badge>
                {userProfile?.preferred_categories?.length > 0 && (
                  <Badge variant="outline" className="text-sm">
                    {userProfile.preferred_categories.length} श्रेणियां चुनी
                  </Badge>
                )}
                <Link to="/profile" className="ml-auto">
                  <Button variant="ghost" size="sm" className="gap-1">
                    <RefreshCw className="w-4 h-4" /> अपडेट करें
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Refresh Button */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            {recommendations.length} सुझाई गई नौकरियां
          </h2>
          <Button 
            variant="outline" 
            onClick={fetchRecommendations} 
            disabled={loading}
            className="rounded-full gap-2"
            data-testid="refresh-recommendations-btn"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            रिफ्रेश
          </Button>
        </div>

        {/* Recommendations */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-4" />
              <p className="text-muted-foreground">AI सुझाव लोड हो रहे हैं...</p>
            </div>
          </div>
        ) : recommendations.length > 0 ? (
          <div className="space-y-6">
            {recommendations.map((job, index) => (
              <div key={job.id} className="relative">
                {/* Match Score Badge */}
                <div className="absolute -top-3 -left-2 z-10">
                  <Badge className={`${getMatchColor(job.match_score)} px-3 py-1 shadow-md`}>
                    {job.match_score}% {getMatchLabel(job.match_score)}
                  </Badge>
                </div>
                
                <Card className="overflow-hidden hover:shadow-lg transition-all">
                  <CardContent className="p-0">
                    <div className="flex flex-col md:flex-row">
                      {/* Main Job Info */}
                      <div className="flex-1 p-6 pt-8">
                        <div className="flex items-start justify-between gap-4 mb-4">
                          <div>
                            <Badge className="mb-2">{job.category?.toUpperCase()}</Badge>
                            <h3 className="font-bold text-xl mb-1">
                              {job.title_hi || job.title}
                            </h3>
                            <p className="text-muted-foreground">
                              {job.organization_hi || job.organization}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-bold text-primary">{job.vacancies || '—'}</div>
                            <div className="text-xs text-muted-foreground">पद</div>
                          </div>
                        </div>
                        
                        {/* AI Reason */}
                        {job.ai_reason && (
                          <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 mb-4">
                            <div className="flex items-start gap-2">
                              <Sparkles className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                              <p className="text-sm hindi-text">{job.ai_reason}</p>
                            </div>
                          </div>
                        )}
                        
                        {/* Match Reason */}
                        {job.match_reason && !job.ai_reason && (
                          <div className="bg-muted/50 rounded-lg p-3 mb-4">
                            <p className="text-sm text-muted-foreground hindi-text">
                              {job.match_reason}
                            </p>
                          </div>
                        )}
                        
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>अंतिम तिथि: <strong className="text-destructive">{job.last_date}</strong></span>
                          {job.salary && <span>वेतन: {job.salary}</span>}
                        </div>
                      </div>
                      
                      {/* Action */}
                      <div className="md:w-48 p-6 bg-muted/30 flex flex-col justify-center items-center gap-3">
                        <Link to={`/jobs/${job.id}`} className="w-full">
                          <Button className="w-full rounded-full gap-2" data-testid={`view-job-${job.id}`}>
                            विवरण देखें <ArrowRight className="w-4 h-4" />
                          </Button>
                        </Link>
                        {job.apply_link && (
                          <a href={job.apply_link} target="_blank" rel="noopener noreferrer" className="w-full">
                            <Button variant="outline" className="w-full rounded-full">
                              आवेदन करें
                            </Button>
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
        ) : (
          <Card className="text-center py-16">
            <CardContent>
              <AlertCircle className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-xl font-semibold mb-2">कोई सुझाव नहीं मिला</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                अभी कोई नौकरी आपकी प्रोफ़ाइल से मेल नहीं खाती। 
                कृपया अपनी प्रोफ़ाइल अपडेट करें या बाद में देखें।
              </p>
              <div className="flex justify-center gap-4">
                <Link to="/profile">
                  <Button variant="outline" className="rounded-full">
                    प्रोफ़ाइल अपडेट करें
                  </Button>
                </Link>
                <Link to="/jobs">
                  <Button className="rounded-full">
                    सभी नौकरियां देखें
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;
