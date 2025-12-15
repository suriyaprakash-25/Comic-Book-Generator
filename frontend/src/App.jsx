import { useState } from 'react'
import { BookOpen, Sparkles, Loader2, Download, RefreshCw, Image, MessageSquare, Wand2 } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

// Art style presets
const STYLE_PRESETS = [
  { value: 'comic', label: 'American Comic', emoji: '🦸' },
  { value: 'manga', label: 'Japanese Manga', emoji: '🎌' },
  { value: 'cinematic', label: 'Cinematic / Realistic', emoji: '🎬' },
  { value: '3d', label: 'Pixar / 3D Style', emoji: '✨' },
]

// Pipeline stage names
const STAGES = [
  { key: 'stage_1_director', name: 'Director', description: 'Writing script...' },
  { key: 'stage_2_character_designer', name: 'Character Designer', description: 'Defining characters...' },
  { key: 'stage_3_cinematographer', name: 'Cinematographer', description: 'Generating panels...' },
  { key: 'stage_4_editor', name: 'Editor', description: 'Assembling comic...' },
]

// Comic Panel Component with Speech Bubble
function ComicPanel({ panel, index }) {
  const imageUrl = panel.image_url ? `${API_BASE_URL}${panel.image_url}` : null
  const dialogue = panel.dialogue || ''

  return (
    <div className="relative group overflow-hidden rounded-lg border-4 border-black bg-gray-200 aspect-square">
      {/* Panel Image */}
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={`Panel ${index + 1}`}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><rect fill="%23374151" width="400" height="400"/><text fill="%239CA3AF" x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="20">Image not available</text></svg>'
          }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-700">
          <Image className="w-12 h-12 text-gray-500" />
        </div>
      )}

      {/* Speech Bubble Overlay */}
      {dialogue && (
        <div className="absolute top-3 left-3 right-3 max-w-[80%]">
          <div className="relative bg-white rounded-2xl px-4 py-2 shadow-lg border-2 border-black">
            {/* Bubble tail */}
            <div className="absolute -bottom-3 left-6 w-0 h-0 border-l-[10px] border-l-transparent border-r-[10px] border-r-transparent border-t-[12px] border-t-white"></div>
            <div className="absolute -bottom-4 left-[22px] w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[14px] border-t-black -z-10"></div>
            {/* Text */}
            <p className="text-black text-sm font-comic leading-tight">{dialogue}</p>
          </div>
        </div>
      )}

      {/* Panel Number Badge */}
      <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
        Panel {index + 1}
      </div>
    </div>
  )
}

// Pipeline Status Component
function PipelineStatus({ stages, currentStage }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {STAGES.map((stage, i) => {
        const status = stages?.[stage.key] || 'pending'
        const isActive = currentStage === stage.key
        const isCompleted = status === 'completed'
        const isFailed = status === 'failed'

        return (
          <div
            key={stage.key}
            className={`rounded-xl p-4 border-2 transition-all ${
              isCompleted
                ? 'bg-green-500/20 border-green-500'
                : isFailed
                ? 'bg-red-500/20 border-red-500'
                : isActive
                ? 'bg-yellow-500/20 border-yellow-500 animate-pulse'
                : 'bg-white/5 border-white/10'
            }`}
          >
            <div className="text-xs text-white/60 mb-1">Stage {i + 1}</div>
            <div className="font-semibold text-sm">{stage.name}</div>
            <div className="text-xs mt-1">
              {isCompleted && <span className="text-green-400">✓ Complete</span>}
              {isFailed && <span className="text-red-400">✗ Failed</span>}
              {isActive && <span className="text-yellow-400">{stage.description}</span>}
              {!isCompleted && !isFailed && !isActive && <span className="text-white/40">Pending</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function App() {
  const [story, setStory] = useState('')
  const [numPanels, setNumPanels] = useState(4)
  const [selectedStyle, setSelectedStyle] = useState('comic')
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStage, setCurrentStage] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    if (!story.trim()) return

    setIsGenerating(true)
    setError(null)
    setResult(null)
    setCurrentStage('stage_1_director')

    try {
      // Simulate stage progression for UX
      const stageDelays = [
        'stage_1_director',
        'stage_2_character_designer', 
        'stage_3_cinematographer',
        'stage_4_editor'
      ]

      // Start a timer to show stage progression
      let stageIndex = 0
      const stageTimer = setInterval(() => {
        stageIndex++
        if (stageIndex < stageDelays.length) {
          setCurrentStage(stageDelays[stageIndex])
        }
      }, 15000) // Update every 15 seconds

      const response = await axios.post(`${API_BASE_URL}/api/generate-comic-full`, {
        story: story,
        num_panels: numPanels,
        style_preset: selectedStyle
      }, {
        timeout: 600000 // 10 minute timeout for full pipeline
      })

      clearInterval(stageTimer)
      setResult(response.data)
      setCurrentStage(null)

    } catch (err) {
      console.error('Error generating comic:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to generate comic')
    } finally {
      setIsGenerating(false)
      setCurrentStage(null)
    }
  }

  const handleDownload = () => {
    if (result?.comic_page?.image_url) {
      const link = document.createElement('a')
      link.href = `${API_BASE_URL}${result.comic_page.image_url}`
      link.download = `comic_${Date.now()}.png`
      link.click()
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    setStory('')
  }

  // Combine panels with script dialogues for display
  const panelsWithDialogue = result?.panels?.map((panel, idx) => ({
    ...panel,
    dialogue: result?.script?.panels?.[idx]?.dialogue || ''
  })) || []

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black text-white">
      {/* Header */}
      <header className="p-6 border-b border-white/10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-yellow-400" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              AI Comic Generator
            </h1>
          </div>
          <div className="text-sm text-white/60">
            Powered by Hugging Face 🤗
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6 space-y-6">

        {/* Input Section */}
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Wand2 className="w-5 h-5 text-yellow-400" />
            Create Your Story
          </h2>
          
          <textarea
            value={story}
            onChange={(e) => setStory(e.target.value)}
            placeholder="Write your story here... e.g., 'A brave knight named Arthur discovers a baby dragon in the enchanted forest. Instead of fighting it, he decides to protect it from evil hunters. Together, they become unlikely friends and defenders of the realm.'"
            className="w-full h-32 bg-black/30 border border-white/20 rounded-xl p-4 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 resize-none"
            disabled={isGenerating}
          />

          <div className="mt-4 flex flex-wrap items-center gap-4">
            {/* Panel Count Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-white/70">Panels:</label>
              <select
                value={numPanels}
                onChange={(e) => setNumPanels(parseInt(e.target.value))}
                className="bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-400/50"
                disabled={isGenerating}
              >
                {[2, 3, 4, 6].map(n => (
                  <option key={n} value={n}>{n} panels</option>
                ))}
              </select>
            </div>

            {/* Style Selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-white/70">Style:</label>
              <select
                value={selectedStyle}
                onChange={(e) => setSelectedStyle(e.target.value)}
                className="bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-400/50"
                disabled={isGenerating}
              >
                {STYLE_PRESETS.map(style => (
                  <option key={style.value} value={style.value}>
                    {style.emoji} {style.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Generate Button */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !story.trim()}
              className="px-6 py-3 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl font-semibold text-black hover:from-yellow-400 hover:to-orange-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Comic
                </>
              )}
            </button>

            {result && (
              <>
                <button
                  onClick={handleDownload}
                  className="px-4 py-3 bg-green-600 hover:bg-green-500 rounded-xl font-semibold flex items-center gap-2 transition-all"
                >
                  <Download className="w-5 h-5" />
                  Download
                </button>
                <button
                  onClick={handleReset}
                  className="px-4 py-3 bg-white/10 hover:bg-white/20 rounded-xl font-semibold flex items-center gap-2 transition-all"
                >
                  <RefreshCw className="w-5 h-5" />
                  New Comic
                </button>
              </>
            )}
          </div>
        </div>

        {/* Pipeline Status */}
        {(isGenerating || result) && (
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-yellow-400" />
              Pipeline Status
            </h3>
            <PipelineStatus 
              stages={result?.pipeline_stages} 
              currentStage={currentStage}
            />
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-red-400 mb-2">Error</h3>
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {/* Generated Comic Display */}
        {result && result.status === 'success' && (
          <>
            {/* Comic Title */}
            {result.script?.title && (
              <div className="text-center">
                <h2 className="text-3xl font-bold text-yellow-400">{result.script.title}</h2>
              </div>
            )}

            {/* Comic Panels Grid */}
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Image className="w-5 h-5 text-yellow-400" />
                Comic Panels
              </h3>
              
              <div className={`grid gap-4 ${
                panelsWithDialogue.length <= 2 ? 'grid-cols-1 md:grid-cols-2' :
                panelsWithDialogue.length <= 4 ? 'grid-cols-2' :
                'grid-cols-2 md:grid-cols-3'
              }`}>
                {panelsWithDialogue.map((panel, idx) => (
                  <ComicPanel key={panel.panel_id || idx} panel={panel} index={idx} />
                ))}
              </div>
            </div>

            {/* Assembled Comic Page */}
            {result.comic_page?.image_url && (
              <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-yellow-400" />
                  Final Comic Page
                </h3>
                <div className="flex justify-center">
                  <img
                    src={`${API_BASE_URL}${result.comic_page.image_url}`}
                    alt="Generated Comic Page"
                    className="max-w-full max-h-[800px] rounded-lg border-4 border-black shadow-2xl"
                  />
                </div>
              </div>
            )}

            {/* Script Details (Collapsible) */}
            <details className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
              <summary className="p-6 cursor-pointer hover:bg-white/5 rounded-2xl">
                <span className="text-lg font-semibold">📜 View Script Details</span>
              </summary>
              <div className="px-6 pb-6">
                <pre className="bg-black/30 rounded-xl p-4 overflow-auto text-sm text-white/80 max-h-96">
                  {JSON.stringify(result.script, null, 2)}
                </pre>
              </div>
            </details>
          </>
        )}

        {/* Instructions when no result */}
        {!result && !isGenerating && (
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10 text-center">
            <div className="text-6xl mb-4">🎨</div>
            <h3 className="text-xl font-semibold mb-2">Ready to Create!</h3>
            <p className="text-white/60 max-w-md mx-auto">
              Enter your story above and click "Generate Comic" to transform it into a visual comic book page with AI-generated panels and speech bubbles.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-4 text-sm text-white/50">
              <span>✨ LLM Script Writing</span>
              <span>🎨 AI Image Generation</span>
              <span>💬 Auto Speech Bubbles</span>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="p-6 border-t border-white/10 mt-12">
        <div className="max-w-6xl mx-auto text-center text-white/40 text-sm">
          Built with React, FastAPI & Hugging Face 🤗 | Meta-Llama-3 + FLUX.1
        </div>
      </footer>
    </div>
  )
}

export default App
