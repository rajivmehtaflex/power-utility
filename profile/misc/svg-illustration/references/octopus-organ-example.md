# Octopus on Pipe Organ SVG Example

This is the complete SVG code from a successful illustration session showing an octopus operating a pipe organ. Use as a reference for complex scene illustrations with multiple elements.

**Key patterns used:**
- Background with floor and spotlight for atmosphere
- Complex instrument structure (organ cabinet, pipes, keyboard, stops)
- Character with expressive face (eyes, smile, gradient shading)
- Multiple tentacles with different purposes (playing keys, pulling stops, idle)
- Sucker details on tentacles
- Highlights and shadows for depth
- CSS animations for gentle movement

**Coordinate system:** 800x600 viewBox, organ centered, octopus body at (400, 320)

**Techniques demonstrated:**
- CSS variables for color palette (easy theming)
- Linear and radial gradients for depth
- Transformed groups (note: child coordinates are relative to group origin)
- Multiple tentacle paths using quadratic Bézier curves
- Opacity for depth effects
- CSS keyframe animations on groups

**Pitfall encountered:**
- Highlight ellipse originally at `cx="380"` inside `<g transform="translate(400, 320)">` rendered wrong
- Fixed by using relative coordinate `cx="-20"` (see references/svg-coordinate-systems.md)

---

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <style>
    /* Color palette */
    :root {
      --bg-color: #1a1a2e;
      --organ-wood: #5d4037;
      --organ-wood-light: #8d6e63;
      --pipe-gold: #ffd700;
      --pipe-gold-dark: #b8860b;
      --octopus-purple: #6a1b9a;
      --octopus-purple-light: #ab47bc;
      --octopus-sucker: #4a148c;
      --key-white: #ffffff;
      --key-black: #1a1a1a;
      --glow: rgba(106, 27, 154, 0.3);
    }
    
    /* Common styles */
    .wood-fill { fill: var(--organ-wood); }
    .wood-light { fill: var(--organ-wood-light); }
    .pipe-gold { fill: url(#goldGradient); }
    .octopus-body { fill: var(--octopus-purple); stroke: var(--octopus-purple-light); stroke-width: 2; }
    .octopus-sucker { fill: var(--octopus-sucker); }
    .key-white { fill: var(--key-white); stroke: #ccc; stroke-width: 1; }
    .key-black { fill: var(--key-black); }
    
    /* Animations */
    @keyframes tentacleSwing {
      0%, 100% { transform: translateX(0); }
      50% { transform: translateX(2px); }
    }
    
    @keyframes glowPulse {
      0%, 100% { opacity: 0.2; }
      50% { opacity: 0.35; }
    }
    
    .tentacle-keyboard {
      animation: tentacleSwing 4s ease-in-out infinite;
      transform-origin: 400px 360px;
    }
    
    .tentacle-idle {
      animation: tentacleSwing 5s ease-in-out infinite;
      animation-delay: 1s;
      transform-origin: 400px 360px;
    }
    
    .tentacles-stops {
      animation: tentacleSwing 4.5s ease-in-out infinite;
      animation-delay: 0.5s;
      transform-origin: 400px 300px;
    }
  </style>
  
  <defs>
    <!-- Gold gradient for pipes -->
    <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:var(--pipe-gold-dark);stop-opacity:1" />
      <stop offset="30%" style="stop-color:var(--pipe-gold);stop-opacity:1" />
      <stop offset="70%" style="stop-color:var(--pipe-gold);stop-opacity:1" />
      <stop offset="100%" style="stop-color:var(--pipe-gold-dark);stop-opacity:1" />
    </linearGradient>
    
    <!-- Radial gradient for octopus body -->
    <radialGradient id="octopusGradient" cx="50%" cy="40%" r="60%">
      <stop offset="0%" style="stop-color:var(--octopus-purple-light);stop-opacity:1" />
      <stop offset="100%" style="stop-color:var(--octopus-purple);stop-opacity:1" />
    </radialGradient>
    
    <!-- Pipe shadow gradient -->
    <linearGradient id="pipeShadow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#000;stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:#000;stop-opacity:0" />
    </linearGradient>
  </defs>
  
  <!-- Background -->
  <rect x="0" y="0" width="800" height="600" fill="var(--bg-color)" />
  
  <!-- Floor -->
  <rect x="0" y="450" width="800" height="150" fill="var(--organ-wood-light)" opacity="0.3" />
  
  <!-- Subtle spotlight from above -->
  <ellipse cx="400" cy="300" rx="300" ry="200" fill="var(--glow)" opacity="0.2" class="spotlight" />
  
  <!-- Organ Cabinet -->
  <g id="organ-cabinet">
    <!-- Main cabinet body -->
    <rect x="150" y="200" width="500" height="350" rx="10" ry="10" class="wood-fill" />
    
    <!-- Cabinet trim (lighter wood) -->
    <rect x="160" y="210" width="480" height="330" rx="5" ry="5" class="wood-light" />
    
    <!-- Decorative molding at top -->
    <rect x="140" y="180" width="520" height="25" rx="5" ry="5" class="wood-fill" />
    
    <!-- Side panels -->
    <rect x="160" y="220" width="40" height="310" class="wood-fill" />
    <rect x="600" y="220" width="40" height="310" class="wood-fill" />
  </g>
  
  <!-- Pipe Array -->
  <g id="pipe-array">
    <!-- Back row pipes (smaller) -->
    <rect x="180" y="50" width="20" height="150" class="pipe-gold" opacity="0.7" />
    <rect x="210" y="60" width="20" height="140" class="pipe-gold" opacity="0.7" />
    <rect x="240" y="55" width="20" height="145" class="pipe-gold" opacity="0.7" />
    <rect x="270" y="70" width="20" height="130" class="pipe-gold" opacity="0.7" />
    <rect x="510" y="55" width="20" height="145" class="pipe-gold" opacity="0.7" />
    <rect x="540" y="60" width="20" height="140" class="pipe-gold" opacity="0.7" />
    <rect x="570" y="50" width="20" height="150" class="pipe-gold" opacity="0.7" />
    
    <!-- Middle row pipes -->
    <rect x="200" y="40" width="25" height="170" class="pipe-gold" />
    <rect x="235" y="35" width="25" height="175" class="pipe-gold" />
    <rect x="270" y="45" width="25" height="165" class="pipe-gold" />
    <rect x="300" y="30" width="25" height="180" class="pipe-gold" />
    <rect x="475" y="30" width="25" height="180" class="pipe-gold" />
    <rect x="505" y="45" width="25" height="165" class="pipe-gold" />
    <rect x="540" y="35" width="25" height="175" class="pipe-gold" />
    <rect x="575" y="40" width="25" height="170" class="pipe-gold" />
    
    <!-- Front row pipes (largest, tallest) -->
    <rect x="220" y="20" width="30" height="190" class="pipe-gold" />
    <rect x="260" y="10" width="30" height="200" class="pipe-gold" />
    <rect x="300" y="15" width="30" height="195" class="pipe-gold" />
    <rect x="340" y="5" width="30" height="205" class="pipe-gold" />
    <rect x="380" y="0" width="40" height="210" class="pipe-gold" />
    <rect x="430" y="5" width="30" height="205" class="pipe-gold" />
    <rect x="470" y="15" width="30" height="195" class="pipe-gold" />
    <rect x="510" y="10" width="30" height="200" class="pipe-gold" />
    
    <!-- Pipe caps -->
    <rect x="218" y="18" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="258" y="8" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="298" y="13" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="338" y="3" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="378" y="-2" width="44" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="428" y="3" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="468" y="13" width="34" height="8" rx="2" ry="2" class="wood-light" />
    <rect x="508" y="8" width="34" height="8" rx="2" ry="2" class="wood-light" />
  </g>
  
  <!-- Keyboard -->
  <g id="keyboard" transform="translate(200, 480)">
    <!-- Keyboard bed -->
    <rect x="-10" y="-5" width="420" height="15" fill="#333" />
    
    <!-- White keys (C to B, 14 keys) -->
    <rect x="0" y="0" width="30" height="60" class="key-white" />
    <rect x="30" y="0" width="30" height="60" class="key-white" />
    <rect x="60" y="0" width="30" height="60" class="key-white" />
    <rect x="90" y="0" width="30" height="60" class="key-white" />
    <rect x="120" y="0" width="30" height="60" class="key-white" />
    <rect x="150" y="0" width="30" height="60" class="key-white" />
    <rect x="180" y="0" width="30" height="60" class="key-white" />
    <rect x="210" y="0" width="30" height="60" class="key-white" />
    <rect x="240" y="0" width="30" height="60" class="key-white" />
    <rect x="270" y="0" width="30" height="60" class="key-white" />
    <rect x="300" y="0" width="30" height="60" class="key-white" />
    <rect x="330" y="0" width="30" height="60" class="key-white" />
    <rect x="360" y="0" width="30" height="60" class="key-white" />
    <rect x="390" y="0" width="30" height="60" class="key-white" />
    
    <!-- Black keys -->
    <rect x="22" y="0" width="16" height="38" class="key-black" />
    <rect x="52" y="0" width="16" height="38" class="key-black" />
    <rect x="112" y="0" width="16" height="38" class="key-black" />
    <rect x="142" y="0" width="16" height="38" class="key-black" />
    <rect x="172" y="0" width="16" height="38" class="key-black" />
    <rect x="232" y="0" width="16" height="38" class="key-black" />
    <rect x="262" y="0" width="16" height="38" class="key-black" />
    <rect x="322" y="0" width="16" height="38" class="key-black" />
    <rect x="352" y="0" width="16" height="38" class="key-black" />
  </g>
  
  <!-- Stop Knobs -->
  <g id="stop-knobs" transform="translate(250, 420)">
    <!-- Stop panel background -->
    <rect x="0" y="0" width="300" height="40" class="wood-light" rx="3" />
    
    <!-- Individual stops -->
    <circle cx="30" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="27" y="8" width="6" height="10" fill="#b8860b" rx="1" />
    
    <circle cx="80" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="77" y="8" width="6" height="10" fill="#b8860b" rx="1" />
    
    <circle cx="130" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="127" y="8" width="6" height="10" fill="#b8860b" rx="1" />
    
    <circle cx="180" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="177" y="8" width="6" height="10" fill="#b8860b" rx="1" />
    
    <circle cx="230" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="227" y="8" width="6" height="10" fill="#b8860b" rx="1" />
    
    <circle cx="280" cy="20" r="12" fill="#d4af37" stroke="#b8860b" stroke-width="2" />
    <rect x="277" y="8" width="6" height="10" fill="#b8860b" rx="1" />
  </g>
  
  <!-- Octopus Body -->
  <g id="octopus-body" transform="translate(400, 320)">
    <!-- Main body (rounded head shape) -->
    <ellipse cx="0" cy="-20" rx="60" ry="70" fill="url(#octopusGradient)" />
    
    <!-- Eyes -->
    <ellipse cx="-25" cy="-30" rx="15" ry="18" fill="#fff" />
    <ellipse cx="25" cy="-30" rx="15" ry="18" fill="#fff" />
    <circle cx="-22" cy="-30" r="8" fill="#1a1a1a" />
    <circle cx="28" cy="-30" r="8" fill="#1a1a1a" />
    <circle cx="-20" cy="-33" r="3" fill="#fff" opacity="0.7" />
    <circle cx="30" cy="-33" r="3" fill="#fff" opacity="0.7" />
    
    <!-- Smile -->
    <path d="M -15 -5 Q 0 10 15 -5" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" />
  </g>
  
  <!-- Tentacles on Keyboard -->
  <g id="tentacles-keyboard" class="tentacle-keyboard">
    <!-- Tentacle 1 - reaching left white key -->
    <path d="M 360 360 Q 320 400 280 440 Q 260 460 250 485" 
          stroke="var(--octopus-purple)" stroke-width="18" fill="none" stroke-linecap="round" />
    <path d="M 360 360 Q 320 400 280 440 Q 260 460 250 485" 
          stroke="var(--octopus-purple-light)" stroke-width="12" fill="none" stroke-linecap="round" opacity="0.5" />
    <!-- Suckers -->
    <circle cx="330" cy="410" r="5" class="octopus-sucker" />
    <circle cx="305" cy="440" r="5" class="octopus-sucker" />
    <circle cx="280" cy="465" r="5" class="octopus-sucker" />
    
    <!-- Tentacle 2 - reaching middle white key -->
    <path d="M 400 370 Q 400 410 400 460" 
          stroke="var(--octopus-purple)" stroke-width="18" fill="none" stroke-linecap="round" />
    <path d="M 400 370 Q 400 410 400 460" 
          stroke="var(--octopus-purple-light)" stroke-width="12" fill="none" stroke-linecap="round" opacity="0.5" />
    <!-- Suckers -->
    <circle cx="400" cy="400" r="5" class="octopus-sucker" />
    <circle cx="400" cy="430" r="5" class="octopus-sucker" />
    
    <!-- Tentacle 3 - reaching right white key -->
    <path d="M 440 360 Q 480 400 520 440 Q 540 460 550 485" 
          stroke="var(--octopus-purple)" stroke-width="18" fill="none" stroke-linecap="round" />
    <path d="M 440 360 Q 480 400 520 440 Q 540 460 550 485" 
          stroke="var(--octopus-purple-light)" stroke-width="12" fill="none" stroke-linecap="round" opacity="0.5" />
    <!-- Suckers -->
    <circle cx="470" cy="410" r="5" class="octopus-sucker" />
    <circle cx="495" cy="440" r="5" class="octopus-sucker" />
    <circle cx="520" cy="465" r="5" class="octopus-sucker" />
    
    <!-- Tentacle 4 - reaching black key (higher) -->
    <path d="M 380 350 Q 350 380 330 410" 
          stroke="var(--octopus-purple)" stroke-width="14" fill="none" stroke-linecap="round" />
    <!-- Suckers -->
    <circle cx="365" cy="375" r="4" class="octopus-sucker" />
    <circle cx="350" cy="395" r="4" class="octopus-sucker" />
  </g>
  
  <!-- Tentacles on Stop Knobs -->
  <g id="tentacles-stops" class="tentacles-stops">
    <!-- Tentacle reaching left stop -->
    <path d="M 370 300 Q 340 280 300 280 Q 280 280 280 305" 
          stroke="var(--octopus-purple)" stroke-width="14" fill="none" stroke-linecap="round" />
    <path d="M 370 300 Q 340 280 300 280 Q 280 280 280 305" 
          stroke="var(--octopus-purple-light)" stroke-width="10" fill="none" stroke-linecap="round" opacity="0.5" />
    <!-- Suckers -->
    <circle cx="345" cy="285" r="4" class="octopus-sucker" />
    <circle cx="320" cy="285" r="4" class="octopus-sucker" />
    
    <!-- Tentacle reaching right stop -->
    <path d="M 430 300 Q 460 280 500 280 Q 530 280 530 305" 
          stroke="var(--octopus-purple)" stroke-width="14" fill="none" stroke-linecap="round" />
    <path d="M 430 300 Q 460 280 500 280 Q 530 280 530 305" 
          stroke="var(--octopus-purple-light)" stroke-width="10" fill="none" stroke-linecap="round" opacity="0.5" />
    <!-- Suckers -->
    <circle cx="455" cy="285" r="4" class="octopus-sucker" />
    <circle cx="480" cy="285" r="4" class="octopus-sucker" />
  </g>
  
  <!-- Idle Tentacles (background) -->
  <g id="tentacles-idle" class="tentacle-idle" opacity="0.6">
    <!-- Left idle tentacle -->
    <path d="M 340 340 Q 250 360 200 420 Q 180 450 190 480" 
          stroke="var(--octopus-purple)" stroke-width="12" fill="none" stroke-linecap="round" />
    <!-- Suckers -->
    <circle cx="290" cy="365" r="4" class="octopus-sucker" opacity="0.8" />
    <circle cx="245" cy="390" r="4" class="octopus-sucker" opacity="0.8" />
    <circle cx="210" cy="430" r="4" class="octopus-sucker" opacity="0.8" />
    
    <!-- Right idle tentacle -->
    <path d="M 460 340 Q 550 360 600 420 Q 620 450 610 480" 
          stroke="var(--octopus-purple)" stroke-width="12" fill="none" stroke-linecap="round" />
    <!-- Suckers -->
    <circle cx="510" cy="365" r="4" class="octopus-sucker" opacity="0.8" />
    <circle cx="555" cy="390" r="4" class="octopus-sucker" opacity="0.8" />
    <circle cx="590" cy="430" r="4" class="octopus-sucker" opacity="0.8" />
    
    <!-- Bottom center idle tentacle -->
    <path d="M 400 380 Q 400 430 380 480" 
          stroke="var(--octopus-purple)" stroke-width="10" fill="none" stroke-linecap="round" />
    <!-- Suckers -->
    <circle cx="400" cy="420" r="3" class="octopus-sucker" opacity="0.8" />
    <circle cx="395" cy="450" r="3" class="octopus-sucker" opacity="0.8" />
  </g>
  
  <!-- Highlights and Shadows -->
  <g id="highlights-shadows">
    <!-- Octopus body highlight -->
    <ellipse cx="-20" cy="-50" rx="25" ry="20" fill="#fff" opacity="0.15" />
    
    <!-- Pipe shadows on cabinet -->
    <rect x="150" y="210" width="500" height="20" fill="url(#pipeShadow)" opacity="0.4" />
    
    <!-- Octopus shadow on floor -->
    <ellipse cx="400" cy="520" rx="100" ry="20" fill="#000" opacity="0.3" />
    
    <!-- Tentacle shadow highlights -->
    <ellipse cx="360" cy="370" rx="15" ry="8" fill="#fff" opacity="0.1" transform="rotate(-30 360 370)" />
    <ellipse cx="440" cy="370" rx="15" ry="8" fill="#fff" opacity="0.1" transform="rotate(30 440 370)" />
  </g>
  
</svg>
```

**Reusable techniques:**
1. Complex scene composition: Background → Structure → Character → Details
2. CSS variables: Define once, reference throughout with `var(--name)`
3. Gradients: Linear (metallic surfaces), radial (organic forms)
4. Transformed groups: Position elements, use relative coordinates inside
5. Bézier curves: `Q` for smooth curves (tentacles, organic shapes)
6. Animations: Apply to groups with `transform-origin` set appropriately
7. Depth: Opacity, highlights, shadows for 3D effect