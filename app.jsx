// app.jsx — Greg's logo exploration canvas

const { useState } = React;

// ─── shared atoms ────────────────────────────────────────────────────────────

function Surface({ bg = PALETTE.paper, children, style = {} }) {
  return (
    <div style={{
      width: '100%', height: '100%', background: bg,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden', ...style,
    }}>
      {children}
    </div>
  );
}

function CornerLabel({ children, color = PALETTE.dim, side = 'bl' }) {
  const pos = {
    bl: { left: 16, bottom: 14 },
    br: { right: 16, bottom: 14 },
    tl: { left: 16, top: 14 },
    tr: { right: 16, top: 14 },
  }[side];
  return (
    <div style={{
      position: 'absolute', ...pos,
      fontFamily: 'JetBrains Mono, ui-monospace, monospace',
      fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase',
      color, fontWeight: 500,
    }}>{children}</div>
  );
}

// ─── ARTBOARD CONTENTS ───────────────────────────────────────────────────────

function HeroBoard({ Mark, color, label, name }) {
  return (
    <Surface bg={PALETTE.paper}>
      <Mark size={300} color={color}/>
      <CornerLabel side="tl">{label}</CornerLabel>
      <CornerLabel side="br">{name}</CornerLabel>
    </Surface>
  );
}

function DarkBoard({ Mark, color, label }) {
  return (
    <Surface bg={PALETTE.dark}>
      <Mark size={300} color={color}/>
      <CornerLabel side="tl" color={PALETTE.paperDim}>{label}</CornerLabel>
    </Surface>
  );
}

function ConstructionBoard({ ConstructionView, label }) {
  return (
    <Surface bg={PALETTE.paper}>
      <ConstructionView size={420}/>
      <CornerLabel side="tl">{label}</CornerLabel>
    </Surface>
  );
}

// Scale row: shows the mark at multiple sizes
function ScaleBoard({ Mark, color, label }) {
  const sizes = [120, 80, 56, 40, 24, 16];
  return (
    <Surface bg={PALETTE.paper} style={{ flexDirection: 'column', gap: 12 }}>
      <div style={{
        display: 'flex', alignItems: 'flex-end', gap: 40, padding: '0 32px',
      }}>
        {sizes.map(s => (
          <div key={s} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
            <Mark size={s} color={color}/>
            <div style={{
              fontFamily: 'JetBrains Mono, monospace', fontSize: 9, letterSpacing: '0.1em',
              color: PALETTE.dim, fontWeight: 500,
            }}>{s}px</div>
          </div>
        ))}
      </div>
      <CornerLabel side="tl">{label}</CornerLabel>
      <CornerLabel side="br">favicon ←→ marquee</CornerLabel>
    </Surface>
  );
}

// Application: faux browser + site header
function ApplicationBoard({ Mark, markColor, label, accentBg }) {
  return (
    <Surface bg={PALETTE.paper} style={{ flexDirection: 'column', padding: 0, justifyContent: 'flex-start' }}>
      {/* Browser tab */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '14px 18px 0',
        width: '100%', boxSizing: 'border-box',
      }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: '#E0593E' }}/>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: '#E5B33A' }}/>
          <span style={{ width: 10, height: 10, borderRadius: 999, background: '#5BBF5A' }}/>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          marginLeft: 16, padding: '6px 12px 6px 8px',
          background: 'rgba(20,18,16,0.06)', borderRadius: 8,
          minWidth: 220,
        }}>
          <div style={{ width: 16, height: 16, display: 'grid', placeItems: 'center' }}>
            <Mark size={16} color={markColor}/>
          </div>
          <span style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 11, color: PALETTE.ink, fontWeight: 500 }}>
            Greg · Cloud Security
          </span>
          <span style={{ marginLeft: 'auto', fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: PALETTE.dim }}>×</span>
        </div>
        <div style={{ flex: 1 }}/>
      </div>

      {/* URL bar */}
      <div style={{
        margin: '10px 18px 0', padding: '7px 12px',
        background: 'rgba(20,18,16,0.04)', borderRadius: 8,
        fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: PALETTE.dim,
        letterSpacing: '0.02em',
      }}>
        <span style={{ color: 'rgba(20,18,16,0.4)' }}>https://</span>greg.computer
      </div>

      {/* Site mock */}
      <div style={{
        flex: 1, width: '100%', boxSizing: 'border-box',
        background: accentBg || PALETTE.paper,
        marginTop: 16,
        padding: '32px 36px',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        borderTop: '1px solid rgba(20,18,16,0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <Mark size={32} color={markColor}/>
            <span style={{
              fontFamily: 'Space Grotesk, sans-serif', fontWeight: 600, fontSize: 15,
              color: PALETTE.ink, letterSpacing: '-0.01em',
            }}>Greg</span>
          </div>
          <div style={{
            display: 'flex', gap: 22,
            fontFamily: 'Space Grotesk, sans-serif', fontSize: 12, color: PALETTE.dim, fontWeight: 500,
          }}>
            <span>Writing</span><span>Work</span><span>Contact</span>
          </div>
        </div>
        <div>
          <div style={{
            fontFamily: 'Space Grotesk, sans-serif', fontWeight: 600, fontSize: 28,
            color: PALETTE.ink, letterSpacing: '-0.02em', lineHeight: 1.05,
            maxWidth: 420,
          }}>
            Cloud security, architected with intent.
          </div>
          <div style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 10, letterSpacing: '0.14em',
            textTransform: 'uppercase', color: PALETTE.dim, marginTop: 10,
          }}>Greg · Cloud Security Officer & Architect</div>
        </div>
      </div>
      <CornerLabel side="tl">{label}</CornerLabel>
    </Surface>
  );
}

// Avatar / social: round and square avatar tile
function AvatarBoard({ Mark, markColor, bg, label }) {
  return (
    <Surface bg={PALETTE.paper}>
      <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
        {/* circle avatar */}
        <div style={{
          width: 160, height: 160, borderRadius: '50%',
          background: bg, display: 'grid', placeItems: 'center',
          boxShadow: '0 1px 0 rgba(0,0,0,0.04), 0 12px 32px -8px rgba(20,18,16,0.18)',
        }}>
          <Mark size={92} color={markColor}/>
        </div>
        {/* square tile */}
        <div style={{
          width: 160, height: 160, borderRadius: 14,
          background: bg, display: 'grid', placeItems: 'center',
          boxShadow: '0 1px 0 rgba(0,0,0,0.04), 0 12px 32px -8px rgba(20,18,16,0.18)',
        }}>
          <Mark size={92} color={markColor}/>
        </div>
      </div>
      <CornerLabel side="tl">{label}</CornerLabel>
      <CornerLabel side="br">avatar · app tile</CornerLabel>
    </Surface>
  );
}

// ─── BRIEF (intro) ───────────────────────────────────────────────────────────

function BriefBoard() {
  return (
    <div style={{
      width: '100%', height: '100%', background: PALETTE.paper,
      padding: '36px 44px', boxSizing: 'border-box',
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      fontFamily: 'Space Grotesk, sans-serif', color: PALETTE.ink,
    }}>
      <div>
        <div style={{
          fontFamily: 'JetBrains Mono, monospace', fontSize: 11, letterSpacing: '0.18em',
          textTransform: 'uppercase', color: PALETTE.dim, marginBottom: 14,
        }}>Logo · Personal Mark · Greg</div>
        <div style={{
          fontWeight: 600, fontSize: 36, lineHeight: 1.05, letterSpacing: '-0.025em',
          maxWidth: 720,
        }}>
          Three directions for a pure-icon mark.
        </div>
        <div style={{
          fontWeight: 400, fontSize: 15, lineHeight: 1.5, color: 'rgba(20,18,16,0.7)',
          maxWidth: 640, marginTop: 14,
        }}>
          Minimal · Swiss · Brutalist · Futuristic. Each direction is a geometric icon that
          encodes precision and defense without resorting to padlocks or shields.
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
        <BriefCol
          num="01" name="Aperture"
          desc="Vault dial as monogram. A bold geometric G constructed from a single circle and two precise cuts."
          tone="Swiss · editorial · monumental"
        />
        <BriefCol
          num="02" name="Stack"
          desc="Three chevrons ascending. Reads as defense in depth, signal, motion. Borrowed energy from Strava."
          tone="Bold · brutalist · kinetic"
        />
        <BriefCol
          num="03" name="Perimeter"
          desc="A walled enclosure with one precise gap — the gate — and an asset sitting inside it. A sigil."
          tone="Futuristic · technical · minimal"
        />
      </div>
    </div>
  );
}

function BriefCol({ num, name, desc, tone }) {
  return (
    <div style={{ borderTop: `1px solid ${PALETTE.guideHard}`, paddingTop: 14 }}>
      <div style={{
        fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
        letterSpacing: '0.12em', color: PALETTE.dim, marginBottom: 8,
      }}>{num}</div>
      <div style={{
        fontWeight: 600, fontSize: 20, letterSpacing: '-0.015em', marginBottom: 8,
      }}>{name}</div>
      <div style={{
        fontSize: 12.5, lineHeight: 1.5, color: 'rgba(20,18,16,0.72)', marginBottom: 12,
      }}>{desc}</div>
      <div style={{
        fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
        letterSpacing: '0.1em', textTransform: 'uppercase',
        color: PALETTE.dim,
      }}>{tone}</div>
    </div>
  );
}

// ─── APP ─────────────────────────────────────────────────────────────────────

function App() {
  return (
    <DesignCanvas>

      <DCSection id="brief" title="Brief" subtitle="The three directions, side-by-side comparison below">
        <DCArtboard id="brief" label="Read me first" width={920} height={460}>
          <BriefBoard/>
        </DCArtboard>
      </DCSection>

      {/* ─── 01 APERTURE ─────────────────────────────────────────────────── */}
      <DCSection id="aperture" title="01 · Aperture"
        subtitle="Vault dial geometry. The G is built from one circle, one mouth and one spur. Pure black on warm paper.">
        <DCArtboard id="ap-hero" label="Mark" width={420} height={420}>
          <HeroBoard Mark={ApertureMark} color={PALETTE.ink} label="01 · Aperture" name="ink on paper"/>
        </DCArtboard>
        <DCArtboard id="ap-construction" label="Construction" width={420} height={420}>
          <ConstructionBoard ConstructionView={ApertureConstruction} label="Construction"/>
        </DCArtboard>
        <DCArtboard id="ap-dark" label="Inverse" width={420} height={420}>
          <DarkBoard Mark={ApertureMark} color={PALETTE.paper} label="Inverse"/>
        </DCArtboard>
        <DCArtboard id="ap-scale" label="Scale" width={920} height={260}>
          <ScaleBoard Mark={ApertureMark} color={PALETTE.ink} label="Scale · 120 → 16 px"/>
        </DCArtboard>
        <DCArtboard id="ap-app" label="Browser & site" width={520} height={420}>
          <ApplicationBoard Mark={ApertureMark} markColor={PALETTE.ink} label="In situ"/>
        </DCArtboard>
        <DCArtboard id="ap-avatar" label="Avatar" width={520} height={420}>
          <AvatarBoard Mark={ApertureMark} markColor={PALETTE.paper} bg={PALETTE.ink} label="Avatar"/>
        </DCArtboard>
      </DCSection>

      {/* ─── 02 STACK ────────────────────────────────────────────────────── */}
      <DCSection id="stack" title="02 · Stack"
        subtitle="Three chevrons stacked — defense in depth, ascent, signal. Vermillion accent, lifted from Strava but distinct.">
        <DCArtboard id="st-hero" label="Mark" width={420} height={420}>
          <HeroBoard Mark={StackMark} color={PALETTE.vermillion} label="02 · Stack" name="vermillion on paper"/>
        </DCArtboard>
        <DCArtboard id="st-construction" label="Construction" width={420} height={420}>
          <ConstructionBoard ConstructionView={StackConstruction} label="Construction"/>
        </DCArtboard>
        <DCArtboard id="st-dark" label="Inverse" width={420} height={420}>
          <DarkBoard Mark={StackMark} color={PALETTE.vermillion} label="Inverse"/>
        </DCArtboard>
        <DCArtboard id="st-scale" label="Scale" width={920} height={260}>
          <ScaleBoard Mark={StackMark} color={PALETTE.vermillion} label="Scale · 120 → 16 px"/>
        </DCArtboard>
        <DCArtboard id="st-app" label="Browser & site" width={520} height={420}>
          <ApplicationBoard Mark={StackMark} markColor={PALETTE.vermillion} label="In situ"/>
        </DCArtboard>
        <DCArtboard id="st-avatar" label="Avatar" width={520} height={420}>
          <AvatarBoard Mark={StackMark} markColor={PALETTE.paper} bg={PALETTE.vermillion} label="Avatar"/>
        </DCArtboard>
      </DCSection>

      {/* ─── 03 PERIMETER ────────────────────────────────────────────────── */}
      <DCSection id="perimeter" title="03 · Perimeter"
        subtitle="Bastion outline with one precise gate; a single block inside, in electric blue. A technical sigil.">
        <DCArtboard id="pm-hero" label="Mark" width={420} height={420}>
          <HeroBoard Mark={PerimeterMark} color={PALETTE.ink} label="03 · Perimeter" name="ink + electric"/>
        </DCArtboard>
        <DCArtboard id="pm-construction" label="Construction" width={420} height={420}>
          <ConstructionBoard ConstructionView={PerimeterConstruction} label="Construction"/>
        </DCArtboard>
        <DCArtboard id="pm-dark" label="Inverse" width={420} height={420}>
          <Surface bg={PALETTE.dark}>
            <PerimeterMark size={300} frameColor={PALETTE.paper} blockColor={PALETTE.electric}/>
            <CornerLabel side="tl" color={PALETTE.paperDim}>Inverse</CornerLabel>
          </Surface>
        </DCArtboard>
        <DCArtboard id="pm-scale" label="Scale" width={920} height={260}>
          <Surface bg={PALETTE.paper} style={{ flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 40, padding: '0 32px' }}>
              {[120, 80, 56, 40, 24, 16].map(s => (
                <div key={s} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
                  <PerimeterMark size={s}/>
                  <div style={{
                    fontFamily: 'JetBrains Mono, monospace', fontSize: 9, letterSpacing: '0.1em',
                    color: PALETTE.dim, fontWeight: 500,
                  }}>{s}px</div>
                </div>
              ))}
            </div>
            <CornerLabel side="tl">Scale · 120 → 16 px</CornerLabel>
            <CornerLabel side="br">favicon ←→ marquee</CornerLabel>
          </Surface>
        </DCArtboard>
        <DCArtboard id="pm-app" label="Browser & site" width={520} height={420}>
          <ApplicationBoard
            Mark={(p) => <PerimeterMark {...p} frameColor={p.color} blockColor={PALETTE.electric}/>}
            markColor={PALETTE.ink}
            label="In situ"
          />
        </DCArtboard>
        <DCArtboard id="pm-avatar" label="Avatar" width={520} height={420}>
          <Surface bg={PALETTE.paper}>
            <div style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
              <div style={{
                width: 160, height: 160, borderRadius: '50%',
                background: PALETTE.ink, display: 'grid', placeItems: 'center',
                boxShadow: '0 12px 32px -8px rgba(20,18,16,0.18)',
              }}>
                <PerimeterMark size={92} frameColor={PALETTE.paper} blockColor={PALETTE.electric}/>
              </div>
              <div style={{
                width: 160, height: 160, borderRadius: 14,
                background: PALETTE.ink, display: 'grid', placeItems: 'center',
                boxShadow: '0 12px 32px -8px rgba(20,18,16,0.18)',
              }}>
                <PerimeterMark size={92} frameColor={PALETTE.paper} blockColor={PALETTE.electric}/>
              </div>
            </div>
            <CornerLabel side="tl">Avatar</CornerLabel>
            <CornerLabel side="br">avatar · app tile</CornerLabel>
          </Surface>
        </DCArtboard>
      </DCSection>

    </DesignCanvas>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
