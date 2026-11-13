// A stylised sea: clear shallows, foam on every shoreline, drifting light, a wake behind the boat.
import * as THREE from 'three';
import { HAZE, SUN, WATER_Y } from './core.js';

const MAX_ISLANDS = 12;

const vertexShader = /* glsl */`
  varying vec3 vWorld;
  varying float vViewZ;
  void main() {
    vec4 world = modelMatrix * vec4(position, 1.0);
    vWorld = world.xyz;
    vec4 view = viewMatrix * world;
    vViewZ = view.z;
    gl_Position = projectionMatrix * view;
  }
`;

const fragmentShader = /* glsl */`
  precision highp float;
  #include <packing>
  varying vec3 vWorld;
  varying float vViewZ;
  uniform float uTime;
  uniform sampler2D tDepth;
  uniform float uHasDepth;
  uniform vec2 uResolution;
  uniform float uNear;
  uniform float uFar;
  uniform vec3 uShallow;
  uniform vec3 uMid;
  uniform vec3 uDeep;
  uniform vec3 uFoam;
  uniform vec3 uHaze;
  uniform vec3 uSky;
  uniform vec3 uSun;
  uniform float uFogNear;
  uniform float uFogFar;
  uniform vec3 uIslands[${MAX_ISLANDS}];
  uniform int uIslandCount;
  uniform vec4 uBoat;      // x, z, heading cos, heading sin
  uniform float uBoatSpeed;
  uniform float uEdge;     // > 0: fade to transparent at this radius (single-island viewer)
  uniform vec2 uCentre;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) { v += a * noise(p); p = p * 2.03 + 17.0; a *= 0.5; }
    return v;
  }

  void main() {
    vec2 p = vWorld.xz;
    vec3 toCamera = normalize(cameraPosition - vWorld);

    // How much water lies between this point and the sea bed or an island.
    float depth = 40.0;
    if (uHasDepth > 0.5) {
      float sceneZ = perspectiveDepthToViewZ(texture2D(tDepth, gl_FragCoord.xy / uResolution).x, uNear, uFar);
      depth = max(0.0, (vViewZ - sceneZ) * max(0.18, toCamera.y));
    }
    // Analytic shelf around each island keeps shallows soft and adds a contact shadow.
    float shelf = 40.0;
    float shade = 0.0;
    for (int i = 0; i < ${MAX_ISLANDS}; i++) {
      if (i >= uIslandCount) break;
      vec3 isle = uIslands[i];
      float d = distance(p, isle.xy) - isle.z;
      shelf = min(shelf, d);
      vec2 shadowCentre = isle.xy - uSun.xz * 1.7;
      shade = max(shade, 1.0 - smoothstep(isle.z * 0.55, isle.z * 1.22, distance(p, shadowCentre)));
    }
    float shelfDepth = max(0.0, shelf) * 0.55 + 0.25;
    float water = uHasDepth > 0.5 ? min(depth, shelfDepth + 1.2) : shelfDepth;

    // Slow swell and drifting light, in two layers moving against each other.
    float swell = fbm(p * 0.07 + vec2(uTime * 0.035, -uTime * 0.022));
    float ripple = fbm(p * 0.42 + vec2(-uTime * 0.11, uTime * 0.07));
    vec2 q = p * 0.55 + vec2(uTime * 0.05, uTime * 0.03) + ripple * 0.9;
    float cells = abs(noise(q) - 0.5) + abs(noise(q * 1.9 + 7.3) - 0.5) * 0.6;
    float caustic = smoothstep(0.16, 0.0, cells);

    vec3 colour = mix(uShallow, uMid, smoothstep(0.0, 2.2, water));
    colour = mix(colour, uDeep, smoothstep(1.6, 9.0, water) * 0.92);
    colour = mix(colour, colour * 1.07 + 0.02, swell);
    colour += caustic * mix(0.11, 0.035, smoothstep(0.5, 6.0, water));

    // Sky on the surface at grazing angles, and a soft glitter path toward the sun.
    float fresnel = pow(1.0 - max(0.0, toCamera.y), 3.0);
    colour = mix(colour, uSky, fresnel * 0.38);
    vec3 normal = normalize(vec3((ripple - 0.5) * 0.5, 1.0, (swell - 0.5) * 0.5));
    float glint = pow(max(0.0, dot(reflect(-uSun, normal), toCamera)), 60.0);
    colour += glint * 0.55;
    float sparkle = step(0.986, noise(p * 3.1 + floor(uTime * 2.0) * 0.37)) * smoothstep(0.55, 0.8, ripple);
    colour += sparkle * 0.5;

    colour *= 1.0 - shade * 0.2;

    // Shoreline foam: a bright lip plus rings that drift outward.
    float foam = 0.0;
    if (uHasDepth > 0.5) {
      float lip = 1.0 - smoothstep(0.02, 0.1 + 0.06 * ripple, depth);
      float ring = smoothstep(0.75, 0.95, sin(depth * 9.0 - uTime * 1.3 + ripple * 5.0)) * (1.0 - smoothstep(0.25, 0.95, depth));
      foam = max(lip * 0.85, ring * 0.5);
    } else {
      float ring = smoothstep(0.7, 0.95, sin(shelf * 5.0 - uTime * 1.3 + ripple * 4.0)) * (1.0 - smoothstep(0.0, 1.4, shelf));
      foam = ring * 0.5 * step(0.0, shelf);
    }

    // Wake: two diverging arms and a churned strip behind the stern.
    vec2 rel = p - uBoat.xy;
    vec2 local = vec2(dot(rel, vec2(uBoat.z, uBoat.w)), dot(rel, vec2(-uBoat.w, uBoat.z)));
    float behind = -local.x;
    if (behind > 0.2 && behind < 16.0) {
      float fade = (1.0 - behind / 16.0) * smoothstep(0.2, 1.2, behind) * uBoatSpeed;
      float arm = abs(abs(local.y) - behind * 0.3);
      float arms = smoothstep(0.16 + behind * 0.015, 0.0, arm) * (0.6 + 0.4 * ripple);
      float churn = smoothstep(0.42, 0.0, abs(local.y)) * smoothstep(5.0, 0.0, behind) * (0.5 + 0.5 * noise(p * 6.0 - uTime));
      foam = max(foam, (arms * 0.75 + churn) * fade);
    }
    colour = mix(colour, uFoam, clamp(foam, 0.0, 1.0));

    float alpha = uHasDepth > 0.5 ? mix(0.62, 1.0, smoothstep(0.0, 1.4, depth)) : 1.0;
    alpha = max(alpha, foam);

    float fog = smoothstep(uFogNear, uFogFar, -vViewZ);
    colour = mix(colour, uHaze, fog);
    if (uEdge > 0.0) alpha *= 1.0 - smoothstep(uEdge * 0.72, uEdge, distance(p, uCentre));
    gl_FragColor = vec4(colour, alpha);
    #include <colorspace_fragment>
  }
`;

export function createOcean({ size = 900, edge = 0 } = {}) {
  const geometry = edge ? new THREE.CircleGeometry(edge, 64) : new THREE.PlaneGeometry(size, size, 1, 1);
  geometry.rotateX(-Math.PI / 2);
  const uniforms = {
    uTime: { value: 0 },
    tDepth: { value: null },
    uHasDepth: { value: 0 },
    uResolution: { value: new THREE.Vector2(1, 1) },
    uNear: { value: 1 },
    uFar: { value: 4000 },
    uShallow: { value: new THREE.Color('#b9f4e2') },
    uMid: { value: new THREE.Color('#62d3c9') },
    uDeep: { value: new THREE.Color('#3bb0bd') },
    uFoam: { value: new THREE.Color('#f7fffb') },
    uHaze: { value: HAZE.clone() },
    uSky: { value: new THREE.Color('#e8f6f3') },
    uSun: { value: SUN.clone() },
    uFogNear: { value: 70 },
    uFogFar: { value: 260 },
    uIslands: { value: Array.from({ length: MAX_ISLANDS }, () => new THREE.Vector3(0, 0, 0)) },
    uIslandCount: { value: 0 },
    uBoat: { value: new THREE.Vector4(1e5, 1e5, 1, 0) },
    uBoatSpeed: { value: 0 },
    uEdge: { value: edge },
    uCentre: { value: new THREE.Vector2(0, 0) },
  };
  const material = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms, transparent: true, depthWrite: false });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.y = WATER_Y;
  mesh.renderOrder = 5;
  mesh.frustumCulled = false;
  return {
    mesh, uniforms,
    setIslands(list) {
      uniforms.uIslandCount.value = Math.min(list.length, MAX_ISLANDS);
      list.slice(0, MAX_ISLANDS).forEach((item, i) => uniforms.uIslands.value[i].set(item.x, item.z, item.r));
    },
  };
}
