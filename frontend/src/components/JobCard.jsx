import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Calendar, MapPin, Users, Building2, IndianRupee, ArrowRight, Clock } from 'lucide-react';

const JobCard = ({ job, language = 'hi' }) => {
  const isHindi = language === 'hi';
  
  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('hi-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      government: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      railway: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      bank: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      ssc: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      upsc: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      state: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
      defence: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
      police: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
    };
    return colors[category] || colors.government;
  };

  return (
    <div 
      className="ticket-card bg-card border border-border/50 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group"
      data-testid={`job-card-${job.id}`}
    >
      {/* Top Section with Category */}
      <div className="p-4 border-b border-dashed border-border/50">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <Badge className={`${getCategoryColor(job.category)} mb-2`}>
              {job.category?.toUpperCase()}
            </Badge>
            <h3 className="font-bold text-lg line-clamp-2 group-hover:text-primary transition-colors">
              {isHindi && job.title_hi ? job.title_hi : job.title}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-muted-foreground">
              <Building2 className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm truncate">
                {isHindi && job.organization_hi ? job.organization_hi : job.organization}
              </span>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-2xl font-bold text-primary">{job.vacancies || '—'}</div>
            <div className="text-xs text-muted-foreground">पद</div>
          </div>
        </div>
      </div>

      {/* Middle Section */}
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{job.state === 'all' ? 'संपूर्ण भारत' : job.state}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <IndianRupee className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{job.salary || 'विवरण देखें'}</span>
          </div>
        </div>

        <p className="text-sm text-muted-foreground line-clamp-2 hindi-text">
          {isHindi && job.qualification_hi ? job.qualification_hi : job.qualification}
        </p>
      </div>

      {/* Bottom Section */}
      <div className="p-4 bg-muted/30 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <Clock className="w-4 h-4 text-destructive" />
          <span className="text-destructive font-medium">
            अंतिम तिथि: {job.last_date}
          </span>
        </div>
        <Link to={`/jobs/${job.id}`}>
          <Button size="sm" className="rounded-full gap-1" data-testid={`job-view-${job.id}`}>
            देखें <ArrowRight className="w-4 h-4" />
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default JobCard;
