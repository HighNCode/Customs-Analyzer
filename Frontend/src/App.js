import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileSpreadsheet, AlertCircle, CheckCircle, X, Menu } from 'lucide-react';

const REQUIRED_COLUMNS = [
  'GD_NO_Complete', 'NTN', 'IMPORTER NAME', 'HS CODE', 'ITEM DESCRIPTION',
  'Declared Unit PRICE', 'ORIGIN COUNTRY', 'ASSD QTY', 'ASSD UNIT',
  'ASSD UNIT PRICE', 'ASSD CURR', 'ASSESSED IMPORT VALUE RS',
  'Customs Duty PAID', 'Sales Tax PAID', 'Income Tax PAID',
  'Additional Custom Duty PAID', 'ADD SALES TAX PAID', 'REG.DUTY PAID',
  'GST PAID', 'Total', 'SRO'
];

const API_BASE_URL = 'http://localhost:8000';

export default function CustomsAnalysisPlatform() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [validationError, setValidationError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        setApiConnected(true);
      }
    } catch (error) {
      setApiConnected(false);
      console.error('API connection failed:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    setValidationError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        setValidationError(error.detail || 'Failed to upload file');
        setIsProcessing(false);
        return;
      }

      const result = await response.json();
      const summary = result.summary;
      
      setUploadedFile(file);
      setSessionId(result.session_id);

      const welcomeMessage = {
        role: 'assistant',
        content: `✅ **File uploaded successfully and connected to AI!**\n\n**Data Summary:**\n- Total Records: ${summary.totalRows.toLocaleString()}\n- Unique Importers: ${summary.uniqueImporters.toLocaleString()}\n- Unique HS Codes: ${summary.uniqueHSCodes.toLocaleString()}\n- Origin Countries: ${summary.uniqueCountries.toLocaleString()}\n- Total Import Value: Rs ${summary.totalValue.toLocaleString(undefined, {maximumFractionDigits: 2})}\n- Total Customs Duty: Rs ${summary.totalDutyPaid.toLocaleString(undefined, {maximumFractionDigits: 2})}\n- Total Sales Tax: Rs ${summary.totalTaxPaid.toLocaleString(undefined, {maximumFractionDigits: 2})}\n\n🤖 **AI Analysis Ready!** I'm now connected to your DeepSeek LLM and ready to analyze this customs data.\n\nYou can ask me about:\n- Valuation discrepancies\n- Tax calculations and anomalies\n- Unusual patterns or suspicious entries\n- Specific importers or HS codes\n- Country-wise analysis\n- Compliance issues\n- And much more!`,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages([welcomeMessage]);
      setIsProcessing(false);
      setApiConnected(true);
    } catch (error) {
      setValidationError(`Network error: ${error.message}. Make sure the backend is running on ${API_BASE_URL}`);
      setIsProcessing(false);
      setApiConnected(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    if (!sessionId) {
      alert('Please upload an Excel file first.');
      return;
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    const userQuery = input;
    setInput('');
    setIsProcessing(true);

    // Add a placeholder message for streaming
    const placeholderMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      isStreaming: true
    };
    setMessages(prev => [...prev, placeholderMessage]);
    const messageIndex = messages.length + 1; // +1 because we just added user message

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userQuery,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from API');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let sqlQuery = '';
      let rowCount = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.slice(6); // Remove 'data: ' prefix

            if (content === '[DONE]') {
              setIsProcessing(false);
              continue;
            }

            if (content.startsWith('SQL: ')) {
              sqlQuery = content.slice(5);
              accumulatedContent += `\n**SQL Query:**\n\`\`\`sql\n${sqlQuery}\n\`\`\`\n\n`;
            } else if (content.startsWith('Rows: ')) {
              rowCount = content.slice(6);
              accumulatedContent += `**Rows Retrieved:** ${rowCount}\n\n**Analysis:**\n\n`;
            } else if (content.startsWith('Data: ')) {
              // Skip the raw data, just note we're starting analysis
              continue;
            } else if (content.trim()) {
              // This is the streaming LLM response
              accumulatedContent += content;
            }

            // Update the message in real-time
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[messageIndex] = {
                ...newMessages[messageIndex],
                content: accumulatedContent
              };
              return newMessages;
            });
          }
        }
      }

      // Mark streaming as complete
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[messageIndex] = {
          ...newMessages[messageIndex],
          isStreaming: false
        };
        return newMessages;
      });
      setIsProcessing(false);

    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ **Error:** ${error.message}\n\nPlease make sure:\n1. The backend server is running (python main.py)\n2. Ollama is running (ollama serve)\n3. DeepSeek model is available (ollama list)`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[messageIndex] = errorMessage;
        return newMessages;
      });
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearFile = () => {
    setUploadedFile(null);
    setSessionId(null);
    setMessages([]);
    setValidationError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden`}>
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">Customs Data Analyzer</h2>
          
          {/* API Connection Status */}
          <div className={`mb-4 p-3 rounded-lg ${apiConnected ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${apiConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className={`text-xs font-medium ${apiConnected ? 'text-green-800' : 'text-red-800'}`}>
                {apiConnected ? 'Backend Connected' : 'Backend Disconnected'}
              </span>
            </div>
            {!apiConnected && (
              <p className="text-xs text-red-600 mt-1">
                Run: python main.py
              </p>
            )}
          </div>

          {/* File Upload Section */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Excel File
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
              disabled={!apiConnected}
            />
            <label
              htmlFor="file-upload"
              className={`flex items-center justify-center w-full px-4 py-3 border-2 border-dashed rounded-lg transition-colors ${
                apiConnected 
                  ? 'border-gray-300 cursor-pointer hover:border-blue-500 hover:bg-blue-50' 
                  : 'border-gray-200 cursor-not-allowed bg-gray-50'
              }`}
            >
              <Upload className={`w-5 h-5 mr-2 ${apiConnected ? 'text-gray-400' : 'text-gray-300'}`} />
              <span className={`text-sm ${apiConnected ? 'text-gray-600' : 'text-gray-400'}`}>
                Choose Excel File
              </span>
            </label>
          </div>

          {/* Uploaded File Info */}
          {uploadedFile && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <FileSpreadsheet className="w-5 h-5 text-green-600 mt-0.5 mr-2" />
                  <div>
                    <p className="text-sm font-medium text-green-800">{uploadedFile.name}</p>
                    <p className="text-xs text-green-600 mt-1">AI Analysis Active</p>
                  </div>
                </div>
                <button
                  onClick={clearFile}
                  className="text-green-600 hover:text-green-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Validation Error */}
          {validationError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-2" />
                <div>
                  <p className="text-sm font-medium text-red-800">Error</p>
                  <p className="text-xs text-red-600 mt-1">{validationError}</p>
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Quick Analysis
            </p>
            {[
              'Show valuation discrepancies',
              'Analyze tax calculations',
              'Find suspicious patterns',
              'Top importers analysis',
              'Country-wise breakdown'
            ].map((action, idx) => (
              <button
                key={idx}
                onClick={() => {
                  if (sessionId) {
                    setInput(action);
                  } else {
                    alert('Please upload an Excel file first.');
                  }
                }}
                disabled={!sessionId}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {action}
              </button>
            ))}
          </div>

          {/* Column Info */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs font-medium text-blue-800 mb-2">Required Columns (21)</p>
            <div className="max-h-40 overflow-y-auto text-xs text-blue-700 space-y-1">
              {REQUIRED_COLUMNS.map((col, idx) => (
                <div key={idx} className="flex items-center">
                  <CheckCircle className="w-3 h-3 mr-1.5 flex-shrink-0" />
                  <span>{col}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="mr-4 p-2 hover:bg-gray-100 rounded-lg"
            >
              <Menu className="w-5 h-5 text-gray-600" />
            </button>
            <h1 className="text-xl font-semibold text-gray-800">Post Custom Audit Assistant</h1>
          </div>
          {sessionId && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">AI Connected</span>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !uploadedFile && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <FileSpreadsheet className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-800 mb-2">
                  Welcome to AI-Powered Customs Analyzer
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Upload your customs Excel file to begin AI-assisted analysis. The system will help you with post-custom audits, identify discrepancies, and provide intelligent insights.
                </p>
                {!apiConnected && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
                    ⚠️ Backend not connected. Make sure to run: <code className="bg-yellow-100 px-1 py-0.5 rounded">python main.py</code>
                  </div>
                )}
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm" style={{lineHeight: '1.6'}}>
                  {message.content.split('\n').map((line, i) => {
                    if (line.startsWith('**') && line.endsWith('**')) {
                      return <div key={i} className="font-semibold mt-2 mb-1">{line.slice(2, -2)}</div>;
                    }
                    if (line.startsWith('- ')) {
                      return <div key={i} className="ml-4">{line}</div>;
                    }
                    if (line.startsWith('# ')) {
                      return <div key={i} className="text-lg font-bold mt-3 mb-2">{line.slice(2)}</div>;
                    }
                    if (line.startsWith('## ')) {
                      return <div key={i} className="text-base font-bold mt-2 mb-1">{line.slice(3)}</div>;
                    }
                    return <div key={i}>{line || <br />}</div>;
                  })}
                </div>
                <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-200' : 'text-gray-500'}`}>
                  {message.timestamp}
                </div>
              </div>
            </div>
          ))}

          {isProcessing && (
            <div className="flex justify-start">
              <div className="max-w-3xl px-4 py-3 rounded-lg bg-white border border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                  <span className="text-sm text-gray-600 ml-2">AI is analyzing...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={sessionId ? "Ask me anything about the customs data..." : "Upload an Excel file to start..."}
                  disabled={!sessionId}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                  rows="3"
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() || !sessionId || isProcessing}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Press Enter to send • Shift+Enter for new line • Powered by DeepSeek AI
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}