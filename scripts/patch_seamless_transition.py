"""
Patch frontend/static/index.html to seamlessly integrate the Application Module
section inside the animated hero scroll track with two independent visual layers.
"""

import sys

INDEX_PATH = r"E:\ai-manthan\hydro_guard_indore\frontend\static\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Normalize newlines for matching
is_crlf = "\r\n" in content
normalized = content.replace("\r\n", "\n")

target1 = """    <!-- Cinematic Hero Section -->
    <header id="hero" class="hero-section">
      <div class="hero-overlay"></div>

      <div class="hero-container">"""

replacement1 = """    <!-- Cinematic Hero Section with Scroll-Controlled Canvas Animation -->
    <div id="hero-scroll-track" class="hero-scroll-track">
      <!-- LAYER A: Sticky Full-Viewport Background Animation Layer -->
      <div id="hero-bg-layer" class="hero-bg-layer">
        <canvas id="hero-canvas" class="hero-canvas"></canvas>
        <div class="hero-overlay"></div>
      </div>

      <!-- LAYER B: Foreground Homepage Content (Scrolls seamlessly over pinned background) -->
      <div class="hero-fg-layer">
        <!-- Hero Initial Header View -->
        <header id="hero" class="hero-header-content">
          <div class="hero-container">"""

target2 = """            <span>View Audit Logs</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- Topography and Municipal Info Section -->"""

replacement2 = """            <span>View Audit Logs</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </div>
        </div>
      </div>
    </section>
      </div><!-- /.hero-fg-layer -->
    </div><!-- /#hero-scroll-track -->

    <!-- Topography and Municipal Info Section -->"""

target3 = """  <!-- Main Client Application JS -->
  <script src="/static/js/app.js?v=3.2"></script>
</body>"""

replacement3 = """  <!-- Main Client Application JS -->
  <script src="/static/js/app.js?v=3.2"></script>

  <!-- Cinematic ZIP-Based Scroll Animation JS -->
  <script src="/static/js/hero_scroll_animation.js?v=1.1"></script>
</body>"""

if target1 not in normalized:
    print("ERROR: target1 not found in index.html")
    sys.exit(1)
if target2 not in normalized:
    print("ERROR: target2 not found in index.html")
    sys.exit(1)
if target3 not in normalized:
    print("ERROR: target3 not found in index.html")
    sys.exit(1)

patched = normalized.replace(target1, replacement1).replace(target2, replacement2).replace(target3, replacement3)

if is_crlf:
    patched = patched.replace("\n", "\r\n")

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(patched)

print("SUCCESS: index.html patched with seamless module section transition structure.")

