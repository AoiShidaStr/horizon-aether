//! The Aether for Horizon: the native (trait mod) half.
//!
//! A clean-room port from public behaviour descriptions of the Aether's three
//! bosses (the Slider, the Valkyrie Queen and the Sun Spirit). The game's own
//! zombie class carries them; this crate gives them their goals, their box,
//! and the immunities the descriptions give them. The content half
//! (`content/`) declares their entity types and attributes, plus the blocks,
//! items, recipes and loot of the Aether.
//!
//! The launcher links this crate into the game and calls `hooks()`
//! (docs/native-mods.md, "Trait mods"). The same `Hooks` serve a dedicated
//! server (only the server hooks fire there) and a client (where goals never
//! tick, but the box change matters).
pub mod mobs;

mod server;

use horizon_client::mod_api::{
    EntityLeaveLevelEvent, EntityTickListenedEvent, EntityTickPostEvent, Flow, Hooks, Host,
    LivingConversionPreEvent, LivingDeathEvent, LivingIncomingDamageEvent, RegisterGoalsEvent,
    WorldLifecycleEvent, WorldPhase,
};

pub fn hooks() -> Box<dyn Hooks> {
    Box::new(Mod)
}

struct Mod;

impl Hooks for Mod {
    fn register_goals(&self, event: &mut RegisterGoalsEvent<'_>) {
        server::register_goals(event);
    }

    fn world_lifecycle(&self, _host: &mut dyn Host, event: &mut WorldLifecycleEvent<'_>) {
        if matches!(event.phase, WorldPhase::WorldOpenReady | WorldPhase::WorldCloseFinal) {
            server::clear();
        }
    }

    fn entity_tick_listened(&self, _host: &mut dyn Host, event: &mut EntityTickListenedEvent) {
        event.listened = true;
    }

    fn entity_tick_post(&self, host: &mut dyn Host, event: &mut EntityTickPostEvent<'_>) {
        server::entity_tick_post(host, event);
    }

    fn living_conversion_pre(&self, _host: &mut dyn Host, event: &mut LivingConversionPreEvent<'_>) -> Flow {
        server::living_conversion_pre(event)
    }

    fn living_incoming_damage(&self, event: &mut LivingIncomingDamageEvent<'_>) -> Flow {
        server::living_incoming_damage(event)
    }

    fn living_death(&self, _host: &mut dyn Host, event: &mut LivingDeathEvent<'_>) -> Flow {
        server::living_death(event)
    }

    fn entity_leave_level(&self, _host: &mut dyn Host, event: &mut EntityLeaveLevelEvent<'_>) {
        server::entity_leave_level(event.entity, event.kind);
    }
}
