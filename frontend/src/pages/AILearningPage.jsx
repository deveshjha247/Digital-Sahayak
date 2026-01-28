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
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  // Learn from External AI
  const handleLearnFromExternal = async () => {
    if (!prompt || !externalResponse) {
      alert('Prompt और External AI Response दोनों भरें');
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
          ai_name: aiName
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
      alert('Prompt भरें');
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
        body: JSON.stringify({ prompt })
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
              एक AI जो दूसरे AI से सीखता है और खुद को बेहतर बनाता है
            </CardDescription>
          </CardHeader>
        </Card>

        <Tabs defaultValue="learn" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="learn">Learn from AI</TabsTrigger>
            <TabsTrigger value="generate">Smart Generate</TabsTrigger>
            <TabsTrigger value="stats">Learning Stats</TabsTrigger>
          </TabsList>

          {/* Learn from External AI */}
          <TabsContent value="learn">
            <Card>
              <CardHeader>
                <CardTitle>दूसरे AI से सीखें</CardTitle>
                <CardDescription>
                  GitHub Copilot, ChatGPT या किसी भी AI का response paste करें
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="ainame">AI का नाम</Label>
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
                    placeholder="आपने क्या पूछा था?"
                    rows={3}
                  />
                </div>

                <div>
                  <Label htmlFor="external">External AI का Response</Label>
                  <Textarea
                    id="external"
                    value={externalResponse}
                    onChange={(e) => setExternalResponse(e.target.value)}
                    placeholder="दूसरे AI ने क्या जवाब दिया?"
                    rows={6}
                  />
                </div>

                <Button
                  onClick={handleLearnFromExternal}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? 'सीख रहा हूँ...' : '✨ Learn & Improve'}
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
                  Past learnings के साथ better response generate करें
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="smartprompt">Your Question/Task</Label>
                  <Textarea
                    id="smartprompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="क्या करना है?"
                    rows={4}
                  />
                </div>

                <Button
                  onClick={handleSmartGenerate}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? 'Generate कर रहा हूँ...' : '🚀 Smart Generate'}
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

          {/* Learning Stats */}
          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle>Learning Statistics</CardTitle>
                <CardDescription>
                  AI कितना सीख चुका है
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
