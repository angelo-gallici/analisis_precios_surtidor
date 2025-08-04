let mapa;
let capaEstaciones;
let geojsonDatos;
let ubicacionUsuario = null;
let circuloRadio = null;
let rutaControl = null;
let capaEstacionesFiltradas = null;

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
	construirSlider();

	document
		.getElementById("btnBuscar")
		.addEventListener("click", buscarMejorEstacion);
	document
		.getElementById("btnLimpiar")
		.addEventListener("click", limpiarFiltros);
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

function construirSlider() {
	const slider = document.getElementById("radioSlider");
	const label = document.getElementById("radioValor");
	slider.addEventListener("input", () => {
		label.innerText = `${slider.value} km`;
	});
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
			ubicacionUsuario = [lat, lon];
			mapa.setView(ubicacionUsuario, 12);

			L.marker(ubicacionUsuario, {
				icon: L.icon({
					iconUrl: "https://cdn-icons-png.flaticon.com/512/64/64113.png",
					iconSize: [25, 25],
					iconAnchor: [12, 12],
				}),
			})
				.addTo(mapa)
				.bindPopup("📍 Tu ubicación")
				.openPopup();
		},
		(err) => {
			console.warn("No se pudo obtener la ubicación:", err.message);
		}
	);
}

function actualizarVista() {
	const seleccionados = obtenerSeleccionados();
	if (capaEstaciones) mapa.removeLayer(capaEstaciones);
	if (seleccionados.length === 0) return;

	const features = construirFeaturesFiltradas(seleccionados);
	capaEstaciones = L.geoJSON(features, {
		pointToLayer: (feature, latlng) => crearIcono(feature),
		onEachFeature: crearPopup,
	}).addTo(mapa);
}

function obtenerSeleccionados() {
	return Array.from(
		document.querySelectorAll("#filtro-productos input:checked")
	).map((e) => e.value);
}

function construirFeaturesFiltradas(productos, limiteDistanciaKm = null) {
	const estacionesMap = new Map();

	geojsonDatos.features.forEach((f) => {
		const prod = f.properties.producto;
		const [lon, lat] = f.geometry.coordinates;
		const distancia = ubicacionUsuario
			? mapa.distance(ubicacionUsuario, [lat, lon])
			: 0;

		if (
			productos.includes(prod) &&
			(limiteDistanciaKm == null || distancia <= limiteDistanciaKm * 1000)
		) {
			const key = `${f.properties.bandera.toUpperCase()}|${lat}|${lon}|${
				f.properties.direccion
			}`;
			if (!estacionesMap.has(key)) {
				estacionesMap.set(key, {
					bandera: f.properties.bandera.toUpperCase(),
					latlng: [lat, lon],
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

	return Array.from(estacionesMap.values()).map((est) => ({
		type: "Feature",
		geometry: { type: "Point", coordinates: [est.latlng[1], est.latlng[0]] },
		properties: est,
	}));
}

function crearIcono(feature) {
	const bandera = feature.properties.bandera.toLowerCase();
	const iconos = {
		shell: "icons/shell.png",
		ypf: "icons/ypf.png",
		axion: "icons/axion.png",
		puma: "icons/puma.png",
		voy: "icons/voy.png",
		dapsa: "icons/dapsa.png",
		gulf: "icons/gulf.png",
		refinor: "icons/refinor.png",
	};
	const iconUrl = iconos[bandera] || "icons/estacion.png";

	return L.marker(
		[feature.geometry.coordinates[1], feature.geometry.coordinates[0]],
		{
			icon: L.icon({
				iconUrl: iconUrl,
				iconSize: [28, 28],
				iconAnchor: [14, 28],
				popupAnchor: [0, -28],
			}),
		}
	);
}

function crearPopup(feature, layer) {
	const p = feature.properties;
	let popup = `<div style="font-size:14px; line-height:1.4;"><strong style="font-size:16px; color:#007BFF;">${p.bandera.toUpperCase()}</strong><br><em>${
		p.direccion
	}</em><br><br>`;
	p.combustibles.forEach((c) => {
		const nombre = nombresBonitos[c.producto.toLowerCase()] || c.producto;
		popup += `⛽ ${nombre}: <span style="color:green;">$${c.precio}</span><br>`;
	});
	if (p.combustibles.length > 0 && p.combustibles[0].fecha) {
		popup += `<br>📅 <small>${p.combustibles[0].fecha}</small>`;
	}
	popup += `</div>`;
	layer.bindPopup(popup);
}

function buscarMejorEstacion() {
	const productos = obtenerSeleccionados();
	if (!ubicacionUsuario || productos.length === 0) return;

	const radioKm = parseFloat(document.getElementById("radioSlider").value);

	if (circuloRadio) mapa.removeLayer(circuloRadio);
	circuloRadio = L.circle(ubicacionUsuario, {
		radius: radioKm * 1000,
		color: "#3388ff",
		fillColor: "#3388ff",
		fillOpacity: 0.2,
	}).addTo(mapa);

	// Obtener solo estaciones dentro del radio
	const estaciones = construirFeaturesFiltradas(productos, radioKm);

	// Limpiar capas previas
	if (capaEstaciones) {
		mapa.removeLayer(capaEstaciones);
		capaEstaciones = null;
	}
	if (capaEstacionesFiltradas) {
		mapa.removeLayer(capaEstacionesFiltradas);
	}
	if (rutaControl) mapa.removeControl(rutaControl);

	// Buscar estación con menor precio entre seleccionados (supongo que quieres el mínimo precio de algún combustible)
	let mejorEstacion = null;
	let mejorPrecio = Infinity;

	estaciones.forEach((est) => {
		est.properties.combustibles.forEach((c) => {
			if (productos.includes(c.producto) && c.precio < mejorPrecio) {
				mejorPrecio = c.precio;
				mejorEstacion = est;
			}
		});
	});

	// Mostrar solo estaciones dentro del radio
	capaEstacionesFiltradas = L.geoJSON(estaciones, {
		pointToLayer: (feature, latlng) => crearIcono(feature),
		onEachFeature: crearPopup,
	}).addTo(mapa);

	if (mejorEstacion) {
		const [lon, lat] = mejorEstacion.geometry.coordinates;

		// Popup informativo en mejor estación
		const distancia = (
			mapa.distance(ubicacionUsuario, [lat, lon]) / 1000
		).toFixed(1);
		const props = mejorEstacion.properties;
		let popupHTML = `
      <div style="font-size:14px; line-height:1.4;">
      <strong style="font-size:16px; color:#007BFF;">${props.bandera.toUpperCase()}</strong><br>
      <em>${props.direccion}</em><br>
      📏 Distancia: <strong>${distancia} km</strong><br><br>`;
		props.combustibles.forEach((c) => {
			const nombre = nombresBonitos[c.producto.toLowerCase()] || c.producto;
			popupHTML += `⛽ ${nombre}: <span style="color:green;">$${c.precio}</span><br>`;
		});
		if (props.combustibles.length > 0 && props.combustibles[0].fecha) {
			popupHTML += `<br>📅 <small>${props.combustibles[0].fecha}</small>`;
		}
		popupHTML += `</div>`;

		L.popup({ closeButton: true })
			.setLatLng([lat, lon])
			.setContent(popupHTML)
			.openOn(mapa);

		// Trazar ruta
		rutaControl = L.Routing.control({
			language: "es",
			waypoints: [L.latLng(...ubicacionUsuario), L.latLng(lat, lon)],
			routeWhileDragging: false,
			addWaypoints: false,
			showAlternatives: false,
			createMarker: () => null,
			lineOptions: {
				styles: [{ color: "green", weight: 5 }],
			},
		}).addTo(mapa);
	}
}

function limpiarFiltros() {
	if (capaEstaciones) mapa.removeLayer(capaEstaciones);
	if (capaEstacionesFiltradas) mapa.removeLayer(capaEstacionesFiltradas);
	if (rutaControl) mapa.removeControl(rutaControl);
	if (circuloRadio) mapa.removeLayer(circuloRadio);

	document
		.querySelectorAll("#filtro-productos input")
		.forEach((c) => (c.checked = false));
	mapa.setView([-38.5, -60], 5);
	mapa.closePopup();
	actualizarVista();
}

cargarDatos();
