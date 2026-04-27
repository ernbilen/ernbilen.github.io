(function () {
  const canvas = document.getElementById("globe");
  const context = canvas.getContext("2d");
  const tooltip = document.getElementById("tooltip");

  const projection = d3.geoOrthographic();
  const path = d3.geoPath(projection, context);
  const world = topojson.feature(window.WORLD_TOPOLOGY, window.WORLD_TOPOLOGY.objects.countries);
  const borders = topojson.mesh(
    window.WORLD_TOPOLOGY,
    window.WORLD_TOPOLOGY.objects.countries,
    (a, b) => a !== b
  );
  const points = window.UFO_POINTS.points;

  let rotation = [100, -20, 0];
  let currentScale = 1;
  let hoveredPoint = null;
  let drawnPoints = [];
  let autoRotate = true;
  let lastFrame = performance.now();

  function visibleFromCenter(point) {
    const center = [-rotation[0], -rotation[1]];
    return d3.geoDistance([point.lon, point.lat], center) <= Math.PI / 2;
  }

  function resize() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const ratio = window.devicePixelRatio || 1;

    canvas.width = width * ratio;
    canvas.height = height * ratio;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    context.setTransform(ratio, 0, 0, ratio, 0, 0);

    projection
      .translate([width / 2, height / 2])
      .scale(Math.min(width, height) * 0.46 * currentScale)
      .clipAngle(90)
      .precision(0.3)
      .rotate(rotation);

    render();
  }

  function drawSphere(width, height) {
    const cx = width / 2;
    const cy = height / 2;
    const radius = projection.scale() * 1.08;
    const glow = context.createRadialGradient(cx, cy, projection.scale() * 0.2, cx, cy, radius);
    glow.addColorStop(0, "rgba(94, 182, 255, 0.10)");
    glow.addColorStop(0.7, "rgba(94, 182, 255, 0.06)");
    glow.addColorStop(1, "rgba(94, 182, 255, 0)");
    context.fillStyle = glow;
    context.fillRect(0, 0, width, height);

    context.beginPath();
    path({ type: "Sphere" });
    context.fillStyle = "#0b1622";
    context.fill();

    context.beginPath();
    path({ type: "Sphere" });
    context.strokeStyle = "rgba(255, 255, 255, 0.35)";
    context.lineWidth = 1.2;
    context.stroke();
  }

  function drawLand() {
    context.beginPath();
    path(world);
    context.fillStyle = "#223445";
    context.fill();

    context.beginPath();
    path(borders);
    context.strokeStyle = "rgba(255, 255, 255, 0.22)";
    context.lineWidth = 0.6;
    context.stroke();
  }

  function drawDots() {
    drawnPoints = [];

    for (const point of points) {
      if (!visibleFromCenter(point)) continue;

      const projected = projection([point.lon, point.lat]);
      if (!projected) continue;

      const radius = Math.max(1.1, Math.min(5, 0.7 + Math.sqrt(point.count) * 0.14));

      context.beginPath();
      context.arc(projected[0], projected[1], radius, 0, Math.PI * 2);
      context.fillStyle = hoveredPoint === point ? "#ffffff" : "rgba(255, 74, 74, 0.95)";
      context.fill();

      drawnPoints.push({
        point,
        x: projected[0],
        y: projected[1],
        radius: Math.max(5, radius + 3),
      });
    }
  }

  function render() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    context.clearRect(0, 0, width, height);
    drawSphere(width, height);
    drawLand();
    drawDots();
  }

  function setTooltip(point, x, y) {
    if (!point) {
      tooltip.hidden = true;
      return;
    }

    tooltip.hidden = false;
    tooltip.style.left = x + "px";
    tooltip.style.top = y + "px";
    tooltip.textContent = point.city + ", " + point.country + " • " + point.count;
  }

  function pickPoint(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let nextHovered = null;

    for (let i = drawnPoints.length - 1; i >= 0; i -= 1) {
      const item = drawnPoints[i];
      const dx = x - item.x;
      const dy = y - item.y;
      if (dx * dx + dy * dy <= item.radius * item.radius) {
        nextHovered = item.point;
        break;
      }
    }

    hoveredPoint = nextHovered;
    setTooltip(nextHovered, x, y);
    render();
  }

  function animate(now) {
    const dt = now - lastFrame;
    lastFrame = now;

    if (autoRotate) {
      rotation = [rotation[0] + dt * 0.0045, rotation[1], 0];
      projection.rotate(rotation);
      render();
    }

    requestAnimationFrame(animate);
  }

  function setupDrag() {
    let start;
    let startRotation;

    d3.select(canvas).call(
      d3
        .drag()
        .on("start", (event) => {
          autoRotate = false;
          start = [event.x, event.y];
          startRotation = rotation.slice();
        })
        .on("drag", (event) => {
          const dx = event.x - start[0];
          const dy = event.y - start[1];
          rotation = [
            startRotation[0] + dx * 0.22,
            Math.max(-85, Math.min(85, startRotation[1] - dy * 0.22)),
            0,
          ];
          projection.rotate(rotation);
          render();
        })
        .on("end", () => {
          autoRotate = true;
        })
    );
  }

  function setupZoom() {
    d3.select(canvas).call(
      d3.zoom().scaleExtent([0.75, 4]).on("zoom", (event) => {
        currentScale = event.transform.k;
        resize();
      })
    );
  }

  canvas.addEventListener("mousemove", pickPoint);
  canvas.addEventListener("mouseleave", function () {
    hoveredPoint = null;
    setTooltip(null);
    render();
  });

  window.addEventListener("resize", resize);

  setupDrag();
  setupZoom();
  resize();
  requestAnimationFrame(animate);
})();
