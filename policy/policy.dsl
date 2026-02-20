# Boreal Safety Policy v1.1
# intent 5 = STOP | intent 2 = APPROACH | intent 3 = TURN_LEFT

IF intent == 5 AND conf >= 0
ACT 1 1

IF intent == 2 AND conf >= 20000
REQUIRE_PREV 1
ACT 2 30

IF intent == 3 AND conf >= 15000
ACT 3 -15

DEFAULT DENY
