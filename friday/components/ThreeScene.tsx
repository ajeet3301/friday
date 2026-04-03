"use client";

/**
 * ThreeScene.tsx
 *
 * Fixed 3D canvas. Camera scrolls along Z via GSAP ScrollTrigger.
 * Mouse drives subtle parallax tilt.
 * Theme changes smoothly animate lights + scene background via GSAP.
 *
 * Section layout:
 *   z =   0  → Icosahedron  (Hero)
 *   z = -15  → Spheres      (Audio)
 *   z = -30  → Cube         (Vision)
 *   z = -45  → Particles    (Waitlist)
 */

import { useRef, useEffect, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";
import { useThemeStore } from "@/store/useTheme";

gsap.registerPlugin(ScrollTrigger);

// ─── Palette ─────────────────────────────────────────────────────────────────

const P = {
  dark: {
    bg:      new THREE.Color(0x06010f),
    fog:     new THREE.Color(0x08021a),
    amb:     new THREE.Color(0x1a0a3d),
    dir:     new THREE.Color(0x6d28d9),
    ambI: 0.4, dirI: 1.0, fogN: 20, fogF: 95,
  },
  light: {
    bg:      new THREE.Color(0xe8e4ff),
    fog:     new THREE.Color(0xede9fe),
    amb:     new THREE.Color(0xffffff),
    dir:     new THREE.Color(0xc4b5fd),
    ambI: 1.6, dirI: 0.5, fogN: 25, fogF: 105,
  },
} as const;

// ─── Camera rig ──────────────────────────────────────────────────────────────

function CameraRig() {
  const { camera }       = useThree();
  const setCameraZ       = useThemeStore((s) => s.setCameraZ);
  const setSection       = useThemeStore((s) => s.setActiveSection);
  const setProgress      = useThemeStore((s) => s.setScrollProgress);
  const t                = useRef({ z: 5, mx: 0, my: 0 });

  // Mouse parallax
  useEffect(() => {
    const fn = (e: MouseEvent) => {
      t.current.mx = ((e.clientX / window.innerWidth)  - 0.5) * 2;
      t.current.my = ((e.clientY / window.innerHeight) - 0.5) * 2;
    };
    window.addEventListener("mousemove", fn);
    return () => window.removeEventListener("mousemove", fn);
  }, []);

  // Scroll → camera Z
  useEffect(() => {
    const overlay = document.getElementById("overlay");
    if (!overlay) return;

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger:  overlay,
        start:    "top top",
        end:      "bottom bottom",
        scrub:    1.8,
        onUpdate: (self) => {
          const p = self.progress;
          setProgress(p);
          setSection(Math.min(3, Math.floor(p * 4)));
          const bar = document.getElementById("progress-bar");
          if (bar) bar.style.width = `${p * 100}%`;
        },
      },
    });
    tl.to(t.current, { z: -45, ease: "none" });

    return () => { tl.kill(); ScrollTrigger.getAll().forEach((s) => s.kill()); };
  }, [setProgress, setSection]);

  useFrame((_, dt) => {
    const lf = 1 - Math.pow(0.04, dt * 60);
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, t.current.z, lf * 0.55);
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, t.current.mx * 1.2, lf * 0.25);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, -t.current.my * 0.7, lf * 0.25);
    camera.lookAt(t.current.mx * 0.4, -t.current.my * 0.25, camera.position.z - 8);
    setCameraZ(camera.position.z);
  });

  return null;
}

// ─── Lighting ─────────────────────────────────────────────────────────────────

function Lighting() {
  const theme   = useThemeStore((s) => s.theme);
  const ambRef  = useRef<THREE.AmbientLight>(null!);
  const dirRef  = useRef<THREE.DirectionalLight>(null!);
  const { scene } = useThree();

  // Init scene background + fog once
  useEffect(() => {
    scene.background = P.dark.bg.clone();
    scene.fog        = new THREE.Fog(P.dark.fog, P.dark.fogN, P.dark.fogF);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Animate on theme change
  useEffect(() => {
    const p = P[theme];
    gsap.to(scene.background as THREE.Color, { r: p.bg.r, g: p.bg.g, b: p.bg.b, duration: 0.7, ease: "power2.inOut" });
    if (scene.fog instanceof THREE.Fog) {
      gsap.to(scene.fog.color, { r: p.fog.r, g: p.fog.g, b: p.fog.b, duration: 0.7 });
      gsap.to(scene.fog, { near: p.fogN, far: p.fogF, duration: 0.7 });
    }
    if (ambRef.current) {
      gsap.to(ambRef.current.color, { r: p.amb.r, g: p.amb.g, b: p.amb.b, duration: 0.6 });
      gsap.to(ambRef.current, { intensity: p.ambI, duration: 0.6 });
    }
    if (dirRef.current) {
      gsap.to(dirRef.current.color, { r: p.dir.r, g: p.dir.g, b: p.dir.b, duration: 0.6 });
      gsap.to(dirRef.current, { intensity: p.dirI, duration: 0.6 });
    }
  }, [theme, scene]);

  const p = P[theme];
  return (
    <>
      <ambientLight ref={ambRef} color={p.amb} intensity={p.ambI} />
      <directionalLight ref={dirRef} color={p.dir} intensity={p.dirI} position={[8, 10, 5]} castShadow />
      <pointLight color="#a78bfa" intensity={2.2}  position={[0,   4,  0]} distance={55} decay={2} />
      <pointLight color="#60a5fa" intensity={1.3}  position={[-6, -3, -8]} distance={45} decay={2} />
    </>
  );
}

// ─── Star field ───────────────────────────────────────────────────────────────

function Stars() {
  const isDark = useThemeStore((s) => s.theme === "dark");
  const pos    = useMemo(() => {
    const a = new Float32Array(2000 * 3);
    for (let i = 0; i < 2000; i++) {
      a[i*3]   = (Math.random() - 0.5) * 260;
      a[i*3+1] = (Math.random() - 0.5) * 260;
      a[i*3+2] = -Math.random() * 170;
    }
    return a;
  }, []);

  if (!isDark) return null;
  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" array={pos} count={2000} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial color="#c4b5fd" size={0.045} transparent opacity={0.65} sizeAttenuation />
    </points>
  );
}

// ─── Proximity opacity helper ─────────────────────────────────────────────────

function useOpacity(targetZ: number, range = 13) {
  const cz = useThemeStore((s) => s.cameraZ);
  return Math.max(0, 1 - Math.abs(cz - targetZ) / range);
}

// ─── 1. Hero Icosahedron (z = 0) ─────────────────────────────────────────────

function HeroShape() {
  const meshRef  = useRef<THREE.Mesh>(null!);
  const haloRef  = useRef<THREE.Mesh>(null!);
  const isDark   = useThemeStore((s) => s.theme === "dark");
  const op       = useOpacity(0);

  useFrame(({ clock: c }) => {
    const t = c.getElapsedTime();
    if (meshRef.current) {
      meshRef.current.rotation.x = t * 0.13;
      meshRef.current.rotation.y = t * 0.20;
      meshRef.current.position.y = Math.sin(t * 0.48) * 0.32;
      meshRef.current.scale.setScalar(1 + Math.sin(t * 0.85) * 0.026);
    }
    if (haloRef.current) {
      haloRef.current.rotation.x = t * 0.13;
      haloRef.current.rotation.y = t * 0.20;
    }
  });

  if (op < 0.01) return null;

  return (
    <group position={[0.6, 0, 0]}>
      <mesh ref={meshRef} castShadow>
        <icosahedronGeometry args={[2.3, 1]} />
        <MeshDistortMaterial
          color={isDark ? "#a78bfa" : "#7c3aed"}
          emissive={isDark ? "#4c1d95" : "#ede9fe"}
          emissiveIntensity={isDark ? 0.44 : 0.08}
          metalness={0.28} roughness={0.16}
          transparent opacity={op * (isDark ? 0.88 : 0.76)}
          distort={0.28} speed={2.2}
        />
      </mesh>
      {/* Wireframe halo */}
      <mesh ref={haloRef}>
        <icosahedronGeometry args={[2.78, 1]} />
        <meshBasicMaterial
          color={isDark ? "#a78bfa" : "#7c3aed"}
          wireframe transparent
          opacity={op * (isDark ? 0.11 : 0.07)}
        />
      </mesh>
      {isDark && <pointLight color="#a78bfa" intensity={op * 3.5} distance={10} decay={2} />}
    </group>
  );
}

// ─── 2. Audio Spheres (z = -15) ──────────────────────────────────────────────

const SPHERE_DATA = Array.from({ length: 14 }, (_, i) => {
  const a = (i / 14) * Math.PI * 2;
  const r = 2.5 + (i % 3) * 0.65;
  return {
    x: Math.cos(a) * r, y: Math.sin(i * 0.85) * 0.55,
    z: Math.sin(a) * r * 0.38,
    sz: 0.11 + (i % 4) * 0.055,
    spd: 0.28 + i * 0.065, ph: i * 0.48,
    primary: i % 2 === 0,
  };
});

function AudioSpheres() {
  const grp    = useRef<THREE.Group>(null!);
  const isDark = useThemeStore((s) => s.theme === "dark");
  const op     = useOpacity(-15);

  useFrame(({ clock: c }) => {
    const t = c.getElapsedTime();
    if (!grp.current) return;
    grp.current.rotation.y = t * 0.09;
    grp.current.children.forEach((child, i) => {
      if (i >= SPHERE_DATA.length) return;
      const d = SPHERE_DATA[i];
      child.position.y = d.y + Math.sin(t * d.spd + d.ph) * 0.36;
      child.scale.setScalar(1 + Math.sin(t * 2.1 + d.ph) * 0.12);
    });
  });

  if (op < 0.01) return null;

  return (
    <group ref={grp} position={[-0.4, 0, -15]}>
      {SPHERE_DATA.map((d, i) => (
        <mesh key={i} position={[d.x, d.y, d.z]}>
          <sphereGeometry args={[d.sz, 16, 16]} />
          <meshStandardMaterial
            color={d.primary ? (isDark ? "#a78bfa" : "#7c3aed") : (isDark ? "#60a5fa" : "#2563eb")}
            emissive={d.primary ? (isDark ? "#a78bfa" : "#7c3aed") : (isDark ? "#60a5fa" : "#2563eb")}
            emissiveIntensity={isDark ? 0.55 : 0.04}
            metalness={0.4} roughness={0.12}
            transparent opacity={op * (isDark ? 0.92 : 0.78)}
          />
        </mesh>
      ))}
      {/* Central sphere */}
      <mesh>
        <sphereGeometry args={[0.58, 32, 32]} />
        <MeshDistortMaterial
          color={isDark ? "#a78bfa" : "#7c3aed"}
          emissive={isDark ? "#6d28d9" : "#ede9fe"}
          emissiveIntensity={isDark ? 0.5 : 0.1}
          metalness={0.2} roughness={0.08}
          transparent opacity={op * 0.9}
          distort={0.22} speed={3}
        />
      </mesh>
      {isDark && <pointLight color="#a78bfa" intensity={op * 2.8} distance={12} decay={2} />}
    </group>
  );
}

// ─── 3. Vision Wireframe Cube (z = -30) ──────────────────────────────────────

const CORNERS: [number, number, number][] = [
  [ 1.78,  1.78,  1.78], [-1.78,  1.78,  1.78],
  [ 1.78, -1.78,  1.78], [-1.78, -1.78,  1.78],
  [ 1.78,  1.78, -1.78], [-1.78,  1.78, -1.78],
  [ 1.78, -1.78, -1.78], [-1.78, -1.78, -1.78],
];

function VisionCube() {
  const outer  = useRef<THREE.Group>(null!);
  const inner  = useRef<THREE.Mesh>(null!);
  const isDark = useThemeStore((s) => s.theme === "dark");
  const op     = useOpacity(-30);

  useFrame(({ clock: c }) => {
    const t = c.getElapsedTime();
    if (outer.current) {
      outer.current.rotation.x = t * 0.16;
      outer.current.rotation.y = t * 0.23;
      outer.current.position.y = Math.sin(t * 0.37) * 0.27;
    }
    if (inner.current) {
      inner.current.rotation.x = -t * 0.27;
      inner.current.rotation.z =  t * 0.18;
      inner.current.scale.setScalar(1 + Math.sin(t * 1.4) * 0.05);
    }
  });

  if (op < 0.01) return null;
  const wc = isDark ? "#60a5fa" : "#2563eb";

  return (
    <group ref={outer} position={[0.5, 0.2, -30]}>
      <mesh>
        <boxGeometry args={[3.6, 3.6, 3.6]} />
        <meshBasicMaterial color={wc} wireframe transparent opacity={op * (isDark ? 0.46 : 0.26)} />
      </mesh>
      <mesh ref={inner}>
        <boxGeometry args={[1.85, 1.85, 1.85]} />
        <meshStandardMaterial
          color={wc} emissive={isDark ? "#1d4ed8" : "#bfdbfe"}
          emissiveIntensity={isDark ? 0.44 : 0.1}
          metalness={0.65} roughness={0.12}
          transparent opacity={op * (isDark ? 0.72 : 0.62)}
        />
      </mesh>
      {CORNERS.map((pos, i) => (
        <mesh key={i} position={pos}>
          <sphereGeometry args={[0.09, 8, 8]} />
          <meshStandardMaterial
            color={wc} emissive={wc}
            emissiveIntensity={isDark ? 1.2 : 0.2}
            transparent opacity={op * 0.9}
          />
        </mesh>
      ))}
      {isDark && <pointLight color="#60a5fa" intensity={op * 2.2} distance={14} decay={2} />}
    </group>
  );
}

// ─── 4. Waitlist Particle Ring (z = -45) ─────────────────────────────────────

function WaitlistRing() {
  const pts    = useRef<THREE.Points>(null!);
  const isDark = useThemeStore((s) => s.theme === "dark");
  const op     = useOpacity(-45);

  const { pos, col } = useMemo(() => {
    const N   = 1400;
    const pos = new Float32Array(N * 3);
    const col = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      const ang = (i / N) * Math.PI * 2 * 9;
      const r   = 1.8 + (i / N) * 3.5;
      pos[i*3]   = Math.cos(ang) * r;
      pos[i*3+1] = (i / N - 0.5) * 5;
      pos[i*3+2] = Math.sin(ang) * r * 0.45;
      const m    = i / N;
      col[i*3]   = 0.65 + m * 0.12;
      col[i*3+1] = 0.55 - m * 0.17;
      col[i*3+2] = 0.98 - m * 0.18;
    }
    return { pos, col };
  }, []);

  useFrame(({ clock: c }) => {
    const t = c.getElapsedTime();
    if (!pts.current) return;
    pts.current.rotation.y = t * 0.13;
    pts.current.rotation.x = Math.sin(t * 0.17) * 0.08;
  });

  if (op < 0.01) return null;
  return (
    <points ref={pts} position={[0, 0, -45]}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" array={pos} count={1400} itemSize={3} />
        <bufferAttribute attach="attributes-color"    array={col} count={1400} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={isDark ? 0.055 : 0.042} vertexColors
        transparent opacity={op * (isDark ? 0.88 : 0.52)}
        sizeAttenuation
      />
    </points>
  );
}

// ─── Export ───────────────────────────────────────────────────────────────────

export default function ThreeScene() {
  return (
    <div id="canvas-wrap" aria-hidden="true">
      <Canvas
        camera={{ fov: 60, near: 0.1, far: 220, position: [0, 0, 5] }}
        gl={{
          antialias: true, alpha: false,
          powerPreference: "high-performance",
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.0,
        }}
        shadows
        dpr={[1, 2]}
      >
        <Lighting />
        <Stars />
        <HeroShape />
        <AudioSpheres />
        <VisionCube />
        <WaitlistRing />
        <CameraRig />
      </Canvas>
    </div>
  );
}
