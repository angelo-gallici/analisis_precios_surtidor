let mapa;
let capaEstaciones;
let capaCalor;
let geojsonDatos;

async function cargarDatos() {
  const resp = await fetch("data/estaciones.geojson");
  geojsonDatos = await resp.json();
  inicializarMapa();
}

function inicializarMapa() {
  mapa = L.map("map").setView([-38.5, -60], 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
  }).addTo(mapa);

  actualizarFiltro();
  actualizarVista();
}

function actualizarFiltro() {
  const filtro = document.getElementById("filtro");
  const productos = new Set(
    geojsonDatos.features.map(f => f.properties.producto)
  );

  productos.forEach(prod => {
    const opt = document.createElement("option");
    opt.value = prod;
    opt.innerText = prod;
    filtro.appendChild(opt);
  });

  filtro.addEventListener("change", actualizarVista);
}

function actualizarVista() {
  const filtro = document.getElementById("filtro");
  const seleccionados = Array.from(filtro.selectedOptions).map(o => o.value);

  if (capaEstaciones) capaEstaciones.remove();
  if (capaCalor) capaCalor.remove();

  const puntosFiltrados = geojsonDatos.features.filter(f =>
    seleccionados.length === 0 || seleccionados.includes(f.properties.producto)
  );

  // Marcadores
  capaEstaciones = L.geoJSON(puntosFiltrados, {
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      layer.bindPopup(`
        <strong>${p.bandera}</strong><br>
        ⛽ ${p.producto}<br>
        💲 $${p.precio}<br>
        📅 ${p.fecha}<br>
        📍 ${p.direccion}
      `);
    },
  }).addTo(mapa);
/*
  // Capa de calor
  const puntos = puntosFiltrados.map(f => [
    f.geometry.coordinates[1],
    f.geometry.coordinates[0],
    parseFloat(f.properties.precio),
  ]);

  capaCalor = L.heatLayer(puntos, {
    radius: 25,
    blur: 15,
    maxZoom: 10,
    gradient: {
      0.3: "blue",
      0.6: "lime",
      0.9: "red"
    },
  }).addTo(mapa);
*/
}

cargarDatos();
