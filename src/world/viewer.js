// Case-study pages: one island you can turn by hand, with numbered points of interest.
import * as THREE from 'three';
import { SUN, WATER_Y, createDepthPass, createRenderer, damp, loadIsland, updateMovers } from './core.js';
import { createOcean } from './ocean.js';

export async function startViewer(root, tier, options = {}) {
  const asset = JSON.parse(root.querySelector('[data-island-data]').textContent);
  const canvas = root.querySelector('canvas');
  const frameElement = root.querySelector('.island-frame') || root;
  const markers = [...root.querySelectorAll('[data-marker]')];
  const notes = [...root.querySelectorAll('[data-note]')];
  const reset = root.querySelector('[data-reset]');
  const still = Boolean(options.still);

  const renderer = createRenderer(canvas, tier, true);
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 1, 400);
  const radius = asset.r || 5;
  const ocean = createOcean({ edge: radius + 8.5 });
  ocean.setIslands([{ x: 0, z: 0, r: radius }]);
  ocean.uniforms.uFogNear.value = 9000;
  ocean.uniforms.uFogFar.value = 9999;
  ocean.uniforms.uSun.value.copy(SUN);
  scene.add(ocean.mesh);
  const depth = tier.depth ? createDepthPass(renderer) : null;
  if (depth) { ocean.uniforms.tDepth.value = depth.texture; ocean.uniforms.uHasDepth.value = 1; }

  const island = await loadIsland(asset, tier);
  scene.add(island.root);
  const height = Math.min(5.5, island.box.max.y);
  const home = { azimuth: -0.54, polar: 1.12, distance: 25 * (radius / 5) ** 0.6, target: new THREE.Vector3(0, height * 0.3, 0.3) };
  const state = { azimuth: home.azimuth, polar: home.polar, distance: home.distance, target: home.target.clone() };
  const goal = { azimuth: home.azimuth, polar: home.polar, distance: home.distance, target: home.target.clone() };
  const size = new THREE.Vector2();
  let fit = 1;
  let selected = -1;
  let dragging = null;
  let idle = 0;
  let visible = true;
  let running = false;
  let frame = 0;
  let time = 0;
  let previous = performance.now();

  function resize() {
    const width = frameElement.clientWidth;
    const heightPx = frameElement.clientHeight;
    if (!width || !heightPx) return;
    renderer.setPixelRatio(tier.dpr);
    renderer.setSize(width, heightPx, false);
    renderer.getDrawingBufferSize(size);
    camera.aspect = width / heightPx;
    camera.updateProjectionMatrix();
    fit = camera.aspect < 1 ? 1.05 / camera.aspect : Math.max(0.92, 1.25 / camera.aspect ** 0.35);
    ocean.uniforms.uResolution.value.copy(size);
    ocean.uniforms.uNear.value = camera.near;
    ocean.uniforms.uFar.value = camera.far;
    if (depth) depth.resize();
    if (still) renderOnce();
  }

  function select(index) {
    selected = index;
    notes.forEach((note) => note.classList.toggle('is-active', Number(note.dataset.note) === index));
    markers.forEach((marker) => marker.setAttribute('aria-pressed', String(Number(marker.dataset.marker) === index)));
    const spot = island.hotspots.find((item) => item.index === index);
    if (!spot) {
      Object.assign(goal, { azimuth: home.azimuth, polar: home.polar, distance: home.distance });
      goal.target.copy(home.target);
      return;
    }
    const point = spot.node.getWorldPosition(new THREE.Vector3());
    // Move in and lean toward the object's side, but stay in front where the model is lit and detailed.
    goal.azimuth = home.azimuth + THREE.MathUtils.clamp(point.x / radius, -1, 1) * 0.38;
    goal.polar = 1.08;
    goal.distance = home.distance * 0.6;
    goal.target.set(point.x * 0.85, Math.max(0.5, point.y * 0.55), point.z * 0.85);
    if (still) renderOnce();
  }
  for (const marker of markers) {
    marker.addEventListener('click', () => select(selected === Number(marker.dataset.marker) ? -1 : Number(marker.dataset.marker)));
  }
  for (const note of notes) {
    note.addEventListener('click', () => select(Number(note.dataset.note)));
    note.addEventListener('focusin', () => select(Number(note.dataset.note)));
  }
  reset?.addEventListener('click', () => select(-1));

  canvas.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    dragging = { id: event.pointerId, x: event.clientX, y: event.clientY, azimuth: goal.azimuth, polar: goal.polar, mouse: event.pointerType === 'mouse' };
    canvas.setPointerCapture(event.pointerId);
    root.classList.add('is-dragging');
  });
  canvas.addEventListener('pointermove', (event) => {
    if (!dragging || event.pointerId !== dragging.id) return;
    goal.azimuth = dragging.azimuth - (event.clientX - dragging.x) * 0.0062;
    if (dragging.mouse) goal.polar = THREE.MathUtils.clamp(dragging.polar - (event.clientY - dragging.y) * 0.004, 0.62, 1.38);
    idle = 0;
    if (still) renderOnce();
  });
  const release = (event) => {
    if (!dragging || event.pointerId !== dragging.id) return;
    dragging = null;
    root.classList.remove('is-dragging');
    root.classList.add('was-turned');
  };
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);
  canvas.addEventListener('keydown', (event) => {
    const step = { ArrowLeft: 0.2, ArrowRight: -0.2 }[event.key];
    if (!step) return;
    event.preventDefault();
    goal.azimuth += step;
    idle = 0;
    if (still) renderOnce();
  });

  const offset = new THREE.Vector3();
  const projected = new THREE.Vector3();
  function update(dt) {
    time += still ? 0 : dt;
    idle += dt;
    const sway = !still && selected < 0 && !dragging && idle > 2.5 ? Math.sin((idle - 2.5) * 0.22) * 0.2 : 0;
    const k = still ? 60 : 4.2;
    state.azimuth = damp(state.azimuth, goal.azimuth + sway, k, dt);
    state.polar = damp(state.polar, goal.polar, k, dt);
    state.distance = damp(state.distance, goal.distance * fit, k, dt);
    state.target.lerp(goal.target, 1 - Math.exp(-k * dt));
    offset.setFromSphericalCoords(state.distance, state.polar, state.azimuth);
    camera.position.copy(state.target).add(offset);
    camera.lookAt(state.target);
    ocean.uniforms.uTime.value = time;
    updateMovers(island.movers, time, still);
  }
  function placeMarkers() {
    camera.updateMatrixWorld();
    const width = frameElement.clientWidth;
    const heightPx = frameElement.clientHeight;
    for (const marker of markers) {
      const spot = island.hotspots.find((item) => item.index === Number(marker.dataset.marker));
      if (!spot) { marker.hidden = true; continue; }
      spot.node.getWorldPosition(projected).project(camera);
      marker.style.transform = `translate3d(${((projected.x * 0.5 + 0.5) * width).toFixed(1)}px, ${((-projected.y * 0.5 + 0.5) * heightPx).toFixed(1)}px, 0) translate(-50%, -50%)`;
    }
  }
  function draw() {
    if (depth) depth.render(scene, camera, [ocean.mesh]);
    renderer.render(scene, camera);
    placeMarkers();
  }
  function render(now) {
    frame = 0;
    if (!running) return;
    const dt = Math.min(0.05, (now - previous) / 1000);
    previous = now;
    update(dt);
    draw();
    frame = requestAnimationFrame(render);
  }
  function renderOnce() {
    update(1);
    draw();
  }
  if (window.location.search.includes('debug')) {
    window.__viewer = { step(seconds = 2) { for (let t = 0; t < seconds; t += 1 / 30) update(1 / 30); draw(); return { azimuth: state.azimuth, selected }; }, select };
  }
  function wake() {
    if (still) return;
    const should = visible && !document.hidden;
    if (should && !running) { running = true; previous = performance.now(); frame = requestAnimationFrame(render); }
    else if (!should && running) { running = false; cancelAnimationFrame(frame); }
  }
  new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; wake(); }, { rootMargin: '120px' }).observe(frameElement);
  document.addEventListener('visibilitychange', wake);
  new ResizeObserver(resize).observe(frameElement);
  resize();
  state.distance = goal.distance * fit * (still ? 1 : 1.25);
  if (still) renderOnce(); else wake();
  root.classList.add('is-ready');
  markers.forEach((marker) => { marker.hidden = false; });
}
