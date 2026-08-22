use bevy::prelude::*;
use bevy::picking::mesh_picking::MeshPickingSettings;
use std::sync::{mpsc, Mutex};

use crate::building::{BuildingData, MarqueeData, era_label};

struct BiographyResponse {
    bin: String,
    building_name: String,
    narrative: String,
}

#[derive(Resource)]
struct BiographyChannel {
    sender: mpsc::Sender<BiographyResponse>,
    receiver: Mutex<mpsc::Receiver<BiographyResponse>>,
}

impl Default for BiographyChannel {
    fn default() -> Self {
        let (sender, receiver) = mpsc::channel();
        Self {
            sender,
            receiver: Mutex::new(receiver),
        }
    }
}

#[derive(Resource, Default)]
struct CurrentBiography {
    bin: String,
    text: String,
    visible: bool,
}

#[derive(Component)]
struct BiographyPanel;

#[derive(Component)]
struct BiographyText;

pub struct BiographyPlugin;

impl Plugin for BiographyPlugin {
    fn build(&self, app: &mut App) {
        // Disable Bevy's mesh picking — it raycasts 45K meshes per frame and kills FPS.
        app.insert_resource(MeshPickingSettings {
            require_markers: true,
            ..default()
        });

        app.init_resource::<BiographyChannel>()
            .init_resource::<CurrentBiography>()
            .add_systems(Startup, setup_biography_ui)
            .add_systems(Update, (
                handle_click,
                poll_biography_response,
                update_biography_ui,
                dismiss_biography,
            ));
    }
}

fn setup_biography_ui(mut commands: Commands) {
    commands
        .spawn((
            BiographyPanel,
            Node {
                position_type: PositionType::Absolute,
                right: Val::Px(20.0),
                top: Val::Px(300.0),
                width: Val::Px(420.0),
                max_height: Val::Vh(70.0),
                padding: UiRect::all(Val::Px(14.0)),
                overflow: Overflow::clip_y(),
                flex_direction: FlexDirection::Column,
                ..default()
            },
            BackgroundColor(Color::srgba(0.05, 0.05, 0.1, 0.92)),
            Visibility::Hidden,
        ))
        .with_children(|parent| {
            parent.spawn((
                BiographyText,
                Text::new(""),
                TextFont {
                    font_size: 15.0,
                    ..default()
                },
                TextColor(Color::srgb(0.9, 0.95, 0.9)),
            ));
        });
}

/// Lightweight click detection: project building centroids to screen space,
/// find the closest one to the cursor.
fn handle_click(
    mouse: Res<ButtonInput<MouseButton>>,
    windows: Query<&Window>,
    cameras: Query<(&Camera, &GlobalTransform)>,
    buildings: Query<(&BuildingData, &Visibility)>,
    channel: Res<BiographyChannel>,
    marquee: Res<MarqueeData>,
    mut bio: ResMut<CurrentBiography>,
) {
    if !mouse.just_pressed(MouseButton::Left) {
        return;
    }

    let Ok(window) = windows.single() else { return };
    let Some(cursor) = window.cursor_position() else { return };
    let Ok((camera, cam_gt)) = cameras.single() else { return };

    // Project each visible building centroid to screen space, pick closest to cursor
    let mut best_dist_sq = f32::MAX;
    let mut best_bin: Option<String> = None;
    let max_screen_dist = 30.0_f32; // max pixels from cursor to count as a hit

    for (data, vis) in &buildings {
        if *vis == Visibility::Hidden {
            continue;
        }

        // Project centroid to screen
        let Ok(screen_pos) = camera.world_to_viewport(cam_gt, data.centroid) else {
            continue;
        };

        let dx = screen_pos.x - cursor.x;
        let dy = screen_pos.y - cursor.y;
        let dist_sq = dx * dx + dy * dy;

        if dist_sq < best_dist_sq && dist_sq < max_screen_dist * max_screen_dist {
            best_dist_sq = dist_sq;
            best_bin = Some(data.bin.clone());
        }
    }

    if let Some(bin) = best_bin {
        info!("Clicked building BIN: {}", bin);

        // Find the building data for the clicked BIN
        let mut building_year = 0u16;
        let mut building_height = 0.0f32;
        let mut centroid = Vec3::ZERO;
        for (data, _) in &buildings {
            if data.bin == bin {
                building_year = data.year;
                building_height = data.height;
                centroid = data.centroid;
                break;
            }
        }

        // Check for marquee content
        let marquee_body = marquee.entries.get(&bin).map(|e| {
            format!(
                "━━━ {} ━━━\n{}\n\n{}",
                e.title.to_uppercase(),
                e.niche_tags.join(" · "),
                e.body,
            )
        });

        let era = era_label(building_year);
        let year_str = if building_year > 0 {
            format!("Built {} · {}", building_year, era)
        } else {
            format!("Year unknown · {}", era)
        };

        bio.visible = true;
        bio.bin = bin.clone();
        bio.text = format!(
            "BIN {}\n{}\n{:.0}m tall\n\nLoading biography from Nemotron...",
            bin, year_str, building_height
        );

        let sender = channel.sender.clone();
        let marquee_fallback = marquee_body.unwrap_or_else(|| {
            format!("{:.0}m tall. {} construction.", building_height, era)
        });
        let cx = centroid.x;
        let cz = centroid.z;
        std::thread::spawn(move || {
            let (building_name, biography) = fetch_biography(&bin, cx, cz);
            let narrative = if biography.is_empty() {
                marquee_fallback
            } else {
                biography
            };
            let _ = sender.send(BiographyResponse { bin, building_name, narrative });
        });
    }
}

fn poll_biography_response(
    channel: Res<BiographyChannel>,
    mut bio: ResMut<CurrentBiography>,
) {
    let maybe = channel
        .receiver
        .lock()
        .ok()
        .and_then(|rx| rx.try_recv().ok());

    if let Some(resp) = maybe {
        if resp.bin == bio.bin {
            let title = if resp.building_name.is_empty() {
                format!("BIN {}", resp.bin)
            } else {
                resp.building_name
            };
            bio.text = format!("{}\n\n{}", title, resp.narrative);
        }
    }
}

fn update_biography_ui(
    bio: Res<CurrentBiography>,
    mut panels: Query<&mut Visibility, With<BiographyPanel>>,
    mut texts: Query<&mut Text, With<BiographyText>>,
) {
    if !bio.is_changed() {
        return;
    }

    for mut vis in &mut panels {
        *vis = if bio.visible {
            Visibility::Inherited
        } else {
            Visibility::Hidden
        };
    }

    for mut text in &mut texts {
        *text = Text::new(&bio.text);
    }
}

fn dismiss_biography(
    keys: Res<ButtonInput<KeyCode>>,
    mut bio: ResMut<CurrentBiography>,
) {
    if keys.just_pressed(KeyCode::Escape) {
        bio.visible = false;
    }
}

/// Returns (building_name, biography_text).
/// Matches the web version: POST {bin, lat, lon} → {biography, building_name}
fn fetch_biography(bin: &str, local_x: f32, local_z: f32) -> (String, String) {
    // Convert local coords back to approximate lat/lon for the API
    let center_lat: f64 = 40.7831;
    let center_lng: f64 = -73.9712;
    let meters_per_deg_lat: f64 = 111_320.0;
    let cos_lat = center_lat.to_radians().cos();
    let lon = center_lng + (local_x as f64) / (cos_lat * meters_per_deg_lat);
    let lat = center_lat - (local_z as f64) / meters_per_deg_lat;

    let url = "http://127.0.0.1:30001/biography";
    let body = serde_json::json!({
        "bin": bin,
        "lat": lat,
        "lon": lon,
    });

    match ureq::post(url)
        .header("Content-Type", "application/json")
        .send_json(&body)
    {
        Ok(mut resp) => match resp.body_mut().read_to_string() {
            Ok(text) => {
                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&text) {
                    let name = val.get("building_name")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_string();
                    let bio = val.get("biography")
                        .and_then(|v| v.as_str())
                        // Strip markdown headers like the web version does
                        .map(|s| {
                            s.lines()
                                .filter(|l| !l.starts_with('#'))
                                .collect::<Vec<_>>()
                                .join("\n")
                                .trim()
                                .to_string()
                        })
                        .unwrap_or_default();
                    (name, bio)
                } else {
                    (String::new(), text)
                }
            }
            Err(e) => (String::new(), format!("Error reading response: {e}")),
        },
        Err(e) => {
            let msg = e.to_string();
            if msg.contains("404") {
                (String::new(), String::new()) // empty = will use marquee fallback
            } else {
                (String::new(), format!("Request failed: {e}"))
            }
        }
    }
}
