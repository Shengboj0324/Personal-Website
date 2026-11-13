// Shared pieces of the 3D world: renderer, asset loading, baked materials, small animations.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

// Blender (x, y, z) maps to three.js (x, z, -y). These match studio/kit.py.
export const SUN = new THREE.Vector3(0.64, 0.68, 0.36).normalize();
export const WATER_Y = -1.0;
export const SKY = { horizon: new THREE.Color('#fbe9cf'), mid: new THREE.Color('#dcecea'), zenith: new THREE.Color('#a9d6ee') };
export const HAZE = new THREE.Color('#eef6ee');

const draco = new DRACOLoader();
draco.setDecoderPath('/assets/world/draco/');
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(draco);
const textureLoader = new THREE.TextureLoader();

export function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2'));
  } catch {
    return false;
  }
}

export function pickTier() {
  const small = window.matchMedia('(max-width: 820px)').matches;
  const cores = navigator.hardwareConcurrency || 4;
  const memory = navigator.deviceMemory || 8;
  const low = small || cores <= 4 || memory <= 4;
  return low
    ? { name: 'low', dpr: Math.min(window.devicePixelRatio || 1, 1.5), depth: false, texture: '1k', msaa: false }
    : { name: 'high', dpr: Math.min(window.devicePixelRatio || 1, 2), depth: true, texture: '2k', msaa: true };
}

export function createRenderer(canvas, tier, alpha = false) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: tier.msaa, alpha, powerPreference: 'high-performance' });
  renderer.setPixelRatio(tier.dpr);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  return renderer;
}

const AXES = { x: new THREE.Vector3(1, 0, 0), y: new THREE.Vector3(0, 0, -1), z: new THREE.Vector3(0, 1, 0) };

/** Load one island: geometry, its baked light atlas, moving parts and hotspots. */
export async function loadIsland(asset, tier) {
  const textureUrl = tier.texture === '1k' && asset.tex1k ? asset.tex1k : asset.tex;
  const [gltf, texture] = await Promise.all([
    gltfLoader.loadAsync(asset.glb),
    asset.tex ? textureLoader.loadAsync(textureUrl) : Promise.resolve(null),
  ]);
  if (texture) {
    texture.flipY = false;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
  }
  const baked = new THREE.MeshBasicMaterial({ map: texture });
  const root = gltf.scene;
  const movers = [];
  const hotspots = [];
  const byNode = new Map();
  root.traverse((node) => {
    const match = /^hs_(\d+)/.exec(node.name);
    if (match) hotspots.push({ index: Number(match[1]), node });
    if (node.userData.anim) {
      const kind = node.userData.anim;
      const mover = {
        node, kind, materials: [],
        speed: node.userData.anim_speed ?? 1,
        amp: node.userData.anim_amp ?? (kind === 'bob' ? 0.05 : 8),
        tilt: node.userData.anim_tilt ?? 0,
        axis: AXES[node.userData.anim_axis] || AXES.z,
        phase: Math.random() * Math.PI * 2,
        position: node.position.clone(),
        quaternion: node.quaternion.clone(),
      };
      movers.push(mover);
      byNode.set(node, mover);
    }
    if (!node.isMesh) return;
    // An object with several materials arrives as a group of meshes; its tags live on the group.
    const owner = node.userData.anim || node.userData.keep_material ? node : node.parent;
    const tags = owner ? owner.userData : {};
    const keep = Boolean(tags.keep_material);
    if (!keep && texture) {
      node.material = baked;
    } else if (keep) {
      // Screens keep their image; glass and light beams keep their own colour and opacity.
      const source = node.material;
      const map = source.emissiveMap || source.map || null;
      if (map) map.colorSpace = THREE.SRGBColorSpace;
      const glass = Boolean(tags.glass) || source.transparent || source.opacity < 1;
      const glowing = source.emissive && source.emissive.r + source.emissive.g + source.emissive.b > 0.02;
      node.material = new THREE.MeshBasicMaterial({
        map, color: map ? 0xffffff : (glowing ? source.emissive : source.color), side: THREE.DoubleSide,
        transparent: glass, opacity: glass ? Math.max(0.06, source.opacity) : 1, depthWrite: !glass,
      });
      if (glass) node.renderOrder = 3;
    }
    const mover = byNode.get(owner);
    if (mover && mover.kind === 'pulse') {
      node.material = node.material.clone();
      mover.materials.push({ material: node.material, colour: node.material.color.clone() });
    }
  });
  hotspots.sort((a, b) => a.index - b.index);
  const box = new THREE.Box3().setFromObject(root);
  return { root, movers, hotspots, box, baked };
}

/** Lit (non-baked) model, used for the boat that turns relative to the sun. */
export async function loadLit(url) {
  const gltf = await gltfLoader.loadAsync(url);
  const movers = [];
  gltf.scene.traverse((node) => {
    if (node.isMesh) {
      const source = node.material;
      node.material = new THREE.MeshLambertMaterial({
        color: source.color, emissive: source.emissive, emissiveIntensity: source.emissiveIntensity ?? 1,
        side: THREE.DoubleSide,
      });
    }
    if (node.userData.anim) movers.push({ node, name: node.name, quaternion: node.quaternion.clone() });
  });
  return { root: gltf.scene, movers };
}

const spinQ = new THREE.Quaternion();
const tiltQ = new THREE.Quaternion();
const X = new THREE.Vector3(1, 0, 0);

export function updateMovers(movers, time, still = false) {
  for (const m of movers) {
    const t = still ? 0 : time * m.speed + m.phase;
    if (m.kind === 'spin' || m.kind === 'orbit') {
      spinQ.setFromAxisAngle(m.axis, still ? 0 : time * m.speed);
      m.node.quaternion.copy(m.quaternion).multiply(spinQ);
    } else if (m.kind === 'sway') {
      spinQ.setFromAxisAngle(m.axis, Math.sin(t) * THREE.MathUtils.degToRad(m.amp));
      m.node.quaternion.copy(m.quaternion).multiply(spinQ);
    } else if (m.kind === 'bob') {
      m.node.position.copy(m.position);
      m.node.position.y += Math.sin(t) * m.amp;
      if (m.tilt) {
        tiltQ.setFromAxisAngle(X, Math.sin(t * 0.8 + 1) * THREE.MathUtils.degToRad(m.tilt));
        m.node.quaternion.copy(m.quaternion).multiply(tiltQ);
      }
    } else if (m.kind === 'pulse') {
      const k = still ? 1 : 1 + 0.16 * Math.sin(t * 2.2);
      for (const item of m.materials) item.material.color.copy(item.colour).multiplyScalar(k);
    }
  }
}

/** Half-resolution depth of the solid scene, so the sea can draw shorelines and foam. */
export function createDepthPass(renderer) {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(Math.max(2, size.x >> 1), Math.max(2, size.y >> 1), {
    depthBuffer: true, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
  });
  target.depthTexture = new THREE.DepthTexture(target.width, target.height);
  target.depthTexture.type = THREE.UnsignedIntType;
  const material = new THREE.MeshBasicMaterial({ colorWrite: false });
  return {
    texture: target.depthTexture,
    resize() {
      renderer.getDrawingBufferSize(size);
      target.setSize(Math.max(2, size.x >> 1), Math.max(2, size.y >> 1));
    },
    render(scene, camera, hidden) {
      const was = hidden.map((object) => object.visible);
      for (const object of hidden) object.visible = false;
      scene.overrideMaterial = material;
      renderer.setRenderTarget(target);
      renderer.clear();
      renderer.render(scene, camera);
      renderer.setRenderTarget(null);
      scene.overrideMaterial = null;
      hidden.forEach((object, i) => { object.visible = was[i]; });
    },
    dispose() { target.dispose(); },
  };
}

export const damp = (current, target, lambda, dt) => current + (target - current) * (1 - Math.exp(-lambda * dt));
export const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
