//! The three bosses of this slice and the numbers both halves share, taken
//! from their public behaviour descriptions (Aether wiki, boss pages).
//!
//! Part of the clean-room Horizon port of the Aether; original code.

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Kind {
    /// The Slider: a stone-and-iron cube that charges and hits hard.
    Slider,
    /// The Valkyrie Queen: a fast duellist with a lance.
    ValkyrieQueen,
    /// The Sun Spirit: a burning spirit.
    SunSpirit,
}

impl Kind {
    pub fn from_id(id: &str) -> Option<Self> {
        match id {
            "aether:slider" => Some(Kind::Slider),
            "aether:valkyrie_queen" => Some(Kind::ValkyrieQueen),
            "aether:sun_spirit" => Some(Kind::SunSpirit),
            _ => None,
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            Kind::Slider => "slider",
            Kind::ValkyrieQueen => "valkyrie_queen",
            Kind::SunSpirit => "sun_spirit",
        }
    }

    /// Width, height and eye height. The Slider fills its whole room; the
    /// others are human-sized, the Sun Spirit a little taller.
    pub fn size(self) -> (f64, f64, f64) {
        match self {
            Kind::Slider => (1.6, 1.6, 1.6 * 0.85),
            Kind::ValkyrieQueen => (0.6, 2.0, 1.7),
            Kind::SunSpirit => (0.7, 2.3, 2.1),
        }
    }

    /// How far a blow lands: `(width * 2)^2` plus a player-wide target, the
    /// same reach rule vanilla's melee goals use.
    pub fn reach_sqr(self) -> f64 {
        let w = self.size().0;
        (w * 2.0) * (w * 2.0) + 0.6
    }

    /// Ticks between two blows. The Slider swings slowly, the Queen fast.
    pub fn attack_cooldown(self) -> i32 {
        match self {
            Kind::Slider => 40,
            Kind::ValkyrieQueen => 14,
            Kind::SunSpirit => 20,
        }
    }

    /// Walk speed while chasing.
    pub fn chase_speed(self) -> f64 {
        match self {
            Kind::Slider => 0.9,
            Kind::ValkyrieQueen => 1.4,
            Kind::SunSpirit => 1.1,
        }
    }

    /// Random stroll speed.
    pub fn stroll_speed(self) -> f64 {
        match self {
            Kind::Slider => 0.6,
            Kind::ValkyrieQueen => 1.0,
            Kind::SunSpirit => 0.9,
        }
    }

    /// The Slider is made of stone and iron: arrows bounce off it.
    pub fn arrow_proof(self) -> bool {
        self == Kind::Slider
    }

    /// The Sun Spirit lives in fire and takes no damage from it.
    pub fn fire_proof(self) -> bool {
        self == Kind::SunSpirit
    }

    /// It is a spirit of the sun: daylight does not burn it. The Slider is
    /// stone and does not burn either.
    pub fn burns_in_daylight(self) -> bool {
        self == Kind::ValkyrieQueen
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ids_round_trip() {
        for kind in [Kind::Slider, Kind::ValkyrieQueen, Kind::SunSpirit] {
            assert_eq!(Kind::from_id(&format!("aether:{}", kind.name())), Some(kind));
        }
        assert_eq!(Kind::from_id("minecraft:zombie"), None);
    }

    #[test]
    fn slider_reach_is_wide() {
        // 1.6 * 2 = 3.2, squared, plus 0.6.
        assert!((Kind::Slider.reach_sqr() - (3.2 * 3.2 + 0.6)).abs() < 1.0e-9);
        assert!(Kind::Slider.reach_sqr() > Kind::ValkyrieQueen.reach_sqr());
    }

    #[test]
    fn immunities_follow_the_boss() {
        assert!(Kind::Slider.arrow_proof());
        assert!(!Kind::ValkyrieQueen.arrow_proof());
        assert!(Kind::SunSpirit.fire_proof());
        assert!(!Kind::ValkyrieQueen.fire_proof());
        assert!(!Kind::SunSpirit.burns_in_daylight());
        assert!(Kind::ValkyrieQueen.burns_in_daylight());
    }
}
