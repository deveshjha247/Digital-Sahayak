import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import YojanaCard from '../components/YojanaCard';
import { Search, Building2, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const YojanaPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [yojanas, setYojanas] = useState([]);
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
    fetchYojanas();
  }, [filters]);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.yojana_categories || []);
      setStates(res.data.states || []);
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  const fetchYojanas = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.search) params.append('search', filters.search);
      if (filters.category && filters.category !== 'all') params.append('category', filters.category);
      if (filters.state && filters.state !== 'all') params.append('state', filters.state);
      
      const res = await axios.get(`${API}/yojana?${params.toString()}`);
      setYojanas(res.data.yojanas || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Error fetching yojanas:', err);
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
      <div className="bg-accent text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Badge className="bg-white/20 text-white mb-4">सरकारी योजनाएं</Badge>
          <h1 className="text-3xl md:text-4xl font-bold mb-2" style={{ fontFamily: 'Outfit' }}>
            योजनाएं खोजें और आवेदन करें
          </h1>
          <p className="text-white/80 max-w-2xl">
            PM आवास, किसान सम्मान निधि, शिक्षा छात्रवृत्ति और अन्य सरकारी योजनाओं का लाभ उठाएं
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
                placeholder="योजना खोजें... (जैसे: आवास, छात्रवृत्ति, पेंशन)"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10"
                data-testid="yojana-search-input"
              />
            </div>
            <Select value={filters.category} onValueChange={(v) => handleFilterChange('category', v)}>
              <SelectTrigger className="w-full md:w-48" data-testid="yojana-category-filter">
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
              <SelectTrigger className="w-full md:w-48" data-testid="yojana-state-filter">
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
            <Button type="submit" className="rounded-full gap-2 bg-accent hover:bg-accent/90" data-testid="yojana-search-btn">
              <Search className="w-4 h-4" /> खोजें
            </Button>
          </form>
        </div>
      </div>

      {/* Results */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <p className="text-muted-foreground">
            <span className="font-semibold text-foreground">{total}</span> योजनाएं मिलीं
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent" />
          </div>
        ) : yojanas.length > 0 ? (
          <div className="grid md:grid-cols-2 gap-6">
            {yojanas.map((yojana) => (
              <YojanaCard key={yojana.id} yojana={yojana} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Building2 className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">कोई योजना नहीं मिली</h3>
            <p className="text-muted-foreground">
              अलग फ़िल्टर या खोज शब्द आज़माएं
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default YojanaPage;
