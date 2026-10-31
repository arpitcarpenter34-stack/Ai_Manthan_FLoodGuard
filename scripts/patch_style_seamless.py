"""
Update frontend/static/css/style.css to support seamless transition of the
Application Module section over the pinned background animation.
"""

CSS_PATH = r"E:\ai-manthan\hydro_guard_indore\frontend\static\css\style.css"

with open(CSS_PATH, "r", encoding="utf-8") as f:
    content = f.read()

is_crlf = "\r\n" in content
normalized = content.replace("\r\n", "\n")

# 1. Update hero-scroll-track and hero-fg-layer
target1 = """/* Cinematic Hero Scroll Track Container (350vh for smooth 299-frame progression) */
.hero-scroll-track {
  position: relative;
  width: 100%;
  height: 350vh;
}

/* LAYER A: Sticky Full-Viewport Background Animation Layer */
.hero-bg-layer {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  z-index: 1;
}

/* Full-bleed HTML5 Canvas for frame-by-frame scroll rendering */
.hero-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
  display: block;
}

/* Feather-light mist gradient preserving 100% of the rainy city, dam, and river background */
.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.16) 38%, transparent 75%);
  z-index: 2;
  pointer-events: none;
}

/* LAYER B: Foreground Homepage Content Layer (Scrolls normally over pinned background) */
.hero-fg-layer {
  position: relative;
  z-index: 5;
  margin-top: -100vh;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 78px 28px 12px;
  pointer-events: none;
}

.hero-fg-layer > * {
  pointer-events: auto;
}"""

replacement1 = """/* Cinematic Hero Scroll Track Container (Covers Hero + Seamless Application Module Section) */
.hero-scroll-track {
  position: relative;
  width: 100%;
  min-height: 260vh;
}

/* LAYER A: Sticky Full-Viewport Background Animation Layer */
.hero-bg-layer {
  position: sticky;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  z-index: 1;
}

/* Full-bleed HTML5 Canvas for frame-by-frame scroll rendering */
.hero-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
  display: block;
}

/* Feather-light mist gradient preserving 100% of the rainy city, dam, and river background */
.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.16) 38%, transparent 75%);
  z-index: 2;
  pointer-events: none;
}

/* LAYER B: Foreground Homepage Content Layer (Scrolls seamlessly over pinned background) */
.hero-fg-layer {
  position: relative;
  z-index: 5;
  margin-top: -100vh;
  width: 100%;
  pointer-events: none;
}

.hero-fg-layer > * {
  pointer-events: auto;
}

/* Initial Hero Header View inside Foreground Layer */
.hero-header-content {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 78px 28px 12px;
}"""

# 2. Update homepage-features-section, section-head, and feature-launch-card
target2 = """.homepage-features-section {
  padding: 80px 24px 100px;
  max-width: 1320px;
  margin: 0 auto;
}

.section-head {
  text-align: center;
  margin-bottom: 50px;
}"""

replacement2 = """.homepage-features-section {
  padding: 30px 24px 90px;
  max-width: 1320px;
  margin: 0 auto;
  width: 100%;
  position: relative;
}

.section-head {
  text-align: center;
  margin-bottom: 36px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  padding: 26px 32px;
  max-width: 840px;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 12px 35px rgba(15, 23, 42, 0.08);
}"""

target3 = """.feature-launch-card {
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
}"""

replacement3 = """.feature-launch-card {
  background: rgba(255, 255, 255, 0.90);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 26px rgba(15, 23, 42, 0.06);
}"""

assert target1 in normalized, "target1 not found in style.css"
assert target2 in normalized, "target2 not found in style.css"
assert target3 in normalized, "target3 not found in style.css"

patched = normalized.replace(target1, replacement1).replace(target2, replacement2).replace(target3, replacement3)

if is_crlf:
    patched = patched.replace("\n", "\r\n")

with open(CSS_PATH, "w", encoding="utf-8") as f:
    f.write(patched)

print("SUCCESS: style.css updated with seamless frosted module section styles.")

