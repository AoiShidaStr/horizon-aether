//! The server half: the three bosses' goals, the zombie template's habits
//! they do not have, and their immunities.
//!
//! Clean-room: written from the public behaviour descriptions of the Aether's
//! bosses, not from the Java mod's code. Original code.
use crate::mobs::Kind;
use horizon_client::mobs::{
    Mob,
    goals::{self, Cx, Float, Goal, HurtByTarget, LookAtPlayer, NearestTarget, RandomLookAround, Stroll},
};
use horizon_client::mod_api::{
    Compound, EntityTickPostEvent, Flow, Host, LivingConversionPreEvent, LivingDeathEvent,
    LivingIncomingDamageEvent, RegisterGoalsEvent, Tag,
};
use std::sync::Arc;

fn kind_of(m: &Mob) -> Option<Kind> {
    Kind::from_id(&m.kind.id)
}

/// The bosses' goals, in place of the zombie's. Also asked for a client's
/// copies, where goals never tick; the box change below matters on both sides.
pub fn register_goals(event: &mut RegisterGoalsEvent<'_>) {
    let mob = &mut *event.mob;
    let Some(kind) = kind_of(mob) else {
        return;
    };
    // The boss box, and no burning in daylight for the stone and sun bosses,
    // on this mob's own copy of its type (the zombie template is 0.6 x 1.95
    // and burns).
    let mut ty = (*mob.kind).clone();
    let (w, h, eye) = kind.size();
    ty.width = w;
    ty.height = h;
    ty.eye_height = eye;
    ty.flags.burns_in_day = kind.burns_in_daylight();
    mob.kind = Arc::new(ty);

    let ai = &mut mob.ai;
    ai.goals.clear();
    ai.targets.clear();
    ai.goals.add(0, Float);
    ai.goals.add(1, AetherMelee::new(kind));
    ai.goals.add(5, Stroll::avoiding_water(kind.stroll_speed()));
    ai.goals.add(6, LookAtPlayer::new(12.0));
    ai.goals.add(6, RandomLookAround::default());
    ai.targets.add(1, HurtByTarget::new());
    ai.targets.add(2, NearestTarget::player(true));
}

/// The bosses' melee: chase the target, and land a blow on a cooldown once in
/// reach. The Slider's is slow and wide, the Valkyrie Queen's fast.
#[derive(Clone, Debug)]
pub(crate) struct AetherMelee {
    kind: Kind,
    cooldown: i32,
    recalc: i32,
    path_target: [f64; 3],
}

impl AetherMelee {
    pub(crate) fn new(kind: Kind) -> Self {
        Self {
            kind,
            cooldown: 0,
            recalc: 0,
            path_target: [0.0; 3],
        }
    }
}

impl Goal for AetherMelee {
    fn flags(&self) -> u8 {
        goals::MOVE | goals::LOOK
    }

    fn can_use(&mut self, m: &mut Mob, cx: &mut Cx) -> bool {
        let Some(who) = m.ai.target else {
            return false;
        };
        let Some(t) = cx.w.target_info(who) else {
            return false;
        };
        let in_reach = m.distance_sqr(t.position) <= self.kind.reach_sqr();
        if !in_reach && !m.sees(cx.w, who) {
            return false;
        }
        if !t.alive {
            return false;
        }
        let at = [t.position.x, t.position.y, t.position.z];
        m.create_path_to_entity(cx.w, at, 0).is_some() || in_reach
    }

    fn can_continue(&mut self, m: &mut Mob, cx: &mut Cx) -> bool {
        let Some(t) = m.target_info(cx.w) else {
            return false;
        };
        t.alive && !m.ai.nav.is_done()
    }

    fn start(&mut self, m: &mut Mob, cx: &mut Cx) {
        if let Some(t) = m.target_info(cx.w) {
            let at = [t.position.x, t.position.y, t.position.z];
            m.nav_move_to_entity(cx.w, at, 0, self.kind.chase_speed());
        }
        m.ai.aggressive = true;
        self.recalc = 0;
        self.cooldown = 0;
    }

    fn stop(&mut self, m: &mut Mob, cx: &mut Cx) {
        if let Some(t) = m.target_info(cx.w)
            && t.is_player
            && t.creative
        {
            m.ai.target = None;
        }
        m.ai.aggressive = false;
        m.nav_stop();
    }

    fn every_tick(&self) -> bool {
        true
    }

    fn tick(&mut self, m: &mut Mob, cx: &mut Cx) {
        let Some(who) = m.ai.target else {
            return;
        };
        let Some(t) = cx.w.target_info(who) else {
            return;
        };
        m.look_at_speed([t.position.x, t.eye_y, t.position.z], 30.0, 30.0);
        let at = [t.position.x, t.position.y, t.position.z];
        self.recalc = (self.recalc - 1).max(0);
        if self.recalc == 0 {
            self.path_target = at;
            self.recalc = 8;
            if !m.nav_move_to_entity(cx.w, at, 0, self.kind.chase_speed()) {
                self.recalc = 20;
            }
        }
        self.cooldown = (self.cooldown - 1).max(0);
        let d2 = m.distance_sqr(t.position);
        if self.cooldown == 0 && d2 <= self.kind.reach_sqr() {
            horizon_client::mobs::ai::do_hurt_target(m, who, cx);
            self.cooldown = self.kind.attack_cooldown();
        }
    }

    fn box_clone(&self) -> Box<dyn Goal> {
        Box::new(self.clone())
    }
}

/// The first tick this server sees one of our mobs: undo what the zombie
/// template rolled in `finalizeSpawn` (a baby, picking up loot, breaking
/// doors, calling reinforcements of its own kind).
pub fn entity_tick_post(host: &mut dyn Host, event: &mut EntityTickPostEvent<'_>) {
    let Some(kind) = Kind::from_id(event.kind) else {
        return;
    };
    let Some(handle) = host.entity(event.entity) else {
        return;
    };
    let _ = host.entity_set_attribute_base(handle, "minecraft:spawn_reinforcements", 0.0);
    let mut nbt = Compound::new();
    nbt.insert("IsBaby".into(), Tag::Byte(0));
    nbt.insert("CanPickUpLoot".into(), Tag::Byte(0));
    nbt.insert("CanBreakDoors".into(), Tag::Byte(0));
    let _ = host.entity_merge_nbt(handle, nbt);
    let _ = kind;
}

/// Our bosses never turn into another mob: the zombie template would become a
/// drowned underwater.
pub fn living_conversion_pre(event: &mut LivingConversionPreEvent<'_>) -> Flow {
    if Kind::from_id(event.kind).is_some() {
        Flow::Cancel
    } else {
        Flow::Continue
    }
}

/// The Slider shrugs off projectiles; the Sun Spirit shrugs off fire.
pub fn living_incoming_damage(event: &mut LivingIncomingDamageEvent<'_>) -> Flow {
    let Some(kind) = Kind::from_id(event.kind) else {
        return Flow::Continue;
    };
    if (kind.arrow_proof() && is_projectile(event.damage_type))
        || (kind.fire_proof() && is_fire(event.damage_type))
    {
        return Flow::Cancel;
    }
    Flow::Continue
}

/// `#minecraft:is_projectile`, vanilla 26.3.
fn is_projectile(damage_type: &str) -> bool {
    matches!(
        damage_type,
        "minecraft:arrow"
            | "minecraft:trident"
            | "minecraft:mob_projectile"
            | "minecraft:unattributed_fireball"
            | "minecraft:fireball"
            | "minecraft:wither_skull"
            | "minecraft:thrown"
            | "minecraft:wind_charge"
            | "minecraft:spit"
    )
}

/// `#minecraft:is_fire`, vanilla 26.3.
fn is_fire(damage_type: &str) -> bool {
    matches!(
        damage_type,
        "minecraft:in_fire"
            | "minecraft:on_fire"
            | "minecraft:lava"
            | "minecraft:hot_floor"
            | "minecraft:campfire"
            | "minecraft:fireball"
            | "minecraft:unattributed_fireball"
    )
}

/// Nothing to forget on death: this half keeps no per-mob state.
pub fn living_death(_event: &mut LivingDeathEvent<'_>) -> Flow {
    Flow::Continue
}

pub fn entity_leave_level(_entity: u32, _kind: &str) {}

pub fn clear() {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn damage_type_sets() {
        assert!(is_projectile("minecraft:arrow"));
        assert!(!is_projectile("minecraft:player_attack"));
        assert!(is_fire("minecraft:lava"));
        assert!(!is_fire("minecraft:fall"));
    }

    #[test]
    fn only_the_slider_spares_arrows() {
        assert!(Kind::Slider.arrow_proof() && is_projectile("minecraft:arrow"));
        assert!(!Kind::SunSpirit.arrow_proof());
    }
}
