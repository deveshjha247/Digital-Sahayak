import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import JobCard from '../components/JobCard';
import { Search, Filter, Briefcase, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const JobsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    category: searchParams.get('category') || 'all',
    state: searchParams.get('state') || 'all'
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.job_categories || []);
      setStates(res.data.states || []);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.category && filters.category !== 'all') params.append('category', filters.category);
      if (filters.state && filters.state !== 'all') params.append('state', filters.state);
      
      const res = await axios.get(`${API}/jobs?${params.toString()}`);
      setJobs(res.data.jobs || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Error fetching jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchParams({ ...filters });
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    setSearchParams(newFilters);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-secondary text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Badge className="bg-primary/20 text-primary-foreground mb-4">नौकरी अलर्ट</Badge>
          <h1 className="text-3xl md:text-4xl font-bold mb-2" style={{ fontFamily: 'Outfit' }}>
            सरकारी नौकरी खोजें
          </h1>
          <p className="text-white/70 max-w-2xl">
            Railway, Bank, SSC, UPSC, State PSC और अन्य सरकारी नौकरियों की जानकारी एक जगह
          </p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-card border-b sticky top-16 z-40 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="नौकरी खोजें... (जैसे: Railway, SSC, Teacher)"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10"
                data-testid="job-search-input"
              />
            </div>
            <Select value={filters.category} onValueChange={(v) => handleFilterChange('category', v)}>
              <SelectTrigger className="w-full md:w-48" data-testid="job-category-filter">
                <SelectValue placeholder="श्रेणी चुनें" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">सभी श्रेणी</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>
                    {cat.name_hi || cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filters.state} onValueChange={(v) => handleFilterChange('state', v)}>
              <SelectTrigger className="w-full md:w-48" data-testid="job-state-filter">
                <SelectValue placeholder="राज्य चुनें" />
              </SelectTrigger>
              <SelectContent>
                {states.map((state) => (
                  <SelectItem key={state.id} value={state.id}>
                    {state.name_hi || state.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="submit" className="rounded-full gap-2" data-testid="job-search-btn">
              <Search className="w-4 h-4" /> खोजें
            </Button>
          </form>
        </div>
      </div>

      {/* Results */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <p className="text-muted-foreground">
            <span className="font-semibold text-foreground">{total}</span> नौकरियां मिलीं
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : jobs.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Briefcase className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">कोई नौकरी नहीं मिली</h3>
            <p className="text-muted-foreground">
              अलग फ़िल्टर या खोज शब्द आज़माएं
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsPage;
