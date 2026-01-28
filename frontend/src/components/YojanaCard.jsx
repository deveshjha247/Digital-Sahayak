import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Building2, FileCheck, IndianRupee, ArrowRight, CheckCircle2 } from 'lucide-react';

const YojanaCard = ({ yojana, language = 'hi' }) => {
  const isHindi = language === 'hi';

  const getCategoryColor = (category) => {
    const colors = {
      welfare: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
      education: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      agriculture: 'bg-lime-100 text-lime-800 dark:bg-lime-900 dark:text-lime-200',
      housing: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
      health: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      women: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
      pension: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      employment: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
    };
    return colors[category] || colors.welfare;
  };

  return (
    <div 
      className="bg-card border-l-4 border-l-primary rounded-r-xl shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 overflow-hidden"
      data-testid={`yojana-card-${yojana.id}`}
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex-1">
            <Badge className={`${getCategoryColor(yojana.category)} mb-2`}>
              {isHindi ? {
                welfare: 'कल्याण',
                education: 'शिक्षा',
                agriculture: 'कृषि',
                housing: 'आवास',
                health: 'स्वास्थ्य',
                women: 'महिला',
                pension: 'पेंशन',
                employment: 'रोजगार'
              }[yojana.category] : yojana.category?.toUpperCase()}
            </Badge>
            <h3 className="font-bold text-lg leading-tight">
              {isHindi && yojana.name_hi ? yojana.name_hi : yojana.name}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-muted-foreground">
              <Building2 className="w-4 h-4" />
              <span className="text-sm">
                {isHindi && yojana.ministry_hi ? yojana.ministry_hi : yojana.ministry}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-primary font-bold">
              <IndianRupee className="w-4 h-4" />
              <span>{yojana.service_fee || 20}</span>
            </div>
            <div className="text-xs text-muted-foreground">सेवा शुल्क</div>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4 hindi-text">
          {isHindi && yojana.description_hi ? yojana.description_hi : yojana.description}
        </p>

        {/* Benefits Preview */}
        <div className="bg-accent/10 rounded-lg p-3 mb-4">
          <p className="text-xs font-medium text-accent mb-2 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> मुख्य लाभ
          </p>
          <p className="text-sm line-clamp-2 hindi-text">
            {isHindi && yojana.benefits_hi ? yojana.benefits_hi : yojana.benefits}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileCheck className="w-4 h-4" />
            <span>{yojana.documents_required?.length || 0} दस्तावेज़ आवश्यक</span>
          </div>
          <Link to={`/yojana/${yojana.id}`}>
            <Button size="sm" variant="outline" className="rounded-full gap-1" data-testid={`yojana-view-${yojana.id}`}>
              आवेदन करें <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default YojanaCard;
