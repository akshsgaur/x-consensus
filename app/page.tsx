"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import Image from "next/image"

interface LiveSearchResult {
  title: string;
  url: string;
  snippet: string;
  relevance_score?: number;
}

interface ConsensusData {
  sideA: {
    title: string;
    points: string[];
    username?: string;
  };
  sideB: {
    title: string;
    points: string[];
    username?: string;
  };
  consensus: string[];
  success: boolean;
  error?: string;
  
  // Enhanced fields
  peace_meme_url?: string;
  meme_prompt?: string;
  live_search_results?: LiveSearchResult[];
  enhanced_context?: string;
  confidence_score?: number;
  processing_time?: number;
}

export default function Home() {
  const [url, setUrl] = useState("")
  const [showResults, setShowResults] = useState(false)
  const [loading, setLoading] = useState(false)
  const [consensusData, setConsensusData] = useState<ConsensusData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progressMessage, setProgressMessage] = useState("")

  const analyzeThread = async (threadUrl: string) => {
    setLoading(true)
    setError(null)
    setProgressMessage("Starting analysis...")
    
    // Progress simulation for better UX
    const progressInterval = setInterval(() => {
      setProgressMessage(prev => {
        if (prev.includes("Extracting thread")) return "Analyzing with AI..."
        if (prev.includes("Analyzing with AI")) return "Finding common ground..."
        if (prev.includes("Finding common ground")) return "Almost done..."
        return "Extracting thread data..."
      })
    }, 15000) // Update every 15 seconds
    
    try {
      // Add timeout and better error handling
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 180000) // 3 minute timeout
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/analyze-thread`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: threadUrl }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      clearInterval(progressInterval)
      
      const data = await response.json()
      
      if (response.ok && data.success) {
        setConsensusData(data)
        setShowResults(true)
        setProgressMessage("")
      } else {
        setError(data.error || 'Failed to analyze thread')
        setProgressMessage("")
      }
    } catch (err) {
      clearInterval(progressInterval)
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. The analysis is taking longer than expected due to Twitter rate limiting. This is normal - please try again in a few minutes.')
      } else {
        setError('Failed to connect to analysis service')
      }
      setProgressMessage("")
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      analyzeThread(url.trim())
    }
  }

  const handleDemo = () => {
    const demoUrl = "https://x.com/elonmusk/status/1859734904336646594"
    setUrl(demoUrl)
    analyzeThread(demoUrl)
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#000000", color: "#ffffff" }}>
      {/* Header with X-Consensus Builder branding */}
      <div className="flex items-center justify-between p-6">
        <div className="flex items-center gap-3">
          <div
            className="px-4 py-2 flex items-center gap-2"
            style={{
              backgroundColor: "#ffffff",
              color: "#000000",
              border: "2px solid #000000",
              boxShadow: "4px 4px 0px #666666",
            }}
          >
            <span className="font-bold text-lg">X-Consensus Builder</span>
          </div>
        </div>
        <div
          className="px-3 py-1 text-sm font-medium flex items-center gap-2"
          style={{
            backgroundColor: "#ffffff",
            color: "#000000",
            border: "2px solid #000000",
            boxShadow: "3px 3px 0px #666666",
          }}
        >
          <Image
            src="/hack-logo.png"
            alt="Hackathon Logo"
            width={48}
            height={48}
            className="object-contain"
          />
          hackathon
        </div>
      </div>

      {/* Top Section - Logo and Title */}
      <div className="flex flex-col items-center justify-center pt-8 pb-8">
        {/* Logo Card - Larger tilted design */}
        <div
          className="relative mb-12"
          style={{
            transform: "rotate(-3deg)",
          }}
        >
          <div
            className="w-64 h-64 flex items-center justify-center"
            style={{
              backgroundColor: "#ffffff",
              border: "4px solid #000000",
              boxShadow: "12px 12px 0px #666666",
            }}
          >
            <Image
              src="/x-consensus-logo.png"
              alt="X-Consensus Builder Logo"
              width={200}
              height={200}
              className="object-contain"
              style={{
                transform: "rotate(-1deg)",
              }}
            />
          </div>
        </div>
      </div>

      {/* Bottom Section - Main Card */}
      <div className="flex justify-center px-4 pb-16">
        <div
          className="w-full max-w-2xl p-12"
          style={{
            backgroundColor: "#ffffff",
            border: "4px solid #000000",
            boxShadow: "12px 12px 0px #666666",
          }}
        >
          {/* Card Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-black mb-4">Where heated debates reveal hidden agreements</h2>
            <p className="text-lg text-gray-600 mb-2">Drop an X thread URL, watch the magic happen ✨</p>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              type="url"
              placeholder="https://x.com/elonmusk/status/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full p-4 text-lg bg-white text-black placeholder:text-gray-500 focus:outline-none focus:ring-0"
              style={{
                border: "3px solid #000000",
              }}
            />

            <div className="flex flex-col gap-4 items-center">
              {/* Primary Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-black text-white px-8 py-4 text-lg font-semibold hover:bg-black focus:ring-0 disabled:opacity-50 transition-all duration-300 ease-in-out hover:rotate-1 hover:scale-102"
                style={{
                  border: "3px solid #000000",
                  boxShadow: loading ? "3px 3px 0px #666666" : "6px 6px 0px #666666",
                }}
              >
                {loading ? "Analyzing..." : "Find Common Ground"}
              </Button>

              {/* Progress Message */}
              {loading && progressMessage && (
                <div className="mt-2 text-center text-sm text-gray-600">
                  {progressMessage}
                </div>
              )}
              
              {/* Enhanced Progress Info */}
              {loading && (
                <div className="mt-2 text-center text-xs text-gray-500">
                  ✨ Enhanced analysis with live search & meme generation
                </div>
              )}

            </div>
          </form>

          {/* Error Display */}
          {error && (
            <div className="mt-6 p-4 text-center" style={{
              backgroundColor: "#fee2e2",
              border: "2px solid #dc2626",
              color: "#dc2626"
            }}>
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>
      </div>

      {/* Results Section - Hidden by default */}
      {showResults && consensusData && (
        <div className="px-4 pb-16">
          {/* Opposing Viewpoints */}
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            <div
              className="p-6"
              style={{
                backgroundColor: "#ffffff",
                border: "4px solid #000000",
                boxShadow: "8px 8px 0px #666666",
              }}
            >
              <h3 className="text-xl font-bold mb-4" style={{ color: "#dc2626" }}>
                {consensusData.sideA.username ? `@${consensusData.sideA.username}'s perspective` : consensusData.sideA.title}
              </h3>
              <div className="space-y-3" style={{ color: "#333333" }}>
                {consensusData.sideA.points.map((point, index) => (
                  <p key={index}>"{point}"</p>
                ))}
              </div>
            </div>

            <div
              className="p-6"
              style={{
                backgroundColor: "#ffffff",
                border: "4px solid #000000",
                boxShadow: "8px 8px 0px #666666",
              }}
            >
              <h3 className="text-xl font-bold mb-4" style={{ color: "#2563eb" }}>
                {consensusData.sideB.username ? `@${consensusData.sideB.username}'s perspective` : consensusData.sideB.title}
              </h3>
              <div className="space-y-3" style={{ color: "#333333" }}>
                {consensusData.sideB.points.map((point, index) => (
                  <p key={index}>"{point}"</p>
                ))}
              </div>
            </div>
          </div>

          {/* Bridge Visualization */}
          <div className="text-center mb-8">
            <div
              className="inline-flex items-center gap-4 p-6"
              style={{
                backgroundColor: "#ffffff",
                border: "4px solid #000000",
                boxShadow: "8px 8px 0px #666666",
              }}
            >
              <span className="text-xl font-bold" style={{ color: "#333333" }}>
                Finding Common Ground
              </span>
            </div>
          </div>

          {/* Peace Meme Section */}
          {consensusData.peace_meme_url && (
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-6" style={{ color: "#000000" }}>
                🎕️ Peace Meme
              </h3>
              <div
                className="inline-block p-4"
                style={{
                  backgroundColor: "#ffffff",
                  border: "4px solid #000000",
                  boxShadow: "8px 8px 0px #666666",
                }}
              >
                <img
                  src={consensusData.peace_meme_url}
                  alt="AI-generated peace meme"
                  className="max-w-md mx-auto rounded"
                  style={{ border: "2px solid #000000" }}
                />
              </div>
            </div>
          )}

          {/* Consensus Points */}
          <div className="space-y-6">
            <div className="flex items-center justify-center gap-4 mb-8">
              <h3 className="text-3xl font-bold text-center" style={{ color: "#000000" }}>
                Hidden Agreements
              </h3>
              {consensusData.confidence_score && (
                <div
                  className="px-3 py-1 text-sm font-bold"
                  style={{
                    backgroundColor: "#16a34a",
                    color: "#ffffff",
                    border: "2px solid #000000",
                  }}
                >
                  {Math.round(consensusData.confidence_score * 100)}% confidence
                </div>
              )}
            </div>
            <div className="grid gap-4 max-w-3xl mx-auto">
              {consensusData.consensus.map((text, index) => (
                <div
                  key={index}
                  className="p-6 flex items-center gap-4"
                  style={{
                    backgroundColor: "#ffffff",
                    border: "4px solid #000000",
                    boxShadow: "8px 8px 0px #666666",
                  }}
                >
                  <span className="text-2xl font-bold" style={{ color: "#16a34a" }}>
                    ✓
                  </span>
                  <span className="text-lg" style={{ color: "#333333" }}>
                    {text}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Enhanced Data Section */}
          {((consensusData.live_search_results?.length ?? 0) > 0 || consensusData.processing_time) && (
            <div className="mt-12 space-y-6">
              <h3 className="text-xl font-bold text-center" style={{ color: "#000000" }}>
                ✨ Enhanced Analysis Data
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                {/* Live Search Results */}
                {(consensusData.live_search_results?.length ?? 0) > 0 && (
                  <div
                    className="p-6"
                    style={{
                      backgroundColor: "#ffffff",
                      border: "4px solid #000000",
                      boxShadow: "8px 8px 0px #666666",
                    }}
                  >
                    <h4 className="font-bold mb-4" style={{ color: "#2563eb" }}>
                      🔍 Live Search Results
                    </h4>
                    <div className="space-y-3">
                      {consensusData.live_search_results.map((result, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4">
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold text-blue-600 hover:underline text-sm"
                          >
                            {result.title}
                          </a>
                          <p className="text-xs text-gray-600 mt-1">{result.snippet}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Processing Stats */}
                <div
                  className="p-6"
                  style={{
                    backgroundColor: "#ffffff",
                    border: "4px solid #000000",
                    boxShadow: "8px 8px 0px #666666",
                  }}
                >
                  <h4 className="font-bold mb-4" style={{ color: "#dc2626" }}>
                    📊 Analysis Stats
                  </h4>
                  <div className="space-y-2 text-sm">
                    {consensusData.processing_time && (
                      <div className="flex justify-between">
                        <span>Processing Time:</span>
                        <span className="font-semibold">{consensusData.processing_time}s</span>
                      </div>
                    )}
                    {consensusData.confidence_score && (
                      <div className="flex justify-between">
                        <span>AI Confidence:</span>
                        <span className="font-semibold">{Math.round(consensusData.confidence_score * 100)}%</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Enhanced Pipeline:</span>
                      <span className="font-semibold text-green-600">✓ Active</span>
                    </div>
                    {consensusData.peace_meme_url && (
                      <div className="flex justify-between">
                        <span>Peace Meme:</span>
                        <span className="font-semibold text-green-600">✓ Generated</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}