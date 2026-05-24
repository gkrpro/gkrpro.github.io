// logos.jsx — Greg's logo explorations
// Three pure-icon marks: Aperture (Swiss G), Stack (chevron layers), Perimeter (sigil/gate).

const PALETTE = {
  paper:      '#F4EFE5', // warm cream (mark surface)
  canvas:     '#f0eee9', // matches design canvas bg
  dark:       '#0E0D0B',
  ink:        '#141210',
  vermillion: '#D94528',
  electric:   '#2347E5',
  guide:      'rgba(20,18,16,0.22)',
  guideHard:  'rgba(20,18,16,0.5)',
  dim:        'rgba(20,18,16,0.55)',
  paperDim:   'rgba(244,239,229,0.55)',
};

// ─── 1. APERTURE ─────────────────────────────────────────────────────────────
// Geometric G built from a circle, rectangular mouth and an L-shaped spur.
// Swiss / brutalist. Reads as: vault dial, aperture, monogram.

function ApertureMark({ size = 240, color = PALETTE.ink }) {
  const id = React.useId();
  return (
    <svg width={size} height={size} viewBox="0 0 240 240" style={{display:'block'}} aria-label="Aperture mark">
      <defs>
        <mask id={`ap-${id}`}>
          <rect width="240" height="240" fill="white"/>
          <circle cx="120" cy="120" r="72" fill="black"/>
          <rect x="120" y="84" width="120" height="72" fill="black"/>
        </mask>
      </defs>
      <circle cx="120" cy="120" r="120" fill={color} mask={`url(#ap-${id})`}/>
      <rect x="120" y="104" width="60" height="32" fill={color}/>
      <rect x="148" y="120" width="32" height="28" fill={color}/>
    </svg>
  );
}

function ApertureConstruction({ size = 320 }) {
  const id = React.useId();
  return (
    <svg width={size} height={size} viewBox="-20 -20 280 280" style={{display:'block'}}>
      <defs>
        <mask id={`apc-${id}`}>
          <rect x="-20" y="-20" width="280" height="280" fill="white"/>
          <circle cx="120" cy="120" r="72" fill="black"/>
          <rect x="120" y="84" width="120" height="72" fill="black"/>
        </mask>
      </defs>
      {/* mark, slightly faded */}
      <g opacity="0.18">
        <circle cx="120" cy="120" r="120" fill={PALETTE.ink} mask={`url(#apc-${id})`}/>
        <rect x="120" y="104" width="60" height="32" fill={PALETTE.ink}/>
        <rect x="148" y="120" width="32" height="28" fill={PALETTE.ink}/>
      </g>
      {/* outlines + construction */}
      <g fill="none" stroke={PALETTE.guideHard} strokeWidth="1" vectorEffect="non-scaling-stroke">
        <circle cx="120" cy="120" r="120"/>
        <circle cx="120" cy="120" r="72"/>
        <line x1="120" y1="84" x2="240" y2="84"/>
        <line x1="120" y1="156" x2="240" y2="156"/>
        <line x1="120" y1="104" x2="180" y2="104"/>
        <line x1="120" y1="136" x2="180" y2="136"/>
        <line x1="180" y1="104" x2="180" y2="148"/>
        <line x1="148" y1="120" x2="148" y2="148"/>
        <line x1="148" y1="148" x2="180" y2="148"/>
      </g>
      <g fill="none" stroke={PALETTE.guide} strokeWidth="1" vectorEffect="non-scaling-stroke" strokeDasharray="3 4">
        <line x1="-20" y1="120" x2="260" y2="120"/>
        <line x1="120" y1="-20" x2="120" y2="260"/>
      </g>
      {/* tick marks at key radii */}
      <g fill={PALETTE.ink}>
        <circle cx="120" cy="120" r="2"/>
      </g>
      <g fontFamily="JetBrains Mono, monospace" fontSize="9" fill={PALETTE.dim} letterSpacing="0.04em">
        <text x="244" y="123">R 120</text>
        <text x="196" y="123">R 72</text>
        <text x="124" y="79">mouth · 72</text>
        <text x="124" y="100" fill={PALETTE.guideHard}>spur</text>
      </g>
    </svg>
  );
}

// ─── 2. STACK ────────────────────────────────────────────────────────────────
// Three chevrons stacked, ascending. Defense in depth.

function StackMark({ size = 240, color = PALETTE.vermillion }) {
  return (
    <svg width={size} height={size} viewBox="0 0 240 240" style={{display:'block'}} aria-label="Stack mark">
      <g fill="none" stroke={color} strokeWidth="28" strokeLinejoin="miter" strokeMiterlimit="12" strokeLinecap="butt">
        <polyline points="40,62 120,18 200,62"/>
        <polyline points="40,140 120,96 200,140"/>
        <polyline points="40,218 120,174 200,218"/>
      </g>
    </svg>
  );
}

function StackConstruction({ size = 320 }) {
  const stroke = 28;
  return (
    <svg width={size} height={size} viewBox="-20 -20 280 280" style={{display:'block'}}>
      <g opacity="0.18">
        <g fill="none" stroke={PALETTE.vermillion} strokeWidth={stroke} strokeLinejoin="miter" strokeMiterlimit="12">
          <polyline points="40,62 120,18 200,62"/>
          <polyline points="40,140 120,96 200,140"/>
          <polyline points="40,218 120,174 200,218"/>
        </g>
      </g>
      {/* outlines */}
      <g fill="none" stroke={PALETTE.guideHard} strokeWidth="1" vectorEffect="non-scaling-stroke">
        <polyline points="40,62 120,18 200,62"/>
        <polyline points="40,140 120,96 200,140"/>
        <polyline points="40,218 120,174 200,218"/>
      </g>
      {/* centerlines + baselines */}
      <g fill="none" stroke={PALETTE.guide} strokeWidth="1" vectorEffect="non-scaling-stroke" strokeDasharray="3 4">
        <line x1="120" y1="-20" x2="120" y2="260"/>
        <line x1="-20" y1="62" x2="260" y2="62"/>
        <line x1="-20" y1="140" x2="260" y2="140"/>
        <line x1="-20" y1="218" x2="260" y2="218"/>
        <line x1="-20" y1="18" x2="260" y2="18"/>
        <line x1="-20" y1="96" x2="260" y2="96"/>
        <line x1="-20" y1="174" x2="260" y2="174"/>
      </g>
      {/* angle indicator on top chevron */}
      <g fill="none" stroke={PALETTE.guideHard} strokeWidth="1" vectorEffect="non-scaling-stroke">
        <path d="M 110 50 A 14 14 0 0 1 124 36" />
      </g>
      <g fontFamily="JetBrains Mono, monospace" fontSize="9" fill={PALETTE.dim} letterSpacing="0.04em">
        <text x="216" y="22">apex</text>
        <text x="216" y="66">base</text>
        <text x="216" y="144">base</text>
        <text x="216" y="222">base</text>
        <text x="124" y="55">29°</text>
        <text x="46" y="13">rise 44 · run 80</text>
      </g>
    </svg>
  );
}

// ─── 3. PERIMETER ────────────────────────────────────────────────────────────
// Square frame with a precise gap on the right edge — the gate.
// Inside, a solid block aligned with the gap: the protected asset.

function PerimeterMark({ size = 240, frameColor = PALETTE.ink, blockColor = PALETTE.electric }) {
  return (
    <svg width={size} height={size} viewBox="0 0 240 240" style={{display:'block'}} aria-label="Perimeter mark">
      <path
        d="M 24,24 L 216,24 L 216,96 M 216,144 L 216,216 L 24,216 L 24,24"
        fill="none" stroke={frameColor} strokeWidth="20" strokeLinejoin="miter" strokeLinecap="square" strokeMiterlimit="6"
      />
      <rect x="108" y="100" width="80" height="40" fill={blockColor}/>
    </svg>
  );
}

function PerimeterConstruction({ size = 320 }) {
  return (
    <svg width={size} height={size} viewBox="-20 -20 280 280" style={{display:'block'}}>
      <g opacity="0.18">
        <path d="M 24,24 L 216,24 L 216,96 M 216,144 L 216,216 L 24,216 L 24,24"
          fill="none" stroke={PALETTE.ink} strokeWidth="20" strokeLinejoin="miter" strokeLinecap="square"/>
        <rect x="108" y="100" width="80" height="40" fill={PALETTE.electric}/>
      </g>
      {/* outlines */}
      <g fill="none" stroke={PALETTE.guideHard} strokeWidth="1" vectorEffect="non-scaling-stroke">
        <rect x="24" y="24" width="192" height="192"/>
        <rect x="108" y="100" width="80" height="40"/>
        <line x1="216" y1="96" x2="240" y2="96"/>
        <line x1="216" y1="144" x2="240" y2="144"/>
      </g>
      {/* centerlines */}
      <g fill="none" stroke={PALETTE.guide} strokeWidth="1" vectorEffect="non-scaling-stroke" strokeDasharray="3 4">
        <line x1="120" y1="-20" x2="120" y2="260"/>
        <line x1="-20" y1="120" x2="260" y2="120"/>
        <line x1="-20" y1="100" x2="260" y2="100"/>
        <line x1="-20" y1="140" x2="260" y2="140"/>
      </g>
      <g fontFamily="JetBrains Mono, monospace" fontSize="9" fill={PALETTE.dim} letterSpacing="0.04em">
        <text x="244" y="123">gap 48</text>
        <text x="124" y="116">80 × 40</text>
        <text x="28" y="20">192 × 192 · ⌐20</text>
      </g>
    </svg>
  );
}

// ─── EXPORTS ─────────────────────────────────────────────────────────────────
Object.assign(window, {
  PALETTE,
  ApertureMark, ApertureConstruction,
  StackMark, StackConstruction,
  PerimeterMark, PerimeterConstruction,
});
