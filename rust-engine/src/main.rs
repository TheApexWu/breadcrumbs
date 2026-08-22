mod biography;
mod building;

use bevy::prelude::*;
use bevy::input::mouse::{AccumulatedMouseMotion, AccumulatedMouseScroll};
use building::{YearFilter, BuildingStats, TOUR_STATIONS, ERA_LABELS, era_color, era_label};

// --- Iconic landmarks tour ---

struct LandmarkStop {
    name: &'static str,
    year: u16,
    lat: f64,
    lng: f64,
    distance: f32,
    pitch: f32,
    description: &'static str,
}

const LANDMARK_TOUR: &[LandmarkStop] = &[
    LandmarkStop { name: "BATTERY PARK",              year: 1760, lat: 40.7033, lng: -74.0170, distance: 600.0,  pitch: 0.9,  description: "Where New York began — Dutch colonial tip of Manhattan" },
    LandmarkStop { name: "CITY HALL",                  year: 1812, lat: 40.7128, lng: -74.0060, distance: 500.0,  pitch: 0.95, description: "Seat of NYC government since 1812" },
    LandmarkStop { name: "BROOKLYN BRIDGE",            year: 1883, lat: 40.7061, lng: -73.9969, distance: 700.0,  pitch: 0.8,  description: "Gothic towers over the East River — opened 1883" },
    LandmarkStop { name: "FLATIRON BUILDING",          year: 1902, lat: 40.7411, lng: -73.9897, distance: 500.0,  pitch: 1.0,  description: "The triangular icon of Broadway and Fifth — 1902" },
    LandmarkStop { name: "GRAND CENTRAL",              year: 1913, lat: 40.7527, lng: -73.9772, distance: 500.0,  pitch: 0.95, description: "Beaux-Arts cathedral of transit — 1913" },
    LandmarkStop { name: "WOOLWORTH BUILDING",         year: 1913, lat: 40.7125, lng: -74.0083, distance: 500.0,  pitch: 1.05, description: "Cathedral of Commerce — tallest in world 1913-1930" },
    LandmarkStop { name: "CHRYSLER BUILDING",          year: 1930, lat: 40.7516, lng: -73.9755, distance: 450.0,  pitch: 1.1,  description: "Art Deco crown jewel — briefly world's tallest, 1930" },
    LandmarkStop { name: "EMPIRE STATE BUILDING",      year: 1931, lat: 40.7484, lng: -73.9857, distance: 500.0,  pitch: 1.1,  description: "1,454 ft — world's tallest 1931-1970" },
    LandmarkStop { name: "ROCKEFELLER CENTER",         year: 1939, lat: 40.7587, lng: -73.9787, distance: 500.0,  pitch: 1.0,  description: "Art Deco city-within-a-city — Atlas, the rink, 30 Rock" },
    LandmarkStop { name: "UNITED NATIONS",             year: 1952, lat: 40.7489, lng: -73.9680, distance: 600.0,  pitch: 0.9,  description: "Le Corbusier's glass slab on the East River — 1952" },
    LandmarkStop { name: "LINCOLN CENTER",             year: 1962, lat: 40.7725, lng: -73.9835, distance: 500.0,  pitch: 0.9,  description: "Performing arts campus — replaced San Juan Hill neighborhood" },
    LandmarkStop { name: "1520 SEDGWICK AVE",          year: 1973, lat: 40.8301, lng: -73.9225, distance: 400.0,  pitch: 0.85, description: "Birthplace of hip-hop — DJ Kool Herc, August 11, 1973" },
    LandmarkStop { name: "YANKEE STADIUM",             year: 1923, lat: 40.8296, lng: -73.9262, distance: 800.0,  pitch: 0.85, description: "The House That Ruth Built — Bronx icon since 1923" },
    LandmarkStop { name: "CONEY ISLAND",               year: 1903, lat: 40.5749, lng: -73.9859, distance: 1200.0, pitch: 0.8,  description: "America's playground — Luna Park, Cyclone, Nathan's" },
    LandmarkStop { name: "BROOKLYN HEIGHTS",           year: 1950, lat: 40.6960, lng: -73.9977, distance: 600.0,  pitch: 0.85, description: "Manhattan skyline panorama from America's first suburb" },
    LandmarkStop { name: "ONE WORLD TRADE CENTER",     year: 2014, lat: 40.7127, lng: -74.0134, distance: 600.0,  pitch: 1.1,  description: "1,776 ft Freedom Tower — opened 2014" },
    LandmarkStop { name: "HUDSON YARDS",               year: 2019, lat: 40.7536, lng: -74.0003, distance: 600.0,  pitch: 1.0,  description: "NYC's newest neighborhood — The Vessel, Edge, 2019" },
    LandmarkStop { name: "THE SKYLINE",                year: 2026, lat: 40.7549, lng: -73.9840, distance: 2500.0, pitch: 1.05, description: "Over one million buildings — the full five boroughs" },
];

fn main() {
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Sixth Borough".into(),
                resolution: bevy::window::WindowResolution::new(1920, 1080),
                ..default()
            }),
            ..default()
        }))
        .add_plugins(building::BuildingPlugin)
        .add_plugins(biography::BiographyPlugin)
        .init_resource::<CameraAnimation>()
        .init_resource::<AutoTour>()
        .add_systems(Startup, setup_scene)
        .add_systems(Update, (
            camera_controls,
            camera_animate,
            dwell_orbit,
            year_scrub,
            year_animate,
            guided_tour_input,
            auto_tour_system,
            update_hud,
            update_tour_overlay,
        ))
        .run();
}

// --- Camera ---

#[derive(Component)]
struct OrbitCamera {
    yaw: f32,
    pitch: f32,
    distance: f32,
    target: Vec3,
}

impl Default for OrbitCamera {
    fn default() -> Self {
        Self {
            yaw: -90.0_f32.to_radians(),
            pitch: 60.0_f32.to_radians(),
            distance: 2000.0,
            target: Vec3::ZERO,
        }
    }
}

#[derive(Resource, Default)]
struct CameraAnimation {
    active: bool,
    elapsed: f32,
    duration: f32,
    start_yaw: f32,
    start_pitch: f32,
    start_distance: f32,
    start_target: Vec3,
    end_yaw: f32,
    end_pitch: f32,
    end_distance: f32,
    end_target: Vec3,
}

// --- UI marker components ---

#[derive(Component)]
struct YearText;

#[derive(Component)]
struct EraText;

#[derive(Component)]
struct StatsText;

#[derive(Component)]
struct TourOverlayPanel;

#[derive(Component)]
struct TourNameText;

#[derive(Component)]
struct TourDescText;

#[derive(Component)]
struct TourCounterText;

fn setup_scene(mut commands: Commands) {
    let orbit = OrbitCamera::default();
    let eye = orbit_eye(&orbit);

    commands.spawn((
        Camera3d::default(),
        Transform::from_translation(eye).looking_at(orbit.target, Vec3::Y),
        orbit,
    ));

    // PS2-style harsh directional light with low-res shadow map
    commands.spawn((
        DirectionalLight {
            illuminance: 20_000.0,
            shadows_enabled: true,
            shadow_depth_bias: 0.02,
            shadow_normal_bias: 1.8,
            ..default()
        },
        Transform::from_rotation(Quat::from_euler(EulerRot::XYZ, -0.8, 0.4, 0.0)),
    ));

    // Dim ambient so shadows are visible and contrasty (PS2 vibe)
    commands.insert_resource(bevy::light::GlobalAmbientLight {
        color: Color::srgb(0.3, 0.35, 0.5),
        brightness: 200.0,
        affects_lightmapped_meshes: true,
    });

    // ── Top-left HUD: Year + Era + Stats ──
    commands
        .spawn((
            Node {
                position_type: PositionType::Absolute,
                left: Val::Px(24.0),
                top: Val::Px(24.0),
                flex_direction: FlexDirection::Column,
                row_gap: Val::Px(4.0),
                padding: UiRect::all(Val::Px(14.0)),
                ..default()
            },
            BackgroundColor(Color::srgba(0.0, 0.0, 0.0, 0.85)),
        ))
        .with_children(|parent| {
            parent.spawn((
                Text::new("SIXTH BOROUGH"),
                TextFont { font_size: 22.0, ..default() },
                TextColor(Color::WHITE),
            ));
            parent.spawn((
                YearText,
                Text::new("2026"),
                TextFont { font_size: 48.0, ..default() },
                TextColor(Color::srgb(0.0, 0.72, 0.83)),
            ));
            parent.spawn((
                EraText,
                Text::new("GLASS TOWER ERA"),
                TextFont { font_size: 14.0, ..default() },
                TextColor(Color::srgb(0.6, 0.6, 0.6)),
            ));
            parent.spawn((
                StatsText,
                Text::new("1,082,081 BUILDINGS"),
                TextFont { font_size: 11.0, ..default() },
                TextColor(Color::srgb(0.4, 0.4, 0.4)),
            ));
        });

    // ── Right side: Era Legend ──
    commands
        .spawn((
            Node {
                position_type: PositionType::Absolute,
                right: Val::Px(24.0),
                top: Val::Px(24.0),
                flex_direction: FlexDirection::Column,
                row_gap: Val::Px(6.0),
                padding: UiRect::all(Val::Px(14.0)),
                ..default()
            },
            BackgroundColor(Color::srgba(0.0, 0.0, 0.0, 0.85)),
        ))
        .with_children(|parent| {
            parent.spawn((
                Text::new("CONSTRUCTION ERA"),
                TextFont { font_size: 11.0, ..default() },
                TextColor(Color::srgb(0.0, 0.72, 0.83)),
            ));

            let era_sample_years: &[u16] = &[0, 1700, 1800, 1850, 1900, 1945, 1970, 2000];
            for (&year, &label) in era_sample_years.iter().zip(ERA_LABELS.iter()) {
                let color = era_color(year);
                parent
                    .spawn(Node {
                        flex_direction: FlexDirection::Row,
                        align_items: AlignItems::Center,
                        column_gap: Val::Px(8.0),
                        ..default()
                    })
                    .with_children(|row| {
                        row.spawn((
                            Node {
                                width: Val::Px(14.0),
                                height: Val::Px(14.0),
                                ..default()
                            },
                            BackgroundColor(color),
                        ));
                        row.spawn((
                            Text::new(label),
                            TextFont { font_size: 12.0, ..default() },
                            TextColor(Color::srgb(0.7, 0.7, 0.7)),
                        ));
                    });
            }
        });

    // ── Center: Tour landmark overlay (hidden by default) ──
    commands
        .spawn((
            TourOverlayPanel,
            Node {
                position_type: PositionType::Absolute,
                bottom: Val::Px(100.0),
                left: Val::Px(0.0),
                right: Val::Px(0.0),
                flex_direction: FlexDirection::Column,
                align_items: AlignItems::Center,
                row_gap: Val::Px(6.0),
                padding: UiRect::all(Val::Px(20.0)),
                ..default()
            },
            Visibility::Hidden,
        ))
        .with_children(|parent| {
            // Landmark name — big and bold
            parent.spawn((
                TourNameText,
                Text::new(""),
                TextFont { font_size: 42.0, ..default() },
                TextColor(Color::WHITE),
            ));
            // Description
            parent.spawn((
                TourDescText,
                Text::new(""),
                TextFont { font_size: 18.0, ..default() },
                TextColor(Color::srgb(0.7, 0.8, 0.7)),
            ));
            // Counter + controls hint
            parent.spawn((
                TourCounterText,
                Text::new(""),
                TextFont { font_size: 12.0, ..default() },
                TextColor(Color::srgb(0.4, 0.4, 0.4)),
            ));
        });

    // ── Bottom-left: Controls help ──
    commands
        .spawn((
            Node {
                position_type: PositionType::Absolute,
                left: Val::Px(24.0),
                bottom: Val::Px(24.0),
                flex_direction: FlexDirection::Column,
                row_gap: Val::Px(4.0),
                padding: UiRect::all(Val::Px(10.0)),
                ..default()
            },
            BackgroundColor(Color::srgba(0.0, 0.0, 0.0, 0.5)),
        ))
        .with_children(|parent| {
            parent.spawn((
                Text::new("T: auto-tour  |  N/P: next/prev  |  1-9: era jump  |  WASD: pan  |  Scroll: zoom"),
                TextFont { font_size: 11.0, ..default() },
                TextColor(Color::srgb(0.5, 0.5, 0.5)),
            ));
            parent.spawn((
                Text::new("Left/Right: year  |  Click: building info  |  Esc: dismiss"),
                TextFont { font_size: 11.0, ..default() },
                TextColor(Color::srgb(0.5, 0.5, 0.5)),
            ));
        });

    info!("Scene setup complete");
}

fn orbit_eye(orbit: &OrbitCamera) -> Vec3 {
    let x = orbit.distance * orbit.pitch.cos() * orbit.yaw.cos();
    let y = orbit.distance * orbit.pitch.sin();
    let z = orbit.distance * orbit.pitch.cos() * orbit.yaw.sin();
    orbit.target + Vec3::new(x, y, z)
}

fn camera_controls(
    time: Res<Time>,
    keys: Res<ButtonInput<KeyCode>>,
    mouse_button: Res<ButtonInput<MouseButton>>,
    accumulated_motion: Res<AccumulatedMouseMotion>,
    accumulated_scroll: Res<AccumulatedMouseScroll>,
    mut cameras: Query<(&mut OrbitCamera, &mut Transform)>,
    anim: Res<CameraAnimation>,
    tour: Res<AutoTour>,
) {
    // Don't fight animation or dwell orbit
    if anim.active || tour.dwelling {
        return;
    }

    let Ok((mut orbit, mut transform)) = cameras.single_mut() else { return };

    let dt = time.delta_secs();
    let pan_speed = orbit.distance * 0.5;

    let forward = Vec3::new(orbit.yaw.cos(), 0.0, orbit.yaw.sin()).normalize();
    let right = Vec3::new(-orbit.yaw.sin(), 0.0, orbit.yaw.cos()).normalize();

    if keys.pressed(KeyCode::KeyW) { orbit.target += forward * pan_speed * dt; }
    if keys.pressed(KeyCode::KeyS) { orbit.target -= forward * pan_speed * dt; }
    if keys.pressed(KeyCode::KeyA) { orbit.target -= right * pan_speed * dt; }
    if keys.pressed(KeyCode::KeyD) { orbit.target += right * pan_speed * dt; }

    if mouse_button.pressed(MouseButton::Right) {
        let delta = accumulated_motion.delta;
        orbit.yaw -= delta.x * 0.005;
        orbit.pitch = (orbit.pitch + delta.y * 0.005).clamp(0.1, 1.5);
    }

    let scroll_y = accumulated_scroll.delta.y;
    if scroll_y.abs() > 0.01 {
        orbit.distance *= 1.0 - scroll_y * 0.1;
        orbit.distance = orbit.distance.clamp(50.0, 20_000.0);
    }

    let eye = orbit_eye(&orbit);
    *transform = Transform::from_translation(eye).looking_at(orbit.target, Vec3::Y);
}

// --- Camera fly-to animation ---

fn camera_animate(
    time: Res<Time>,
    mut anim: ResMut<CameraAnimation>,
    mut cameras: Query<(&mut OrbitCamera, &mut Transform)>,
    mut tour: ResMut<AutoTour>,
) {
    if !anim.active {
        return;
    }

    anim.elapsed += time.delta_secs();
    let t = (anim.elapsed / anim.duration).min(1.0);
    // Smooth ease-in-out (quintic for more dramatic ease)
    let t = t * t * t * (t * (t * 6.0 - 15.0) + 10.0);

    let Ok((mut orbit, mut transform)) = cameras.single_mut() else { return };

    orbit.yaw = lerp(anim.start_yaw, anim.end_yaw, t);
    orbit.pitch = lerp(anim.start_pitch, anim.end_pitch, t);
    orbit.distance = lerp(anim.start_distance, anim.end_distance, t);
    orbit.target = anim.start_target.lerp(anim.end_target, t);

    let eye = orbit_eye(&orbit);
    *transform = Transform::from_translation(eye).looking_at(orbit.target, Vec3::Y);

    if anim.elapsed >= anim.duration {
        anim.active = false;
        // Start dwelling (slow orbit) after arrival
        if tour.active || tour.current_stop > 0 {
            tour.dwelling = true;
            tour.dwell_timer = 0.0;
        }
    }
}

// --- Slow orbit while dwelling at a landmark ---

fn dwell_orbit(
    time: Res<Time>,
    tour: Res<AutoTour>,
    mut cameras: Query<(&mut OrbitCamera, &mut Transform)>,
) {
    if !tour.dwelling {
        return;
    }

    let Ok((mut orbit, mut transform)) = cameras.single_mut() else { return };

    // Slowly rotate around the landmark
    let orbit_speed = 0.08; // radians per second
    orbit.yaw += orbit_speed * time.delta_secs();

    let eye = orbit_eye(&orbit);
    *transform = Transform::from_translation(eye).looking_at(orbit.target, Vec3::Y);
}

fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}

// --- Smooth year animation ---

#[derive(Resource)]
struct AutoTour {
    active: bool,
    current_stop: usize,
    dwell_timer: f32,
    dwell_duration: f32,
    dwelling: bool,
    // Year animation
    year_target: u16,
    year_animating: bool,
}

impl Default for AutoTour {
    fn default() -> Self {
        Self {
            active: false,
            current_stop: 0,
            dwell_timer: 0.0,
            dwell_duration: 7.0,
            dwelling: false,
            year_target: 2026,
            year_animating: false,
        }
    }
}

fn year_animate(
    time: Res<Time>,
    tour: Res<AutoTour>,
    mut year_filter: ResMut<YearFilter>,
) {
    if !tour.year_animating {
        return;
    }

    let current = year_filter.current_year as f32;
    let target = tour.year_target as f32;
    let diff = target - current;

    if diff.abs() < 1.0 {
        year_filter.current_year = tour.year_target;
        return;
    }

    // Smooth interpolation — faster when far, slower when close
    let speed = diff.abs().max(30.0) * 2.0;
    let step = diff.signum() * speed * time.delta_secs();

    let new_year = (current + step).clamp(1700.0, 2026.0);
    year_filter.current_year = new_year as u16;
}

// --- Guided tour (1-9 era stations) ---

const CENTER_LAT: f64 = 40.7831;
const CENTER_LNG: f64 = -73.9712;
const METERS_PER_DEG_LAT: f64 = 111_320.0;

fn guided_tour_input(
    keys: Res<ButtonInput<KeyCode>>,
    mut tour: ResMut<AutoTour>,
    mut anim: ResMut<CameraAnimation>,
    mut year_filter: ResMut<YearFilter>,
    cameras: Query<&OrbitCamera>,
) {
    let station_keys = [
        KeyCode::Digit1, KeyCode::Digit2, KeyCode::Digit3,
        KeyCode::Digit4, KeyCode::Digit5, KeyCode::Digit6,
        KeyCode::Digit7, KeyCode::Digit8, KeyCode::Digit9,
    ];

    for (i, &key) in station_keys.iter().enumerate() {
        if keys.just_pressed(key) {
            let station = &TOUR_STATIONS[i];

            let cos_lat = (CENTER_LAT.to_radians()).cos();
            let tx = ((station.lng - CENTER_LNG) * cos_lat * METERS_PER_DEG_LAT) as f32;
            let tz = -((station.lat - CENTER_LAT) * METERS_PER_DEG_LAT) as f32;

            let Ok(orbit) = cameras.single() else { return };

            // Stop auto-tour if running
            tour.active = false;
            tour.dwelling = false;

            anim.active = true;
            anim.elapsed = 0.0;
            anim.duration = 2.0;
            anim.start_yaw = orbit.yaw;
            anim.start_pitch = orbit.pitch;
            anim.start_distance = orbit.distance;
            anim.start_target = orbit.target;
            anim.end_yaw = station.yaw;
            anim.end_pitch = station.pitch;
            anim.end_distance = station.distance;
            anim.end_target = Vec3::new(tx, 0.0, tz);

            year_filter.current_year = station.year;

            info!("Era station: {} ({})", station.name, station.year);
            break;
        }
    }
}

// --- Auto tour system ---

fn auto_tour_system(
    keys: Res<ButtonInput<KeyCode>>,
    time: Res<Time>,
    mut tour: ResMut<AutoTour>,
    mut anim: ResMut<CameraAnimation>,
    cameras: Query<&OrbitCamera>,
) {
    // T: toggle auto-tour
    if keys.just_pressed(KeyCode::KeyT) {
        tour.active = !tour.active;
        tour.dwelling = false;
        if tour.active {
            tour.current_stop = 0;
            tour.dwell_timer = 0.0;
            fly_to_landmark(tour.current_stop, &mut tour, &mut anim, &cameras);
            info!("Auto-tour started");
        } else {
            tour.year_animating = false;
            info!("Auto-tour stopped");
        }
        return;
    }

    // N: next stop
    if keys.just_pressed(KeyCode::KeyN) {
        tour.current_stop = (tour.current_stop + 1) % LANDMARK_TOUR.len();
        tour.dwell_timer = 0.0;
        tour.dwelling = false;
        fly_to_landmark(tour.current_stop, &mut tour, &mut anim, &cameras);
        return;
    }
    // P: previous stop
    if keys.just_pressed(KeyCode::KeyP) {
        tour.current_stop = if tour.current_stop == 0 {
            LANDMARK_TOUR.len() - 1
        } else {
            tour.current_stop - 1
        };
        tour.dwell_timer = 0.0;
        tour.dwelling = false;
        fly_to_landmark(tour.current_stop, &mut tour, &mut anim, &cameras);
        return;
    }

    // Dwell timer → auto-advance to next
    if !tour.active || !tour.dwelling {
        return;
    }

    tour.dwell_timer += time.delta_secs();
    if tour.dwell_timer >= tour.dwell_duration {
        tour.current_stop = (tour.current_stop + 1) % LANDMARK_TOUR.len();
        tour.dwell_timer = 0.0;
        tour.dwelling = false;
        fly_to_landmark(tour.current_stop, &mut tour, &mut anim, &cameras);
    }
}

fn fly_to_landmark(
    idx: usize,
    tour: &mut ResMut<AutoTour>,
    anim: &mut ResMut<CameraAnimation>,
    cameras: &Query<&OrbitCamera>,
) {
    let stop = &LANDMARK_TOUR[idx];
    let cos_lat = (CENTER_LAT.to_radians()).cos();
    let tx = ((stop.lng - CENTER_LNG) * cos_lat * METERS_PER_DEG_LAT) as f32;
    let tz = -((stop.lat - CENTER_LAT) * METERS_PER_DEG_LAT) as f32;

    let Ok(orbit) = cameras.single() else { return };

    // Vary the approach angle per landmark for visual interest
    let approach_yaw = -1.57 + (idx as f32 * 0.7);

    anim.active = true;
    anim.elapsed = 0.0;
    anim.duration = 3.0; // cinematic pace
    anim.start_yaw = orbit.yaw;
    anim.start_pitch = orbit.pitch;
    anim.start_distance = orbit.distance;
    anim.start_target = orbit.target;
    anim.end_yaw = approach_yaw;
    anim.end_pitch = stop.pitch;
    anim.end_distance = stop.distance;
    anim.end_target = Vec3::new(tx, 0.0, tz);

    // Smooth year animation instead of jump
    tour.year_target = stop.year;
    tour.year_animating = true;

    info!("→ {}/{}: {} — {}", idx + 1, LANDMARK_TOUR.len(), stop.name, stop.description);
}

// --- Tour overlay (big center title) ---

fn update_tour_overlay(
    tour: Res<AutoTour>,
    mut panels: Query<&mut Visibility, With<TourOverlayPanel>>,
    mut names: Query<&mut Text, (With<TourNameText>, Without<TourDescText>, Without<TourCounterText>)>,
    mut descs: Query<&mut Text, (With<TourDescText>, Without<TourNameText>, Without<TourCounterText>)>,
    mut counters: Query<&mut Text, (With<TourCounterText>, Without<TourNameText>, Without<TourDescText>)>,
) {
    if !tour.is_changed() {
        return;
    }

    let show_overlay = tour.active || tour.dwelling || tour.current_stop > 0;

    for mut vis in &mut panels {
        *vis = if show_overlay { Visibility::Inherited } else { Visibility::Hidden };
    }

    if show_overlay {
        let stop = &LANDMARK_TOUR[tour.current_stop];

        for mut text in &mut names {
            *text = Text::new(stop.name);
        }
        for mut text in &mut descs {
            *text = Text::new(stop.description);
        }
        for mut text in &mut counters {
            let mode = if tour.active { "AUTO-TOUR" } else { "TOUR" };
            *text = Text::new(format!(
                "{} — {}/{}  |  T: auto  N/P: step  Esc: exit",
                mode, tour.current_stop + 1, LANDMARK_TOUR.len()
            ));
        }
    }
}

// --- Year scrubber (manual) ---

fn year_scrub(
    keys: Res<ButtonInput<KeyCode>>,
    time: Res<Time>,
    mut year_filter: ResMut<YearFilter>,
    mut hold_timer: Local<f32>,
    mut tour: ResMut<AutoTour>,
) {
    let left = keys.pressed(KeyCode::ArrowLeft);
    let right = keys.pressed(KeyCode::ArrowRight);

    if !left && !right {
        *hold_timer = 0.0;
        return;
    }

    // Manual year scrub cancels year animation
    tour.year_animating = false;

    *hold_timer += time.delta_secs();
    let speed = if *hold_timer < 0.5 { 1 } else if *hold_timer < 2.0 { 3 } else { 10 };

    let interval = 1.0 / 30.0;
    if *hold_timer % interval > time.delta_secs() {
        return;
    }

    let year = year_filter.current_year as i32;
    let new_year = if left { year - speed } else { year + speed };
    year_filter.current_year = new_year.clamp(1700, 2026) as u16;
}

// --- HUD update ---

fn update_hud(
    year_filter: Res<YearFilter>,
    stats: Res<BuildingStats>,
    mut year_query: Query<&mut Text, (With<YearText>, Without<EraText>, Without<StatsText>)>,
    mut era_query: Query<&mut Text, (With<EraText>, Without<YearText>, Without<StatsText>)>,
    mut stats_query: Query<&mut Text, (With<StatsText>, Without<YearText>, Without<EraText>)>,
) {
    if !year_filter.is_changed() && !stats.is_changed() {
        return;
    }

    let y = year_filter.current_year;

    for mut text in &mut year_query {
        *text = Text::new(format!("{}", y));
    }
    for mut text in &mut era_query {
        *text = Text::new(era_label(y));
    }
    for mut text in &mut stats_query {
        *text = Text::new(format!(
            "{} / {} BUILDINGS",
            format_number(stats.visible),
            format_number(stats.total)
        ));
    }
}

fn format_number(n: u32) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, c) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(c);
    }
    result.chars().rev().collect()
}
