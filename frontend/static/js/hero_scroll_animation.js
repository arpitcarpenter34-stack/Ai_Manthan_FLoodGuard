/**
 * HYDRO-GUARD AI — Cinematic ZIP-Based Scroll Animation
 * 
 * Maps user scroll progress strictly through the 299 chronological frames extracted
 * from the original video frame sequence (ezgif-frame-001.png to ezgif-frame-299.png).
 * 
 * Pipeline:
 *   User Scroll -> Scroll Progress (0.0 to 1.0) -> Frame Index (1 to 299) -> Canvas Render
 * 
 * Visual Architecture:
 *   - Layer A (Sticky Background): Canvas is pinned at top: 0 covering the full viewport
 *     without any black sidebars (active content cropped to 1144x720 16:10 aspect ratio).
 *   - Layer B (Foreground Content): Hero title, description, dual buttons, and 4 feature
 *     cards follow normal document scrolling and move upward naturally out of view.
 *   - When scrolling stops: Frame stops changing.
 *   - Upward scroll: Seamlessly reverses the sequence and brings foreground cards back.
 */

(function () {
  "use strict";

  const TOTAL_FRAMES = 299;
  const FRAME_DIR = "/static/hero_frames";
  const FRAME_PREFIX = "ezgif-frame-";
  const FRAME_EXT = ".png";

  // The 1280x720 video frames extracted from ezgif contain 66px black pillarbox sidebars.
  // Active content is from x=68 to x=1212 (width=1144px, height=720px, 16:10 aspect ratio).
  const ACTIVE_CROP_X = 68;
  const ACTIVE_CROP_Y = 0;
  const ACTIVE_CROP_W = 1144;
  const ACTIVE_CROP_H = 720;

  const frameCache = new Map(); // index (1..299) -> HTMLImageElement
  let canvas = null;
  let ctx = null;
  let scrollTrack = null;
  let scrollIndicator = null;

  let currentTargetFrame = 1;
  let lastDrawnFrame = 1;
  let ticking = false;
  let isInitialized = false;

  function getFrameUrl(idx) {
    const padded = String(idx).padStart(3, "0");
    return `${FRAME_DIR}/${FRAME_PREFIX}${padded}${FRAME_EXT}`;
  }

  function preloadFrame(idx, onLoaded) {
    if (idx < 1 || idx > TOTAL_FRAMES) return null;
    if (frameCache.has(idx)) {
      const existing = frameCache.get(idx);
      if (onLoaded && existing.complete && existing.naturalWidth > 0) {
        onLoaded(existing);
      }
      return existing;
    }

    const img = new Image();
    img.src = getFrameUrl(idx);
    img.onload = () => {
      if (onLoaded) onLoaded(img);
    };
    frameCache.set(idx, img);
    return img;
  }

  function getClosestLoadedFrame(targetIdx) {
    // 1. Direct hit
    if (frameCache.has(targetIdx)) {
      const img = frameCache.get(targetIdx);
      if (img.complete && img.naturalWidth > 0) {
        return img;
      }
    }

    // 2. Search outward bidirectionally for nearest available frame
    for (let offset = 1; offset <= TOTAL_FRAMES; offset++) {
      const prev = targetIdx - offset;
      if (prev >= 1 && frameCache.has(prev)) {
        const img = frameCache.get(prev);
        if (img.complete && img.naturalWidth > 0) {
          return img;
        }
      }
      const next = targetIdx + offset;
      if (next <= TOTAL_FRAMES && frameCache.has(next)) {
        const img = frameCache.get(next);
        if (img.complete && img.naturalWidth > 0) {
          return img;
        }
      }
    }

    return null;
  }

  function drawImageCover(img) {
    if (!ctx || !canvas || !img || !img.complete || img.naturalWidth === 0) return;

    const cw = canvas.width;
    const ch = canvas.height;
    const iw = img.naturalWidth;
    const ih = img.naturalHeight;

    let sx = 0;
    let sy = 0;
    let sw = iw;
    let sh = ih;

    // Crop pillarbox black sidebars if 1280x720 video frame
    if (iw === 1280 && ih === 720) {
      sx = ACTIVE_CROP_X;
      sy = ACTIVE_CROP_Y;
      sw = ACTIVE_CROP_W;
      sh = ACTIVE_CROP_H;
    }

    // Cover-style aspect-ratio scaling to completely cover cw x ch with vibrant image content
    const scale = Math.max(cw / sw, ch / sh);
    const dw = sw * scale;
    const dh = sh * scale;
    const dx = (cw - dw) * 0.5;
    const dy = (ch - dh) * 0.5;

    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
  }

  function renderFrame(targetIdx) {
    const img = getClosestLoadedFrame(targetIdx);
    if (img) {
      drawImageCover(img);
      lastDrawnFrame = targetIdx;
    }
  }

  function resizeCanvas() {
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Use window.innerWidth and window.innerHeight to match full viewport dimensions
    const w = window.innerWidth;
    const h = window.innerHeight;
    const targetW = Math.round(w * dpr);
    const targetH = Math.round(h * dpr);

    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }

    renderFrame(currentTargetFrame);
  }

  function calculateScrollProgress() {
    if (!scrollTrack) return 0;
    const rect = scrollTrack.getBoundingClientRect();
    const trackHeight = scrollTrack.offsetHeight;
    const viewportHeight = window.innerHeight;
    const scrollableDistance = trackHeight - viewportHeight;

    if (scrollableDistance <= 0) return 0;

    // When top of track is at top of viewport, rect.top is 0 -> progress 0
    // When bottom of track reaches bottom of viewport, progress 1
    const progress = -rect.top / scrollableDistance;
    return Math.max(0, Math.min(1, progress));
  }

  function preloadSurroundingFrames(centerIdx) {
    const radius = 20;
    const start = Math.max(1, centerIdx - radius);
    const end = Math.min(TOTAL_FRAMES, centerIdx + radius);

    for (let i = start; i <= end; i++) {
      if (!frameCache.has(i)) {
        preloadFrame(i);
      }
    }
  }

  function startIdleKeyframePreload() {
    // Step 1: Preload sparse keyframes across the whole duration (every 5th frame)
    let kf = 1;
    function loadNextBatch() {
      const batchEnd = Math.min(TOTAL_FRAMES, kf + 30);
      for (; kf <= batchEnd; kf += 5) {
        preloadFrame(kf);
      }
      if (kf < TOTAL_FRAMES) {
        if ("requestIdleCallback" in window) {
          window.requestIdleCallback(loadNextBatch, { timeout: 1000 });
        } else {
          setTimeout(loadNextBatch, 100);
        }
      }
    }
    loadNextBatch();
  }

  function onScrollUpdate() {
    // Only update if homepage view is active
    const homeView = document.getElementById("view-home");
    if (homeView && homeView.style.display === "none") return;

    const progress = calculateScrollProgress();
    // Prompt formula: frameIndex = Math.floor(progress * (totalFrames - 1))
    // 1-based indexing for filenames (1..299):
    const frameIndex = 1 + Math.floor(progress * (TOTAL_FRAMES - 1));
    const clampedFrame = Math.max(1, Math.min(TOTAL_FRAMES, frameIndex));

    // Fade out explore indicator as user scrolls down
    if (scrollIndicator) {
      scrollIndicator.style.opacity = progress > 0.05 ? "0" : "1";
      scrollIndicator.style.pointerEvents = progress > 0.05 ? "none" : "auto";
    }

    if (clampedFrame !== currentTargetFrame) {
      currentTargetFrame = clampedFrame;
      preloadSurroundingFrames(currentTargetFrame);

      // If requested frame is loaded, draw immediately; else trigger load & draw closest
      if (frameCache.has(currentTargetFrame) && frameCache.get(currentTargetFrame).complete) {
        renderFrame(currentTargetFrame);
      } else {
        preloadFrame(currentTargetFrame, () => {
          if (currentTargetFrame === clampedFrame) {
            renderFrame(currentTargetFrame);
          }
        });
        renderFrame(currentTargetFrame); // fallback to nearest while loading
      }
    }
  }

  function onScroll() {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        onScrollUpdate();
        ticking = false;
      });
      ticking = true;
    }
  }

  function init() {
    if (isInitialized) return;

    canvas = document.getElementById("hero-canvas");
    scrollTrack = document.getElementById("hero-scroll-track");
    scrollIndicator = document.querySelector(".scroll-explore-indicator");

    if (!canvas || !scrollTrack) {
      console.warn("[HeroScroll] Hero canvas or scroll track not found in DOM.");
      return;
    }

    ctx = canvas.getContext("2d", { alpha: false });

    // Step 1: Preload Frame 1 and Frame 299 immediately
    preloadFrame(1, (img1) => {
      resizeCanvas();
      drawImageCover(img1);
    });
    preloadFrame(TOTAL_FRAMES);

    // Step 2: Preload initial buffer (1..30)
    for (let i = 2; i <= 30; i++) {
      preloadFrame(i);
    }

    // Step 3: Event Listeners
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", () => {
      resizeCanvas();
      onScrollUpdate();
    }, { passive: true });

    // Step 4: Background keyframe preloading
    startIdleKeyframePreload();

    // Initial sizing & scroll check
    resizeCanvas();
    onScrollUpdate();

    isInitialized = true;
    console.log("[HeroScroll] Cinematic scroll animation initialized (299 frames).");
  }

  // Auto-init on DOMContentLoaded or immediately if DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose global controller for testing and programmatic resets
  window.HeroScrollAnimation = {
    init: init,
    isReady: () => isInitialized,
    getCurrentFrame: () => currentTargetFrame,
    getLastDrawnFrame: () => lastDrawnFrame,
    getProgress: calculateScrollProgress,
    getTotalFrames: () => TOTAL_FRAMES,
    setFrame: (idx) => {
      currentTargetFrame = Math.max(1, Math.min(TOTAL_FRAMES, idx));
      renderFrame(currentTargetFrame);
    }
  };
})();
