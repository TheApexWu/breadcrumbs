use bevy::prelude::*;
use bevy::mesh::PrimitiveTopology;
use serde::Deserialize;
use std::collections::HashMap;
use std::path::Path;

// --- Data schema ---

#[derive(Deserialize)]
pub struct RawBuilding {
    pub p: Vec<[f64; 2]>,
    pub h: f64,
    #[serde(default)]
    pub y: u16,
    pub b: String,
}

// --- ECS components ---

#[derive(Component)]
pub struct BuildingData {
    pub bin: String,
    pub year: u16,
    pub centroid: Vec3,  // world-space center (x, h/2, z)
    pub height: f32,
}

#[derive(Resource)]
pub struct YearFilter {
    pub current_year: u16,
}

impl Default for YearFilter {
    fn default() -> Self {
        Self { current_year: 2026 }
    }
}

// --- Coordinate conversion ---

const CENTER_LAT: f64 = 40.7831;
const CENTER_LNG: f64 = -73.9712;
const METERS_PER_DEG_LAT: f64 = 111_320.0;

fn lng_lat_to_local(lng: f64, lat: f64) -> (f32, f32) {
    let cos_lat = (CENTER_LAT.to_radians()).cos();
    let x = ((lng - CENTER_LNG) * cos_lat * METERS_PER_DEG_LAT) as f32;
    let z = -((lat - CENTER_LAT) * METERS_PER_DEG_LAT) as f32;
    (x, z)
}

// --- Era coloring ---

pub fn era_color(year: u16) -> Color {
    match year {
        0 => Color::srgb_u8(0x40, 0x40, 0x40),
        1..=1799 => Color::srgb_u8(0x8a, 0x8a, 0x7a),
        1800..=1849 => Color::srgb_u8(0xb8, 0x73, 0x33),
        1850..=1899 => Color::srgb_u8(0x8b, 0x69, 0x14),
        1900..=1944 => Color::srgb_u8(0xc4, 0xa8, 0x7c),
        1945..=1969 => Color::srgb_u8(0xa0, 0xa0, 0xa0),
        1970..=1999 => Color::srgb_u8(0x5b, 0x7f, 0xa5),
        _ => Color::srgb_u8(0x4d, 0xb8, 0xa0),
    }
}

fn era_index(year: u16) -> usize {
    match year {
        0 => 0,
        1..=1799 => 1,
        1800..=1849 => 2,
        1850..=1899 => 3,
        1900..=1944 => 4,
        1945..=1969 => 5,
        1970..=1999 => 6,
        _ => 7,
    }
}

// --- Era metadata ---

pub const ERA_LABELS: &[&str] = &[
    "UNKNOWN",
    "COLONIAL ERA",
    "ANTEBELLUM",
    "GILDED AGE",
    "GOLDEN AGE / ART DECO",
    "BRUTALISM / MIDCENTURY",
    "POSTMODERN",
    "GLASS TOWER ERA",
];

pub const ERA_MAX_YEARS: &[u16] = &[0, 1799, 1849, 1899, 1944, 1969, 1999, 9999];

pub fn era_label(year: u16) -> &'static str {
    ERA_LABELS[era_index(year)]
}

// --- Guided tour stations ---

pub struct TourStation {
    pub name: &'static str,
    pub year: u16,
    pub lat: f64,
    pub lng: f64,
    pub distance: f32,
    pub pitch: f32,
    pub yaw: f32,
}

pub const TOUR_STATIONS: &[TourStation] = &[
    TourStation { name: "Colonial",    year: 1760, lat: 40.7033, lng: -74.0170, distance: 800.0,  pitch: 0.78, yaw: -1.57 },
    TourStation { name: "Antebellum",  year: 1840, lat: 40.7128, lng: -74.0060, distance: 900.0,  pitch: 0.84, yaw: -1.57 },
    TourStation { name: "Gilded Age",  year: 1885, lat: 40.7155, lng: -73.9880, distance: 850.0,  pitch: 0.87, yaw: -1.57 },
    TourStation { name: "Golden Age",  year: 1925, lat: 40.7484, lng: -73.9856, distance: 1200.0, pitch: 0.96, yaw: -1.57 },
    TourStation { name: "Art Deco",    year: 1938, lat: 40.7484, lng: -73.9857, distance: 900.0,  pitch: 1.05, yaw: -1.57 },
    TourStation { name: "Midcentury",  year: 1960, lat: 40.7505, lng: -73.9935, distance: 850.0,  pitch: 0.87, yaw: -1.57 },
    TourStation { name: "Bronx 1970s", year: 1975, lat: 40.827,  lng: -73.898,  distance: 2500.0, pitch: 0.87, yaw: -1.57 },
    TourStation { name: "Postmodern",  year: 1987, lat: 40.7580, lng: -73.9855, distance: 1100.0, pitch: 0.87, yaw: -1.57 },
    TourStation { name: "Glass Tower", year: 2020, lat: 40.7536, lng: -74.0003, distance: 1000.0, pitch: 0.96, yaw: -1.57 },
];

// --- Marquee data ---

#[derive(Deserialize, Clone)]
pub struct MarqueeEntry {
    pub title: String,
    pub year: u16,
    pub body: String,
    #[serde(default)]
    pub event_id: String,
    #[serde(default)]
    pub niche_tags: Vec<String>,
    #[serde(default)]
    pub distance_m: f64,
}

#[derive(Deserialize)]
struct MarqueeFile {
    marquee: HashMap<String, MarqueeEntry>,
}

#[derive(Resource, Default)]
pub struct MarqueeData {
    pub entries: HashMap<String, MarqueeEntry>,
}

// --- Mesh generation ---

fn build_extruded_mesh(polygon: &[[f64; 2]], height: f64) -> Option<Mesh> {
    let n = polygon.len();
    if n < 3 {
        return None;
    }

    let local_pts: Vec<(f32, f32)> = polygon
        .iter()
        .map(|&[lng, lat]| lng_lat_to_local(lng, lat))
        .collect();

    let mut coords_2d: Vec<f64> = Vec::with_capacity(n * 2);
    for &(x, z) in &local_pts {
        coords_2d.push(x as f64);
        coords_2d.push(z as f64);
    }

    let tri_indices = match earcutr::earcut(&coords_2d, &[], 2) {
        Ok(indices) => indices,
        Err(_) => return None,
    };

    let h = height as f32;
    if h < 0.1 {
        return None;
    }

    let wall_vert_count = n * 4;
    let total_verts = n * 2 + wall_vert_count;
    let mut positions: Vec<[f32; 3]> = Vec::with_capacity(total_verts);
    let mut normals: Vec<[f32; 3]> = Vec::with_capacity(total_verts);

    // Top cap
    for &(x, z) in &local_pts {
        positions.push([x, h, z]);
        normals.push([0.0, 1.0, 0.0]);
    }

    // Bottom cap
    for &(x, z) in &local_pts {
        positions.push([x, 0.0, z]);
        normals.push([0.0, -1.0, 0.0]);
    }

    // Walls
    for i in 0..n {
        let j = (i + 1) % n;
        let (x0, z0) = local_pts[i];
        let (x1, z1) = local_pts[j];

        let dx = x1 - x0;
        let dz = z1 - z0;
        let len = (dx * dx + dz * dz).sqrt().max(1e-6);
        let nx = dz / len;
        let nz = -dx / len;
        let normal = [nx, 0.0, nz];

        positions.push([x0, h, z0]);
        normals.push(normal);
        positions.push([x1, h, z1]);
        normals.push(normal);
        positions.push([x1, 0.0, z1]);
        normals.push(normal);
        positions.push([x0, 0.0, z0]);
        normals.push(normal);
    }

    let mut indices: Vec<u32> = Vec::new();

    // Top cap triangles (reverse winding so normals face up)
    for tri in tri_indices.chunks(3) {
        indices.push(tri[0] as u32);
        indices.push(tri[2] as u32);
        indices.push(tri[1] as u32);
    }

    // Bottom cap (original winding, normals face down)
    let bottom_offset = n as u32;
    for tri in tri_indices.chunks(3) {
        indices.push(bottom_offset + tri[0] as u32);
        indices.push(bottom_offset + tri[1] as u32);
        indices.push(bottom_offset + tri[2] as u32);
    }

    // Wall triangles
    let wall_offset = (n * 2) as u32;
    for i in 0..n {
        let base = wall_offset + (i as u32) * 4;
        indices.push(base);
        indices.push(base + 1);
        indices.push(base + 2);
        indices.push(base);
        indices.push(base + 2);
        indices.push(base + 3);
    }

    let mut mesh = Mesh::new(PrimitiveTopology::TriangleList, default());
    mesh.insert_attribute(Mesh::ATTRIBUTE_POSITION, positions);
    mesh.insert_attribute(Mesh::ATTRIBUTE_NORMAL, normals);
    mesh.insert_indices(bevy::mesh::Indices::U32(indices));
    Some(mesh)
}

// --- Plugin ---

pub struct BuildingPlugin;

impl Plugin for BuildingPlugin {
    fn build(&self, app: &mut App) {
        app.init_resource::<YearFilter>()
            .init_resource::<MarqueeData>()
            .init_resource::<BuildingStats>()
            .add_systems(Startup, (load_buildings, load_marquee))
            .add_systems(Update, year_filter_system);
    }
}

#[derive(Resource, Default)]
pub struct BuildingStats {
    pub total: u32,
    pub visible: u32,
}

fn load_marquee(mut marquee: ResMut<MarqueeData>) {
    let candidates = [
        Path::new("cultural-content/marquee-bronx.json").to_path_buf(),
        Path::new("../cultural-content/marquee-bronx.json").to_path_buf(),
    ];
    let path = candidates.iter().find(|p| p.exists());
    if let Some(path) = path {
        match std::fs::read_to_string(path) {
            Ok(data) => {
                match serde_json::from_str::<MarqueeFile>(&data) {
                    Ok(file) => {
                        info!("Loaded {} marquee entries", file.marquee.len());
                        marquee.entries = file.marquee;
                    }
                    Err(e) => error!("Failed to parse marquee: {}", e),
                }
            }
            Err(e) => error!("Failed to read marquee: {}", e),
        }
    } else {
        warn!("Marquee file not found");
    }
}

fn load_buildings(
    mut commands: Commands,
    mut meshes: ResMut<Assets<Mesh>>,
    mut materials: ResMut<Assets<StandardMaterial>>,
) {
    let era_years: &[u16] = &[0, 1700, 1800, 1850, 1900, 1945, 1970, 2000];
    let era_material_handles: Vec<Handle<StandardMaterial>> = era_years
        .iter()
        .map(|&y| {
            materials.add(StandardMaterial {
                base_color: era_color(y),
                unlit: false,
                perceptual_roughness: 0.95,
                metallic: 0.0,
                alpha_mode: AlphaMode::Opaque,
                ..default()
            })
        })
        .collect();

    // Data lives at repo root, one level up from renderer-rust-v2/
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));
    let data_dir_candidates = [
        Path::new("data").to_path_buf(),
        Path::new("../data").to_path_buf(),
    ];
    let data_dir = data_dir_candidates
        .iter()
        .find(|d| d.exists())
        .cloned()
        .unwrap_or_else(|| Path::new("../data").to_path_buf());
    info!("Using data directory: {}", data_dir.display());
    let files = [
        "manhattan_compact.json",
        "bronx_compact.json",
        "brooklyn_compact.json",
        "queens_compact.json",
        "staten_compact.json",
    ];

    let mut total = 0u32;
    let mut skipped = 0u32;

    for filename in &files {
        let path = data_dir.join(filename);
        let data = match std::fs::read_to_string(&path) {
            Ok(d) => d,
            Err(e) => {
                error!("Failed to read {}: {}", path.display(), e);
                continue;
            }
        };

        let buildings: Vec<RawBuilding> = match serde_json::from_str(&data) {
            Ok(b) => b,
            Err(e) => {
                error!("Failed to parse {}: {}", path.display(), e);
                continue;
            }
        };

        info!("Loaded {} buildings from {}", buildings.len(), filename);

        for raw in &buildings {
            let mesh = match build_extruded_mesh(&raw.p, raw.h) {
                Some(m) => m,
                None => {
                    skipped += 1;
                    continue;
                }
            };

            let mat_idx = era_index(raw.y);
            let mat = era_material_handles[mat_idx].clone();

            // Compute centroid from polygon points
            let n = raw.p.len() as f64;
            let cx: f64 = raw.p.iter().map(|p| p[0]).sum::<f64>() / n;
            let cy: f64 = raw.p.iter().map(|p| p[1]).sum::<f64>() / n;
            let (lx, lz) = lng_lat_to_local(cx, cy);
            let h = raw.h as f32;

            commands.spawn((
                Mesh3d(meshes.add(mesh)),
                MeshMaterial3d(mat),
                BuildingData {
                    bin: raw.b.clone(),
                    year: raw.y,
                    centroid: Vec3::new(lx, h * 0.5, lz),
                    height: h,
                },
            ));

            total += 1;
        }
    }

    info!(
        "Spawned {} building entities ({} skipped)",
        total, skipped
    );
}

fn year_filter_system(
    year_filter: Res<YearFilter>,
    mut stats: ResMut<BuildingStats>,
    mut query: Query<(&BuildingData, &mut Visibility)>,
) {
    if !year_filter.is_changed() {
        return;
    }

    let mut visible = 0u32;
    let mut total = 0u32;
    for (data, mut vis) in &mut query {
        total += 1;
        let show = data.year == 0 || data.year <= year_filter.current_year;
        *vis = if show {
            visible += 1;
            Visibility::Inherited
        } else {
            Visibility::Hidden
        };
    }
    stats.total = total;
    stats.visible = visible;
}
