import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AILearningPage() {
  const [prompt, setPrompt] = useState('');
  const [externalResponse, setExternalResponse] = useState('');
  const [aiName, setAiName] = useState('GitHub Copilot');
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [webSearchQuery, setWebSearchQuery] = useState('');
  const [webSearchResults, setWebSearchResults] = useState(null);

  // Learn from External AI
  const handleLearnFromExternal = async () => {
    if (!prompt || !externalResponse) {
      alert('Prompt and External AI Response both are required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/ai/learn-from-external', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          prompt,
          other_ai_response: externalResponse,
          ai_name: aiName,
          use_web_search: useWebSearch
        })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Generate with Learning
  const handleSmartGenerate = async () => {
    if (!prompt) {
      alert('Prompt is required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/ai/generate-smart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          prompt,
          use_web_search: useWebSearch 
        })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Web Search
  const handleWebSearch = async () => {
    if (!webSearchQuery) {
      alert('Search query is required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/ai/web-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          query: webSearchQuery,
          max_results: 5
        })
      });

      const data = await response.json();
      setWebSearchResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Get Learning Stats
  const handleGetStats = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/ai/learning-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-3xl">🧠 Self-Learning AI System</CardTitle>
            <CardDescription>
              An AI that learns from other AIs and improves itself with web search capability
            </CardDescription>
          </CardHeader>
        </Card>

        <Tabs defaultValue="learn" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="learn">Learn from AI</TabsTrigger>
            <TabsTrigger value="generate">Smart Generate</TabsTrigger>
            <TabsTrigger value="websearch">Web Search</TabsTrigger>
            <TabsTrigger value="stats">Learning Stats</TabsTrigger>
          </TabsList>

          {/* Learn from External AI */}
          <TabsContent value="learn">
            <Card>
              <CardHeader>
                <CardTitle>Learn from External AI</CardTitle>
                <CardDescription>
                  Paste responses from GitHub Copilot, ChatGPT, or any AI
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="ainame">AI Name</Label>
                  <Input
                    id="ainame"
                    value={aiName}
                    onChange={(e) => setAiName(e.target.value)}
                    placeholder="e.g., GitHub Copilot"
                  />
                </div>

                <div>
                  <Label htmlFor="prompt">Original Prompt/Question</Label>
                  <Textarea
                    id="prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="What did you ask?"
                    rows={3}
                  />
                </div>

                <div>
                  <Label htmlFor="external">External AI's Response</Label>
                  <Textarea
                    id="external"
                    value={externalResponse}
                    onChange={(e) => setExternalResponse(e.target.value)}
                    placeholder="What did the other AI respond?"
                    rows={6}
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="useWebSearch"
                    checked={useWebSearch}
                    onChange={(e) => setUseWebSearch(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="useWebSearch">
                    Use web search for additional context
                  </Label>
                </div>

                <Button
                  onClick={handleLearnFromExternal}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? 'Learning...' : '✨ Learn & Improve'}
                </Button>

                {result && result.success && (
                  <div className="space-y-4 mt-6">
                    <Alert>
                      <AlertDescription>
                        <strong>✅ Learning Successful!</strong>
                      </AlertDescription>
                    </Alert>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Analysis</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <strong className="text-green-600">✓ Strengths:</strong>
                          <ul className="list-disc ml-6 mt-1">
                            {result.analysis?.strengths?.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <strong className="text-orange-600">⚠ Weaknesses:</strong>
                          <ul className="list-disc ml-6 mt-1">
                            {result.analysis?.weaknesses?.map((w, i) => (
                              <li key={i}>{w}</li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <strong className="text-blue-600">+ Missing:</strong>
                          <ul className="list-disc ml-6 mt-1">
                            {result.analysis?.missing_aspects?.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-green-200 bg-green-50">
                      <CardHeader>
                        <CardTitle className="text-lg text-green-800">
                          🎯 Improved Response
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="whitespace-pre-wrap text-sm">
                          {result.improved_response}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Smart Generate */}
          <TabsContent value="generate">
            <Card>
              <CardHeader>
                <CardTitle>Smart Generation</CardTitle>
                <CardDescription>
                  Generate better responses using past learnings and project context
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="smartprompt">Your Question/Task</Label>
                  <Textarea
                    id="smartprompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="What do you want to do?"
                    rows={4}
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="useWebSearchGen"
                    checked={useWebSearch}
                    onChange={(e) => setUseWebSearch(e.target.checked)}
                    className="rounded"
                  />
                  <Label htmlFor="useWebSearchGen">
                    Search web for real-time information
                  </Label>
                </div>

                <Button
                  onClick={handleSmartGenerate}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? 'Generating...' : '🚀 Smart Generate'}
                </Button>

                {result && result.response && (
                  <Card className="border-blue-200 bg-blue-50">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">Response</CardTitle>
                        <div className="flex gap-2">
                          <Badge variant="secondary">
                            {result.learnings_applied} Learnings Applied
                          </Badge>
                          <Badge variant="default">
                            {Math.round(result.confidence * 100)}% Confidence
                          </Badge>
                          {result.used_web_search && (
                            <Badge variant="outline">🌐 Web Search Used</Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="whitespace-pre-wrap text-sm">
                        {result.response}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Web Search */}
          <TabsContent value="websearch">
            <Card>
              <CardHeader>
                <CardTitle>Web Search</CardTitle>
                <CardDescription>
                  Search the web for real-time information (uses DuckDuckGo)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="websearchquery">Search Query</Label>
                  <Input
                    id="websearchquery"
                    value={webSearchQuery}
                    onChange={(e) => setWebSearchQuery(e.target.value)}
                    placeholder="e.g., UPSC 2026 exam eligibility criteria"
                  />
                </div>

                <Button
                  onClick={handleWebSearch}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? 'Searching...' : '🔍 Search Web'}
                </Button>

                {webSearchResults && (
                  <div className="space-y-3 mt-4">
                    <Alert>
                      <AlertDescription>
                        Found {webSearchResults.count} results
                      </AlertDescription>
                    </Alert>
                    
                    {webSearchResults.results.map((result, idx) => (
                      <Card key={idx} className="border-l-4 border-l-blue-500">
                        <CardContent className="pt-4">
                          <h3 className="font-semibold text-blue-600 mb-1">
                            {result.title}
                          </h3>
                          {result.url && (
                            <a 
                              href={result.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-xs text-gray-500 hover:underline block mb-2"
                            >
                              {result.url}
                            </a>
                          )}
                          <p className="text-sm text-gray-700">
                            {result.snippet}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Learning Stats */}
          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle>Learning Statistics</CardTitle>
                <CardDescription>
                  How much the AI has learned
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={handleGetStats} disabled={loading}>
                  {loading ? 'Loading...' : '📊 Get Stats'}
                </Button>

                {stats && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl">
                          {stats.total_learnings}
                        </CardTitle>
                        <CardDescription>Total Learnings</CardDescription>
                      </CardHeader>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl">
                          {Math.round(stats.average_improvement_score)}%
                        </CardTitle>
                        <CardDescription>Avg Improvement Score</CardDescription>
                      </CardHeader>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl">
                          {stats.learning_rate}
                        </CardTitle>
                        <CardDescription>Learning Rate</CardDescription>
                      </CardHeader>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
