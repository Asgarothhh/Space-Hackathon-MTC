"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { Lock, ShieldCheck } from "lucide-react"

const CHARS = "ОРЛЩВЫТШАЬЛЫВАТЫВЬЛА3290ОАШЩЬЗ"

// Генерирует случайную строку символов
function generateLine(length) {
  return Array.from({ length }, () => CHARS[Math.floor(Math.random() * CHARS.length)]).join("")
}

function EncryptedText() {
  const canvasRef = useRef(null)
  const animationRef = useRef(0)
  const linesRef = useRef([])
  const opacitiesRef = useRef([])

  const ROWS = 8
  const COLS = 32

  useEffect(() => {
    // Инициализация данных
    linesRef.current = Array.from({ length: ROWS }, () => generateLine(COLS))
    opacitiesRef.current = Array.from({ length: ROWS }, () => 0.15 + Math.random() * 0.6)

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Настройка разрешения (DPI) для четкости текста
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)

    let tick = 0

    function draw() {
      if (!ctx || !canvas) return
      const w = rect.width
      const h = rect.height

      ctx.clearRect(0, 0, w, h)

      const fontSize = 14
      const lineHeight = h / ROWS
      ctx.font = `${fontSize}px "Space Grotesk", "SF Mono", monospace`
      ctx.textBaseline = "middle"

      for (let row = 0; row < ROWS; row++) {
        // Мутируем символы в строке
        const line = linesRef.current[row].split("")
        const mutations = Math.floor(Math.random() * 4) + 1
        for (let m = 0; m < mutations; m++) {
          const idx = Math.floor(Math.random() * COLS)
          line[idx] = CHARS[Math.floor(Math.random() * CHARS.length)]
        }
        linesRef.current[row] = line.join("")

        // Пульсация прозрачности строки
        const baseOpacity = opacitiesRef.current[row]
        const pulse = Math.sin(tick * 0.02 + row * 1.2) * 0.2
        const opacity = Math.max(0.08, Math.min(1, baseOpacity + pulse))

        const y = row * lineHeight + lineHeight / 2

        for (let col = 0; col < COLS; col++) {
          const char = linesRef.current[row][col]
          const x = (col / COLS) * w + 4

          // Цвет с красным оттенком и пульсирующей яркостью
          const charPulse = Math.sin(tick * 0.03 + col * 0.5 + row * 0.8) * 0.15
          const brightness = Math.max(0.3, Math.min(1, 0.5 + charPulse))

          const r = Math.floor(200 * brightness + 55)
          const g = Math.floor(60 * brightness)
          const b = Math.floor(70 * brightness)

          ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${opacity})`
          ctx.fillText(char, x, y)
        }
      }

      tick++
      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animationRef.current)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full"
      style={{ width: "100%", height: "100%" }}
      aria-hidden="true"
    />
  )
}

function PulsatingWord({ text, delay = 0 }) {
  const [displayText, setDisplayText] = useState(text)
  const [isScrambled, setIsScrambled] = useState(false)

  const scramble = useCallback(() => {
    setIsScrambled(true)
    let iteration = 0
    const maxIterations = text.length

    const interval = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((char, idx) => {
            if (char === " ") return " "
            if (idx < iteration) return text[idx]
            return CHARS[Math.floor(Math.random() * CHARS.length)]
          })
          .join("")
      )

      iteration += 1 / 2

      if (iteration >= maxIterations) {
        clearInterval(interval)
        setDisplayText(text)
        setIsScrambled(false)
      }
    }, 40)

    return () => clearInterval(interval)
  }, [text])

  useEffect(() => {
    const timeout = setTimeout(scramble, delay)
    const loop = setInterval(scramble, 4000 + delay)
    return () => {
      clearTimeout(timeout)
      clearInterval(loop)
    }
  }, [scramble, delay])

  return (
    <span
      className={`inline-block transition-colors duration-300 ${
        isScrambled ? "text-primary" : "text-foreground"
      }`}
    >
      {displayText}
    </span>
  )
}

export function EncryptionSection() {
  return (
    <section className="w-full py-16 md:py-24" aria-labelledby="encryption-heading">
      <div className="max-w-4xl mx-auto px-4 md:px-8">
        {/* Label */}
        <div className="flex items-center gap-2 mb-6">
          <div className="h-px flex-1 max-w-12 bg-primary/40" />
          <span className="text-xs font-mono uppercase tracking-widest text-primary">
            Encryption
          </span>
        </div>

        {/* Heading */}
        <h2
          id="encryption-heading"
          className="text-4xl md:text-6xl font-mono font-bold leading-tight mb-4 text-balance"
        >
          <PulsatingWord text="ПРИВЕТ" delay={0} />{" "}
          <PulsatingWord text="ЧУВАК" delay={600} />
        </h2> 

        <p className="text-muted-foreground text-lg leading-relaxed max-w-xl mb-10">
          The contents of your notes are end-to-end encrypted. No one else can
          read them (not even us).
        </p>

        {/* Card */}
        <div className="relative rounded-3xl border border-white/10 bg-white/5 backdrop-blur-2xl overflow-hidden shadow-2xl shadow-black/30">
          {/* Top bar */}
          <div className="flex items-center gap-3 px-5 py-3 border-b border-white/10">
            <Lock className="h-4 w-4 text-primary" />
            <span className="text-xs font-mono text-muted-foreground tracking-wide">
              end-to-end encrypted
            </span>
            <div className="ml-auto flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] text-primary/80 font-mono">LIVE</span>
            </div>
          </div>

          {/* Canvas area */}
          <div className="h-56 md:h-64 p-4">
            <EncryptedText />
          </div>

          {/* Bottom bar */}
          <div className="flex items-center gap-3 px-5 py-3 border-t border-white/10">
            <ShieldCheck className="h-4 w-4 text-primary/60" />
            <span className="text-[11px] text-muted-foreground font-mono">
              AES-256-GCM &middot; RSA-4096 &middot; Zero-knowledge
            </span>
          </div>
        </div>

        {/* Pills */}
        <div className="flex flex-wrap gap-3 mt-8">
          {["Local encryption", "Private keys", "No server access", "Open audit"].map(
            (label) => (
              <div
                key={label}
                className="px-4 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-xl text-sm text-muted-foreground"
              >
                {label}
              </div>
            )
          )}
        </div>
      </div>
    </section>
  )
}

export default EncryptionSection();