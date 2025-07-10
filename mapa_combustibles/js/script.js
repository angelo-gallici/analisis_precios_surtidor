let mapa;
let capaEstaciones;
let geojsonDatos;

// Diccionario de nombres bonitos
const nombresBonitos = {
	gnc: "GNC",
	"gas oil grado 2": "Gasoil Super",
	"gas oil grado 3": "Gasoil Premium",
	"nafta super entre 92 y 95 ron": "Nafta Super",
	"nafta premium de mas de 95 ron": "Nafta Premium",
};

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

	obtenerUbicacion();
	construirFiltro();
}

function construirFiltro() {
	const productos = new Set(
		geojsonDatos.features.map((f) => f.properties.producto)
	);

	const filtroDiv = document.getElementById("filtro-productos");

	productos.forEach((prod) => {
		const label = document.createElement("label");
		label.innerHTML = `
      <input type="checkbox" value="${prod}"> ${
			nombresBonitos[prod.toLowerCase()] || prod
		}
    `;
		filtroDiv.appendChild(label);
	});

	filtroDiv.addEventListener("change", actualizarVista);
}

function actualizarVista() {
	const seleccionados = Array.from(
		document.querySelectorAll("#filtro-productos input:checked")
	).map((e) => e.value);

	if (capaEstaciones) {
		mapa.removeLayer(capaEstaciones);
	}

	if (seleccionados.length === 0) return;

	const estacionesMap = new Map();

	geojsonDatos.features.forEach((f) => {
		const prod = f.properties.producto;
		if (seleccionados.includes(prod)) {
			const key = `${f.properties.bandera.toUpperCase()}|${
				f.geometry.coordinates[1]
			}|${f.geometry.coordinates[0]}|${f.properties.direccion}`;
			if (!estacionesMap.has(key)) {
				estacionesMap.set(key, {
					bandera: f.properties.bandera.toUpperCase(),
					latlng: [f.geometry.coordinates[1], f.geometry.coordinates[0]],
					direccion: f.properties.direccion,
					combustibles: [],
				});
			}
			estacionesMap.get(key).combustibles.push({
				producto: prod,
				precio: f.properties.precio,
				fecha: f.properties.fecha ? f.properties.fecha.split(" ")[0] : "",
			});
		}
	});

	const estacionesFeatures = Array.from(estacionesMap.values()).map((est) => ({
		type: "Feature",
		geometry: {
			type: "Point",
			coordinates: [est.latlng[1], est.latlng[0]],
		},
		properties: est,
	}));

	capaEstaciones = L.geoJSON(estacionesFeatures, {
		pointToLayer: (feature, latlng) => {
			const bandera = feature.properties.bandera.toLowerCase();

			const iconos = {
				shell: "icons/shell.png",
				ypf: "icons/ypf.png",
				axion: "icons/axion.png",
				puma: "icons/puma.png",
				voy: "icons/voy.png",
				dapsa: "icons/dapsa.png",
				gulf: "icons/gulf.png",
			};

			// Si no existe un ícono para la bandera, usa el ícono genérico
			const iconUrl = iconos[bandera] || "icons/estacion.png";

			return L.marker(latlng, {
				icon: L.icon({
					iconUrl: iconUrl,
					iconSize: [28, 28], // 👈 cuadrado y uniforme
					iconAnchor: [14, 28], // 👈 bien centrado
					popupAnchor: [0, -28], // 👈 para que el popup salga justo encima del ícono
				}),
			});
		},

		onEachFeature: (feature, layer) => {
			const p = feature.properties;
			let popup = `<strong>${p.bandera}</strong><br><em>${p.direccion}</em><br><br>`;
			p.combustibles.forEach((c) => {
				const nombre = nombresBonitos[c.producto.toLowerCase()] || c.producto;
				popup += `⛽ ${nombre}: <span style="color:green;">$${c.precio}</span><br>`;
			});
			if (p.combustibles.length > 0 && p.combustibles[0].fecha) {
				popup += `<br>📅 ${p.combustibles[0].fecha}`;
			}
			layer.bindPopup(popup);
		},
	}).addTo(mapa);
}

function obtenerUbicacion() {
	if (!navigator.geolocation) {
		alert("Tu navegador no soporta geolocalización.");
		return;
	}

	navigator.geolocation.getCurrentPosition(
		(pos) => {
			const lat = pos.coords.latitude;
			const lon = pos.coords.longitude;
			console.log(`📍 Ubicación detectada: ${lat}, ${lon}`);
			mapa.setView([lat, lon], 12);

			L.marker([lat, lon], {
				icon: L.icon({
					iconUrl: "https://cdn-icons-png.flaticon.com/512/64/64113.png",
					iconSize: [25, 25],
					iconAnchor: [12, 12],
				}),
			})
				.addTo(mapa)
				.bindPopup("📍 Tu ubicación");
		},
		(err) => {
			console.warn("No se pudo obtener la ubicación:", err.message);
		}
	);
}

cargarDatos();
