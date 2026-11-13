// The home page: a scroll-driven sail from the harbor past eight islands to a chart of the whole trip.
import * as THREE from 'three';
import {
  HAZE, SKY, SUN, WATER_Y, createDepthPass, createRenderer, damp, loadIsland, loadLit, smooth, updateMovers,
} from './core.js';
import { createOcean } from './ocean.js';

const VIEW_DIR = new THREE.Vector3(-9.1, 7.0, 15.1).normalize();
const WIND_FROM = new THREE.Vector2(-0.45, -0.89).normalize(); // blowing from the north-west (x, z)
const BOAT_SCALE = 1.7; // a toy boat, large enough to read beside the islands

function skyDome() {
  const material = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { uHorizon: { value: HAZE }, uMid: { value: new THREE.Color('#d3ecf1') }, uZenith: { value: SKY.zenith }, uWarm: { value: SKY.horizon }, uSun: { value: SUN } },
    vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vDir; uniform vec3 uHorizon, uMid, uZenith, uWarm, uSun;
      void main(){ float h = clamp(vDir.y, 0.0, 1.0);
        vec3 c = mix(uHorizon, uMid, smoothstep(0.0, 0.16, h)); c = mix(c, uZenith, smoothstep(0.1, 0.7, h));
        vec3 flat_sun = normalize(vec3(uSun.x, 0.08, uSun.z));
        float warm = pow(max(0.0, dot(normalize(vDir), flat_sun)), 3.0) * (1.0 - smoothstep(0.0, 0.3, h));
        c = mix(c, uWarm, warm * 0.75);
        float glow = pow(max(0.0, dot(normalize(vDir), uSun)), 6.0); c += vec3(1.0, 0.86, 0.62) * glow * 0.18;
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(3000, 32, 16), material);
  dome.renderOrder = -10;
  dome.frustumCulled = false;
  return dome;
}

function cloudField(span) {
  const group = new THREE.Group();
  const geometry = new THREE.IcosahedronGeometry(1, 2);
  const colours = [];
  const top = new THREE.Color('#ffffff');
  const bottom = new THREE.Color('#d9ecf0');
  const position = geometry.attributes.position;
  for (let i = 0; i < position.count; i++) {
    const c = bottom.clone().lerp(top, smooth(-0.6, 0.5, position.getY(i)));
    colours.push(c.r, c.g, c.b);
  }
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colours, 3));
  const material = new THREE.MeshBasicMaterial({ vertexColors: true, fog: false });
  let seed = 11;
  const random = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const count = Math.round(span / 15);
  for (let i = 0; i < count; i++) {
    const cluster = new THREE.Group();
    const scale = 3.4 + random() * 4.2;
    [[-0.9, 0.55], [-0.3, 0.82], [0.45, 0.7], [1.05, 0.5]].forEach(([dx, r], j) => {
      const puff = new THREE.Mesh(geometry, material);
      puff.position.set(dx * scale, (random() - 0.4) * 0.3 * scale, (random() - 0.5) * 0.5 * scale);
      puff.scale.set(r * scale * 1.15, r * scale * 0.72, r * scale * 0.9);
      puff.rotation.y = j;
      cluster.add(puff);
    });
    cluster.position.set(-60 + random() * (span + 120), 9 + random() * 13, -190 + random() * 120);
    cluster.userData.drift = 0.25 + random() * 0.35;
    group.add(cluster);
  }
  return group;
}

function routeRibbon(curve, samples = 520) {
  const positions = [];
  const sides = [];
  const normals = [];
  const along = [];
  const index = [];
  const point = new THREE.Vector3();
  const tangent = new THREE.Vector3();
  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    curve.getPoint(t, point);
    curve.getTangent(t, tangent);
    const nx = -tangent.z, nz = tangent.x;
    const len = Math.hypot(nx, nz) || 1;
    for (const side of [-1, 1]) {
      positions.push(point.x, WATER_Y + 0.05, point.z);
      sides.push(side);
      normals.push(nx / len, nz / len);
      along.push(t);
    }
    if (i < samples) index.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('side', new THREE.Float32BufferAttribute(sides, 1));
  geometry.setAttribute('across', new THREE.Float32BufferAttribute(normals, 2));
  geometry.setAttribute('along', new THREE.Float32BufferAttribute(along, 1));
  geometry.setIndex(index);
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: { uWidth: { value: 0.1 }, uProgress: { value: 0 }, uTime: { value: 0 }, uDashes: { value: 420 },
      uColour: { value: new THREE.Color('#f0785a') }, uPaper: { value: new THREE.Color('#fff7e8') }, uOpacity: { value: 0.85 } },
    vertexShader: `attribute float side; attribute vec2 across; attribute float along; uniform float uWidth; varying float vAlong; varying float vSide;
      void main(){ vAlong = along; vSide = side; vec3 p = position; p.xz += across * side * uWidth;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0); }`,
    fragmentShader: `uniform float uProgress, uTime, uDashes, uOpacity; uniform vec3 uColour, uPaper; varying float vAlong; varying float vSide;
      void main(){ float sailed = step(vAlong, uProgress);
        float dash = step(0.45, fract(vAlong * uDashes - uTime * 0.25));
        float a = dash * mix(0.55, 1.0, sailed) * uOpacity * smoothstep(1.0, 0.55, abs(vSide));
        vec3 c = mix(uPaper, uColour, sailed * 0.85 + 0.15);
        gl_FragColor = vec4(c, a);
        #include <colorspace_fragment>
      }`,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 6;
  mesh.frustumCulled = false;
  return mesh;
}

export async function startVoyage(root, tier, options = {}) {
  const data = JSON.parse(root.querySelector('[data-voyage-data]').textContent);
  const stage = root.querySelector('.voyage-stage');
  const canvas = root.querySelector('.voyage-canvas');
  const stops = data.stops;
  const last = stops.length - 1;
  const cards = [...root.querySelectorAll('[data-stop]')];
  const bridges = [...root.querySelectorAll('[data-bridge]')];
  const railButtons = [...root.querySelectorAll('[data-rail]')];
  const labels = [...root.querySelectorAll('[data-label]')];
  const loader = root.querySelector('.voyage-loader');
  const loaderBar = root.querySelector('.voyage-loader-bar');
  const still = Boolean(options.still);
  // In right-to-left editions the caption sits on the right, so the island is framed on the left.
  const side = document.documentElement.dir === 'rtl' ? -1 : 1;

  const renderer = createRenderer(canvas, tier);
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(HAZE, 70, 260);
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 4000);
  const dome = skyDome();
  scene.add(dome);
  scene.add(new THREE.HemisphereLight('#f2fbff', '#73bdb4', 1.25));
  const sun = new THREE.DirectionalLight('#fff1dc', 2.3);
  sun.position.copy(SUN).multiplyScalar(50);
  scene.add(sun);

  const ocean = createOcean({ size: 7000 });
  const islandStops = stops.filter((stop) => stop.slug);
  ocean.setIslands(islandStops.map((stop) => ({ x: stop.x, z: stop.z, r: stop.r })));
  scene.add(ocean.mesh);
  const xs = islandStops.map((stop) => stop.x);
  const zs = islandStops.map((stop) => stop.z);
  const span = Math.max(...xs) - Math.min(...xs);
  const centre = new THREE.Vector3((Math.max(...xs) + Math.min(...xs)) / 2, 0, (Math.max(...zs) + Math.min(...zs)) / 2);
  ocean.mesh.position.x = centre.x;
  const chartScale = Math.min(2.6, (span / Math.max(1, islandStops.length - 1)) / 14);
  const clouds = cloudField(span);
  scene.add(clouds);

  // Route: a mooring beside each island, a waypoint that leads the boat around its front, then open water.
  const moorings = stops.map((stop) => new THREE.Vector3(stop.mx, WATER_Y, stop.mz));
  const first = moorings[0];
  const points = [new THREE.Vector3(first.x - 22, WATER_Y, first.z + 12)];
  stops.forEach((stop, index) => {
    points.push(moorings[index]);
    if (index < last) points.push(new THREE.Vector3(stop.wx, WATER_Y, stop.wz));
  });
  points.push(new THREE.Vector3(moorings[last].x + 34, WATER_Y, moorings[last].z - 6));
  const curve = new THREE.CatmullRomCurve3(points, false, 'centripetal');
  const paramOf = (s) => (1 + 2 * s) / (points.length - 1);
  const ribbon = routeRibbon(curve);
  scene.add(ribbon);

  const depth = tier.depth ? createDepthPass(renderer) : null;
  if (depth) {
    ocean.uniforms.tDepth.value = depth.texture;
    ocean.uniforms.uHasDepth.value = 1;
  }
  const hiddenInDepth = [ocean.mesh, ribbon, clouds];

  // Assets arrive in sailing order; the harbor and the boat gate the first frame.
  const islands = new Map();
  const movers = [];
  let loaded = 0;
  const total = islandStops.length + 1;
  const progress = () => {
    loaded += 1;
    if (loaderBar) loaderBar.style.transform = `scaleX(${Math.min(1, loaded / 3)})`;
  };
  async function addIsland(stop) {
    try {
      const island = await loadIsland(data.assets[stop.slug], tier);
      island.root.position.set(stop.x, 0, stop.z);
      scene.add(island.root);
      islands.set(stop.slug, island);
      movers.push(...island.movers);
    } catch (error) {
      console.warn('Island failed to load:', stop.slug, error);
    }
    progress();
  }
  const boat = { root: new THREE.Group(), movers: [] };
  scene.add(boat.root);
  hiddenInDepth.push(boat.root);
  const boatReady = loadLit(data.boat).then((model) => {
    boat.root.add(model.root);
    boat.movers = model.movers;
    progress();
  }).catch((error) => console.warn('Boat failed to load', error));
  const firstIslands = Promise.all([addIsland(islandStops[0]), islandStops[1] ? addIsland(islandStops[1]) : null]);
  (async () => {
    await firstIslands;
    for (let i = 2; i < islandStops.length; i += 2) {
      await Promise.all([addIsland(islandStops[i]), islandStops[i + 1] ? addIsland(islandStops[i + 1]) : null]);
    }
  })();

  // ---- camera poses
  const size = new THREE.Vector2();
  let aspect = 1;
  let portrait = false;
  const pose = { position: new THREE.Vector3(), quaternion: new THREE.Quaternion(), shiftX: 0, shiftY: 0 };
  const lookMatrix = new THREE.Matrix4();
  const UP = new THREE.Vector3(0, 1, 0);
  function setPose(out, position, target, up = UP, shiftX = 0, shiftY = 0) {
    out.position.copy(position);
    lookMatrix.lookAt(position, target, up);
    out.quaternion.setFromRotationMatrix(lookMatrix);
    out.shiftX = shiftX;
    out.shiftY = shiftY;
    return out;
  }
  const makePose = () => ({ position: new THREE.Vector3(), quaternion: new THREE.Quaternion(), shiftX: 0, shiftY: 0 });
  const stopPose = makePose();
  const transitPose = makePose();
  const tmpA = new THREE.Vector3();
  const tmpB = new THREE.Vector3();
  const chartUp = new THREE.Vector3();

  function poseForStop(index, out) {
    const stop = stops[index];
    if (index === last) {
      // The chart: straight down on the whole archipelago, turned upright on tall screens.
      const hfov = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * aspect);
      const vfov = THREE.MathUtils.degToRad(camera.fov);
      const long = span + 86;
      const tall = aspect < 1;
      // On tall screens the caption takes the lower part, so the chart is fitted into the upper part.
      const height = tall ? (long / 2) / Math.tan(vfov / 2) / 0.6 : (long / 2) / Math.tan(hfov / 2);
      tmpA.set(centre.x, Math.max(120, height), centre.z + 0.01);
      chartUp.set(tall ? 1 : 0, 0, tall ? 0 : -1);
      return setPose(out, tmpA, tmpB.set(centre.x, 0, centre.z), chartUp, 0, tall ? 0.19 : 0.19);
    }
    const r = stop.r || 5;
    const distance = (index === 0 ? 25 : 23.5) * (r / 5) ** 0.6 * (portrait ? 1.95 : Math.max(1, 1.72 / aspect) ** 0.9);
    tmpB.set(stop.x + 0.1, 1.15, stop.z + 0.6);
    tmpA.copy(VIEW_DIR).multiplyScalar(distance).add(tmpB);
    return setPose(out, tmpA, tmpB, UP, portrait ? 0 : (index === 0 ? -0.2 : -0.17) * side, portrait ? 0.2 : -0.02);
  }

  // ---- scroll state
  let target = 0;
  let current = 0;
  let stride = 1;
  let top = 0;
  function measure() {
    const rect = root.getBoundingClientRect();
    top = rect.top + window.scrollY;
    stride = (root.offsetHeight - window.innerHeight) / last;
    renderer.setPixelRatio(tier.dpr);
    renderer.setSize(stage.clientWidth, stage.clientHeight, false);
    renderer.getDrawingBufferSize(size);
    aspect = stage.clientWidth / stage.clientHeight;
    portrait = aspect < 0.82;
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
    ocean.uniforms.uResolution.value.copy(size);
    if (depth) depth.resize();
    readScroll();
  }
  function readScroll() {
    target = THREE.MathUtils.clamp((window.scrollY - top) / stride, 0, last);
  }
  function go(index, behavior = 'smooth') {
    window.scrollTo({ top: top + THREE.MathUtils.clamp(index, 0, last) * stride, behavior: still ? 'auto' : behavior });
  }
  window.addEventListener('scroll', readScroll, { passive: true });
  window.addEventListener('resize', measure);
  new ResizeObserver(measure).observe(stage);
  root.addEventListener('click', (event) => {
    const element = event.target instanceof Element ? event.target : null;
    const step = element?.closest('[data-step]');
    if (step) { event.preventDefault(); go(Math.round(current) + Number(step.dataset.step)); return; }
    const link = element?.closest('a[href*="#stop-"]');
    if (!link) return;
    const index = stops.findIndex((stop) => link.getAttribute('href').endsWith(`#stop-${stop.id}`));
    if (index >= 0) { event.preventDefault(); go(index); }
  });
  const indexOfHash = () => stops.findIndex((stop) => `#stop-${stop.id}` === window.location.hash);
  const hashIndex = indexOfHash();
  window.addEventListener('hashchange', () => { const index = indexOfHash(); if (index >= 0) go(index); });

  const pointer = new THREE.Vector2();
  const pointerSmooth = new THREE.Vector2();
  if (!still) {
    window.addEventListener('pointermove', (event) => {
      if (event.pointerType !== 'mouse') return;
      pointer.set(event.clientX / window.innerWidth - 0.5, event.clientY / window.innerHeight - 0.5);
    }, { passive: true });
  }

  // ---- per-frame update
  const boatPoint = new THREE.Vector3();
  const boatTangent = new THREE.Vector3();
  const previousBoat = new THREE.Vector3();
  const yAxis = new THREE.Vector3(0, 1, 0);
  const q = new THREE.Quaternion();
  let heading = 0;
  let speed = 0;
  let activeCard = -1;
  let activeBridge = -1;
  let activeRail = -1;
  let visible = true;
  let running = false;
  let frame = 0;
  let time = 0;
  let previous = performance.now();
  let intro = still ? 1 : 0;
  let slowFrames = 0;
  let measured = 0;
  const projected = new THREE.Vector3();

  function setActive(list, index, previousIndex) {
    if (index === previousIndex) return index;
    if (previousIndex >= 0 && list[previousIndex]) { list[previousIndex].classList.remove('is-active'); list[previousIndex].inert = true; }
    if (index >= 0 && list[index]) { list[index].classList.add('is-active'); list[index].inert = false; }
    return index;
  }
  for (const card of cards) card.inert = true;

  function update(dt) {
    time += still ? 0 : dt;
    current = still ? target : damp(current, target, 5.5, dt);
    if (Math.abs(current - target) < 0.0005) current = target;
    const nearest = Math.round(current);
    const offset = Math.abs(current - nearest);
    const base = Math.floor(Math.min(current, last - 1e-6));
    const along = base + smooth(0.14, 0.86, current - base);
    const dock = 1 - smooth(0.1, 0.4, offset);
    const chart = nearest === last ? dock : 0;

    // boat
    curve.getPoint(paramOf(along), boatPoint);
    curve.getTangent(paramOf(Math.min(along + 0.01, last + 0.2)), boatTangent);
    const moved = boatPoint.distanceTo(previousBoat);
    previousBoat.copy(boatPoint);
    speed = damp(speed, Math.min(1, moved / Math.max(dt, 1e-3) / 9), 4, dt);
    const wanted = Math.atan2(-boatTangent.x, -boatTangent.z);
    let delta = wanted - heading;
    delta = Math.atan2(Math.sin(delta), Math.cos(delta));
    heading += delta * (still ? 1 : 1 - Math.exp(-6 * dt));
    const swell = Math.sin(time * 1.3) * 0.045 + Math.sin(time * 0.7 + 1) * 0.03;
    boat.root.position.set(boatPoint.x, WATER_Y + swell, boatPoint.z);
    boat.root.rotation.set(Math.sin(time * 1.1) * 0.035 + speed * 0.04, heading, Math.sin(time * 0.9 + 2) * 0.05 - delta * 1.4 - speed * 0.07, 'YXZ');
    // sail trim: the team's baseline rule, sail = 44/90 of the apparent wind angle
    const bowX = -Math.sin(heading), bowZ = -Math.cos(heading);
    const awa = Math.atan2(bowX * WIND_FROM.y - bowZ * WIND_FROM.x, bowX * WIND_FROM.x + bowZ * WIND_FROM.y);
    const trim = THREE.MathUtils.clamp((44 / 90) * awa, -1.5, 1.5);
    for (const mover of boat.movers) {
      let angle = 0;
      if (mover.name.startsWith('sail')) angle = -trim + Math.sin(time * 2.1) * 0.02;
      else if (mover.name.startsWith('rudder')) angle = THREE.MathUtils.clamp(delta * 6, -0.37, 0.37);
      else if (mover.name.startsWith('vane')) angle = -awa + Math.sin(time * 3.1) * 0.08;
      q.setFromAxisAngle(yAxis, angle);
      mover.node.quaternion.copy(mover.quaternion).multiply(q);
    }
    ocean.uniforms.uBoat.value.set(boatPoint.x, boatPoint.z, bowX, bowZ);
    ocean.uniforms.uBoatSpeed.value = speed;

    // camera: blend the sailing view with the framed view of the nearest stop
    poseForStop(nearest, stopPose);
    tmpB.set(boatPoint.x + 5.5 + speed * 2, 2.6, boatPoint.z - 5);
    tmpA.set(boatPoint.x - 5, portrait ? 13 : 8, boatPoint.z + (portrait ? 38 : 24.5));
    setPose(transitPose, tmpA, tmpB, UP, 0, portrait ? 0.08 : 0);
    const w = dock * dock * (3 - 2 * dock);
    pose.position.lerpVectors(transitPose.position, stopPose.position, w);
    pose.quaternion.slerpQuaternions(transitPose.quaternion, stopPose.quaternion, w);
    pose.shiftX = THREE.MathUtils.lerp(transitPose.shiftX, stopPose.shiftX, w);
    pose.shiftY = THREE.MathUtils.lerp(transitPose.shiftY, stopPose.shiftY, w);
    if (intro < 1) {
      intro = Math.min(1, intro + dt / 2.6);
      const e = 1 - (1 - intro) ** 3;
      pose.position.y += (1 - e) * 16;
      pose.position.z += (1 - e) * 26;
      pose.position.x -= (1 - e) * 10;
    }
    pointerSmooth.lerp(pointer, 1 - Math.exp(-3 * dt));
    camera.position.copy(pose.position);
    camera.quaternion.copy(pose.quaternion);
    if (!chart) camera.translateX(pointerSmooth.x * 1.6), camera.translateY(-pointerSmooth.y * 0.9);
    camera.setViewOffset(size.x, size.y, pose.shiftX * size.x, pose.shiftY * size.y, size.x, size.y);

    scene.fog.near = THREE.MathUtils.lerp(70, pose.position.y * 1.6 + 200, chart);
    scene.fog.far = THREE.MathUtils.lerp(260, pose.position.y * 5 + 900, chart);
    dome.position.copy(camera.position);
    const grow = THREE.MathUtils.lerp(1, chartScale, chart);
    for (const island of islands.values()) island.root.scale.setScalar(grow);
    ocean.uniforms.uFogNear.value = scene.fog.near;
    ocean.uniforms.uFogFar.value = scene.fog.far;
    ocean.uniforms.uTime.value = time;
    ribbon.material.uniforms.uTime.value = time;
    ribbon.material.uniforms.uProgress.value = paramOf(along);
    ribbon.material.uniforms.uWidth.value = THREE.MathUtils.lerp(0.085, 1.1, chart);
    ribbon.material.uniforms.uDashes.value = THREE.MathUtils.lerp(420, 120, chart);
    ribbon.material.uniforms.uOpacity.value = THREE.MathUtils.lerp(0.75, 1, chart);
    boat.root.scale.setScalar(THREE.MathUtils.lerp(BOAT_SCALE, chartScale * 2.4, chart));
    for (const cluster of clouds.children) {
      cluster.position.x += cluster.userData.drift * dt * (still ? 0 : 1);
      if (cluster.position.x > span + 70) cluster.position.x = -70;
    }
    clouds.visible = chart < 0.5;
    updateMovers(movers, time, still);

    // captions and controls
    activeCard = setActive(cards, dock > 0.5 ? nearest : -1, activeCard);
    const mid = current - base;
    activeBridge = setActive(bridges, mid > 0.3 && mid < 0.7 ? base : -1, activeBridge);
    if (nearest !== activeRail) {
      railButtons.forEach((button) => {
        if (button.dataset.rail === String(nearest)) button.setAttribute('aria-current', 'step');
        else button.removeAttribute('aria-current');
      });
      activeRail = nearest;
      root.dataset.stop = stops[nearest].id;
    }
    root.style.setProperty('--voyage-progress', (current / last).toFixed(4));
    root.classList.toggle('is-sailing', dock < 0.5);
    root.classList.toggle('is-chart', chart > 0.6);
  }

  function placeLabels() {
    camera.updateMatrixWorld();
    const chart = root.classList.contains('is-chart');
    for (const label of labels) {
      const stop = stops[Number(label.dataset.label)];
      projected.set(stop.x, chart ? 0 : 6.2, stop.z).project(camera);
      const here = Math.round(current) === Number(label.dataset.label) && !chart && !root.classList.contains('is-sailing');
      const near = chart || Math.hypot(stop.x - camera.position.x, stop.z - camera.position.z) < 105;
      const show = projected.z < 1 && Math.abs(projected.x) < 1.05 && Math.abs(projected.y) < 1.05 && !here
        && near && (chart || islands.has(stop.slug));
      label.classList.toggle('is-visible', show);
      if (show) {
        const x = (projected.x * 0.5 + 0.5) * stage.clientWidth;
        const y = (-projected.y * 0.5 + 0.5) * stage.clientHeight;
        label.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0) translate(-50%, ${chart ? '-140%' : '-100%'})`;
      }
    }
  }

  function render(now) {
    frame = 0;
    if (!running) return;
    const dt = Math.min(0.05, (now - previous) / 1000);
    previous = now;
    update(dt);
    if (depth && ocean.uniforms.uHasDepth.value) depth.render(scene, camera, hiddenInDepth);
    renderer.render(scene, camera);
    placeLabels();
    // If the device struggles, trade resolution for smoothness once.
    if (measured < 120 && intro >= 1) {
      measured += 1;
      if (dt > 0.03) slowFrames += 1;
      if (measured === 120 && slowFrames > 50) {
        tier.dpr = Math.min(tier.dpr, 1);
        ocean.uniforms.uHasDepth.value = 0;
        measure();
      }
    }
    if (!still) frame = requestAnimationFrame(render);
  }
  // ?debug exposes a manual clock, for checking frames where requestAnimationFrame is paused.
  if (window.location.search.includes('debug')) {
    window.__voyage = { step(seconds = 2) {
      readScroll();
      for (let t = 0; t < seconds; t += 1 / 30) update(1 / 30);
      if (depth && ocean.uniforms.uHasDepth.value) depth.render(scene, camera, hiddenInDepth);
      renderer.render(scene, camera);
      placeLabels();
      return { current, target, islands: islands.size, calls: renderer.info.render.calls, triangles: renderer.info.render.triangles };
    } };
  }
  function wake() {
    const should = visible && !document.hidden;
    if (should && !running) { running = true; previous = performance.now(); frame = requestAnimationFrame(render); }
    else if (!should && running) { running = false; cancelAnimationFrame(frame); }
  }
  function renderOnce() {
    if (!still) return;
    running = true;
    previous = performance.now() - 16;
    render(performance.now());
    running = false;
  }
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; wake(); }).observe(stage);
  document.addEventListener('visibilitychange', wake);
  if (still) window.addEventListener('scroll', () => requestAnimationFrame(renderOnce), { passive: true });

  measure();
  if (hashIndex > 0) { go(hashIndex, 'auto'); readScroll(); current = target; }
  await Promise.all([firstIslands, boatReady]);
  if (hashIndex > 0) { go(hashIndex, 'auto'); readScroll(); current = target; }
  measure();
  current = target;
  if (still) renderOnce(); else wake();
  root.classList.add('is-ready');
  if (loader) loader.setAttribute('aria-hidden', 'true');
  return { go, renderOnce };
}
