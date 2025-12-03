import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileSpreadsheet, AlertCircle, CheckCircle, X, Menu, Download, Copy, Table, BarChart3, Loader } from 'lucide-react';

const REQUIRED_COLUMNS = [
  'GD_NO_Complete', 'NTN', 'IMPORTER NAME', 'HS CODE', 'ITEM DESCRIPTION',
  'Declared Unit PRICE', 'ORIGIN COUNTRY', 'ASSD QTY', 'ASSD UNIT',
  'ASSD UNIT PRICE', 'ASSD CURR', 'ASSESSED IMPORT VALUE RS',
  'Customs Duty PAID', 'Sales Tax PAID', 'Income Tax PAID',
  'Additional Custom Duty PAID', 'ADD SALES TAX PAID', 'REG.DUTY PAID',
  'GST PAID', 'Total', 'SRO'
];

const API_BASE_URL = 'http://localhost:8000';

// Helper function to render formatted message content
const renderMessageContent = (content) => {
  return content.split('\n').map((line, i) => {
    if (line.match(/^[📊📈💡⚠️🔍]\s\*\*.+\*\*$/)) {
      return (
        <div key={i} className="font-bold text-base mt-4 mb-2 text-blue-700 border-b border-blue-200 pb-1">
          {line.replace(/\*\*/g, '')}
        </div>
      );
    }
    
    if (line.includes('**')) {
      const parts = line.split('**');
      return (
        <div key={i} className="my-1">
          {parts.map((part, idx) => 
            idx % 2 === 1 ? <strong key={idx}>{part}</strong> : part
          )}
        </div>
      );
    }
    
    if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
      return (
        <div key={i} className="ml-4 my-1 flex items-start">
          <span className="text-blue-600 mr-2">•</span>
          <span>{line.replace(/^[•\-]\s*/, '')}</span>
        </div>
      );
    }
    
    if (line.match(/^\d+\.\s/)) {
      return (
        <div key={i} className="ml-4 my-1 flex items-start">
          <span className="text-blue-600 mr-2 font-semibold">{line.match(/^\d+\./)[0]}</span>
          <span>{line.replace(/^\d+\.\s*/, '')}</span>
        </div>
      );
    }
    
    if (line.trim() === '---') {
      return <hr key={i} className="my-3 border-gray-300" />;
    }
    
    return line.trim() ? <div key={i} className="my-1">{line}</div> : <br key={i} />;
  });
};

// Data Table Component
const DataTable = ({ data, columns, resultId }) => {
  const [showAll, setShowAll] = useState(false);
  const displayData = showAll ? data : data.slice(0, 10);

  const copyToClipboard = () => {
    const headers = columns.join('\t');
    const rows = data.map(row => columns.map(col => row[col] || '').join('\t')).join('\n');
    const text = headers + '\n' + rows;
    navigator.clipboard.writeText(text);
    alert('Data copied to clipboard!');
  };

  const downloadFile = (format) => {
    window.open(`${API_BASE_URL}/download/${resultId}?format=${format}`, '_blank');
  };

  return (
    <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center">
          <Table className="w-4 h-4 text-gray-600 mr-2" />
          <span className="text-sm font-medium text-gray-700">
            Data Results ({data.length} rows)
          </span>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={copyToClipboard}
            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center"
          >
            <Copy className="w-3 h-3 mr-1" />
            Copy
          </button>
          <button
            onClick={() => downloadFile('csv')}
            className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center"
          >
            <Download className="w-3 h-3 mr-1" />
            CSV
          </button>
          <button
            onClick={() => downloadFile('excel')}
            className="px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center"
          >
            <Download className="w-3 h-3 mr-1" />
            Excel
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayData.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-gray-50">
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {data.length > 10 && (
        <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-center">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showAll ? 'Show less' : `Show all ${data.length} rows`}
          </button>
        </div>
      )}
    </div>
  );
};

// Add this component before your CustomsAnalysisPlatform component

const VisualizationModal = ({ isOpen, onClose, resultId, queryText }) => {
  const [imageUrl, setImageUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasGenerated, setHasGenerated] = useState(false);

  const handleGenerateVisualization = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/generate-visualization/${resultId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to generate visualization');
      }

      const data = await response.json();
      setImageUrl(`${API_BASE_URL}/visualization/${resultId}?t=${Date.now()}`);
      setHasGenerated(true);
      setIsLoading(false);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (imageUrl) {
      try {
        // Fetch the image as a blob
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        
        // Create a download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `visualization_${resultId}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up the blob URL
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Download failed:', error);
        // Fallback to opening in new tab
        window.open(imageUrl, '_blank');
      }
    }
  };

  const handleClose = () => {
    setImageUrl(null);
    setHasGenerated(false);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-800">
                Data Visualization
              </h2>
              {queryText && (
                <p className="text-sm text-gray-500 mt-0.5">
                  {queryText.length > 60 ? `${queryText.substring(0, 60)}...` : queryText}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!hasGenerated && !isLoading && !error && (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-4">
              <BarChart3 className="w-16 h-16 text-gray-300" />
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-800 mb-2">
                  Generate Visualization
                </h3>
                <p className="text-sm text-gray-600 mb-4 max-w-md">
                  Click the button below to generate a visual representation of your data analysis.
                </p>
                <button
                  onClick={handleGenerateVisualization}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Generate Chart
                </button>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-4">
              <Loader className="w-12 h-12 text-blue-600 animate-spin" />
              <div className="text-center">
                <h3 className="text-lg font-medium text-gray-800 mb-2">
                  Generating Visualization...
                </h3>
                <p className="text-sm text-gray-600">
                  Our AI is creating the perfect chart for your data
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-4">
              <AlertCircle className="w-12 h-12 text-red-500" />
              <div className="text-center">
                <h3 className="text-lg font-medium text-red-800 mb-2">
                  Generation Failed
                </h3>
                <p className="text-sm text-red-600 mb-4">
                  {error}
                </p>
                <button
                  onClick={handleGenerateVisualization}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {imageUrl && !isLoading && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
                <img
                  src={imageUrl}
                  alt="Data Visualization"
                  className="w-full h-auto rounded"
                  onError={() => setError('Failed to load image')}
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {imageUrl && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Visualization generated successfully
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download PNG</span>
              </button>
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

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
  const [visualizationModal, setVisualizationModal] = useState({
    isOpen: false,
    resultId: null,
    queryText: ''
  });

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
        content: `✅ **File uploaded successfully!**\n\n📊 **Data Summary**\n• Total Records: ${summary.totalRows.toLocaleString()}\n• Unique Importers: ${summary.uniqueImporters.toLocaleString()}\n• Unique HS Codes: ${summary.uniqueHSCodes.toLocaleString()}\n• Origin Countries: ${summary.uniqueCountries.toLocaleString()}\n• Total Import Value: Rs ${summary.totalValue.toLocaleString(undefined, {maximumFractionDigits: 2})}\n• Total Customs Duty: Rs ${summary.totalDutyPaid.toLocaleString(undefined, {maximumFractionDigits: 2})}\n• Total Sales Tax: Rs ${summary.totalTaxPaid.toLocaleString(undefined, {maximumFractionDigits: 2})}\n\n🤖 **AI Ready!** Ask me about valuation discrepancies, tax anomalies, patterns, compliance issues, or specific importers.`,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages([welcomeMessage]);
      setIsProcessing(false);
      setApiConnected(true);
    } catch (error) {
      setValidationError(`Network error: ${error.message}. Make sure backend is running.`);
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
  
    const placeholderMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      isStreaming: true,
      metadata: null,
      resultId: null,
      columns: null,
      dataPreview: null,
      wantsData: false,
      hasVisualization: false
    };
    setMessages(prev => [...prev, placeholderMessage]);
    const messageIndex = messages.length + 1;
  
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
      let metadata = null;
  
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
  
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
  
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.type === 'metadata') {
                metadata = data;
                accumulatedContent = `🔍 **Query Executed**\n• SQL: \`${data.sql}\`\n• Rows Retrieved: ${data.rows}\n\n📊 **Analysis**\n\n`;
                
                // Update message with metadata immediately
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[messageIndex] = {
                    ...newMessages[messageIndex],
                    content: accumulatedContent,
                    metadata: metadata,
                    resultId: data.result_id,
                    columns: data.columns,
                    dataPreview: data.data_preview,
                    wantsData: data.wants_data,
                    hasVisualization: data.has_visualization
                  };
                  return newMessages;
                });
              } else if (data.type === 'token') {
                accumulatedContent += data.content;
                
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[messageIndex] = {
                    ...newMessages[messageIndex],
                    content: accumulatedContent
                  };
                  return newMessages;
                });
              } else if (data.type === 'visualization_ready') {
                // Mark visualization as ready
                setMessages(prev => {
                  const newMessages = [...prev];
                  newMessages[messageIndex] = {
                    ...newMessages[messageIndex],
                    hasVisualization: true,
                    visualizationReady: true
                  };
                  return newMessages;
                });
              } else if (data.type === 'done') {
                setIsProcessing(false);
              }
            } catch (e) {
              console.log('Parse error:', e);
            }
          }
        }
      }
  
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
        content: `❌ **Error:** ${error.message}\n\nMake sure:\n• Backend is running\n• OpenRouter API key is set`,
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
          
          <div className={`mb-4 p-3 rounded-lg ${apiConnected ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${apiConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className={`text-xs font-medium ${apiConnected ? 'text-green-800' : 'text-red-800'}`}>
                {apiConnected ? 'Backend Connected' : 'Backend Disconnected'}
              </span>
            </div>
            {!apiConnected && (
              <p className="text-xs text-red-600 mt-1">
                Run: uvicorn main:app --reload
              </p>
            )}
          </div>

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

          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
              Quick Analysis
            </p>
            {[
              'Show top 10 importers',
              'Find price discrepancies',
              'Give me audit prone cases',
              'Show unusual patterns',
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

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !uploadedFile && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <FileSpreadsheet className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-800 mb-2">
                  Welcome to AI-Powered Customs Analyzer
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Upload your customs Excel file to begin AI-assisted analysis.
                </p>
                {!apiConnected && (
                  <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-800">
                    ⚠️ Backend not connected. Run: <code className="bg-yellow-100 px-1 py-0.5 rounded">uvicorn main:app --reload</code>
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
                className={`max-w-4xl w-full px-4 py-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
                }`}
              >
                <div className="text-sm leading-relaxed">
                  {renderMessageContent(message.content)}
                  
                  {/* Show data table if available */}
                  {message.dataPreview && message.dataPreview.length > 0 && message.columns && (
                    <DataTable 
                      data={message.dataPreview} 
                      columns={message.columns}
                      resultId={message.resultId}
                    />
                  )}
                  
                  {/* Show download button if no preview but data exists */}
                  {message.wantsData && !message.dataPreview && message.resultId && (
                    <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800 mb-2">📥 Large dataset - Download available</p>
                      <div className="flex space-x-2">
                        <a
                          href={`${API_BASE_URL}/download/${message.resultId}?format=csv`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
                        >
                          <Download className="w-3 h-3 mr-1" />
                          CSV
                        </a>
                        <a
                          href={`${API_BASE_URL}/download/${message.resultId}?format=excel`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center"
                        >
                          <Download className="w-3 h-3 mr-1" />
                          Excel
                        </a>
                      </div>
                    </div>
                  )}

                  {/* Show visualization button - ALWAYS show if resultId exists */}
                  {Boolean(message?.resultId) &&
                    message.role === 'assistant' &&
                    typeof message?.content === "string" && (
                    <div className="mt-3">
                      <button
                        onClick={() => setVisualizationModal({
                          isOpen: true,
                          resultId: message.resultId,
                          queryText:
                            typeof messages[idx - 1]?.content === "string"
                                ? messages[idx - 1].content
                                : "Data Analysis"
                        })}
                        disabled={message.isStreaming}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <BarChart3 className="w-4 h-4" />
                        <span>
                          {message.visualizationReady ? 'View Chart' : 'Generate Chart'}
                        </span>
                      </button>
                    </div>
                  )}
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
                  <span className="text-sm text-gray-600 ml-2">AI analyzing...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={sessionId ? "Ask about customs data..." : "Upload file to start..."}
                  disabled={!sessionId}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
                  rows="2"
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
              Enter to send • Shift+Enter for new line • Powered by DeepSeek AI
            </p>
          </div>
        </div>
      </div>
      {/* Visualization Modal */}
      {visualizationModal.isOpen && visualizationModal.resultId && (
        <VisualizationModal
          isOpen={visualizationModal.isOpen}
          onClose={() => setVisualizationModal({ isOpen: false, resultId: null, queryText: '' })}
          resultId={visualizationModal.resultId}
          queryText={visualizationModal.queryText || "Data Analysis"}
        />
      )}
    </div>
  );
}