from pysc2.agents import base_agent
from pysc2.env import sc2_env
from pysc2.lib import actions, features, units
from absl import app
import random

class ProtossAgent(base_agent.BaseAgent):

    def __init__(self):
        super(ProtossAgent, self).__init__()
        self.attack_coordinates= None

    def unit_type_is_selected(self, obs, unit_type):
        if (len(obs.observation.single_select) > 0 and obs.observation.single_select[0].unit_type == unit_type):
            return True

        if (len(obs.observation.multi_select) > 0 and obs.observation.multi_select[0].unit_type == unit_type):
            return True

        return False

    def get_units_by_type(self, obs, unit_type):
        return [unit for unit in obs.observation.feature_units if unit.unit_type == unit_type]

    def can_do(self, obs, action):
        return action in obs.observation.available_actions

    def build_assimilator(self, obs):
        neutral_vespene_geysers = self.get_units_by_type(obs, units.Neutral.VespeneGeyser)
        assimilators = self.get_units_by_type(obs, units.Protoss.Assimilator)

        if len(assimilators) < 1 and len(neutral_vespene_geysers) > 0:
            if self.unit_type_is_selected(obs, units.Protoss.Probe):
                geyser = random.choice(neutral_vespene_geysers)
                return actions.FUNCTIONS.Build_Assimilator_screen("now", (geyser.x, geyser.y))

            probes = self.get_units_by_type(obs, units.Protoss.Probe)

            if len(probes) > 0:
                probes = random.choice(probes)
                return actions.FUNCTIONS.select_point("select_all_type", (probes.x, probes.y))

    def gather_vespene_gas(self, obs):
        assimilator = self.get_units_by_type(obs, units.Protoss.Assimilator)
        if len(assimilator) > 0:
            assimilator = random.choice(assimilator)
            if assimilator['assigned_harvesters'] < 3:
                if self.unit_type_is_selected(obs, units.Protoss.Probe):
                    if len(obs.observation.single_select) < 2 and len(obs.observation.multi_select) < 2:
                        if self.can_do(obs, actions.FUNCTIONS.Harvest_Gather_screen.id):
                            return actions.FUNCTIONS.Harvest_Gather_screen("now", (assimilator.x, assimilator.y))


                probes = self.get_units_by_type(obs, units.Protoss.Probe)
                if len(probes) > 0:
                    probe = random.choice(probes)
                    return actions.FUNCTIONS.select_point("select", (probe.x, probe.y))

    def step(self, obs):
        super(ProtossAgent, self).step(obs)

        if obs.first():
            #Self Position
            player_y, player_x = (obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()

            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16) #X, Y

        minerals = obs.observation.player.minerals
        vespene = obs.observation.player.vespene

        #Create Pylon in every oportunity (4 total)
        Pylon = self.get_units_by_type(obs, units.Protoss.Pylon)
        if len(Pylon) < 4 and minerals >= 100:
            if self.can_do(obs, actions.FUNCTIONS.Build_Pylon_screen.id):
                x = random.randint(0, 83)
                y = random.randint(0, 83)
                return actions.FUNCTIONS.Build_Pylon_screen("now", (x, y))

        #Create gateway every oportunity (3 total)
        Gateways = self.get_units_by_type(obs, units.Protoss.Gateway)
        if len(Gateways) < 3 and minerals >= 150:
            if self.unit_type_is_selected(obs, units.Protoss.Probe):
                if self.can_do(obs, actions.FUNCTIONS.Build_Gateway_screen.id):
                    x = random.randint(0,83)
                    y = random.randint(0,83)
                    return actions.FUNCTIONS.Build_Gateway_screen("now", (x,y))

        #Attack - Zealots 
        Zealots = self.get_units_by_type(obs, units.Protoss.Zealot)
        if len(Zealots) >= 10:
            if self.unit_type_is_selected(obs, units.Protoss.Zealot):
                if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.Functions.select_army("select")
        
        #Create Zealots
        if len(Gateways) >= 3:
            if self.unit_type_is_selected(obs, units.Protoss.Gateway):
                Zealots = self.get_units_by_type(obs, units.Protoss.Zealot)
                if len(Zealots) <= 15:
                    if self.can_do(obs, actions.FUNCTIONS.Train_Zealot_quick.id):
                        return actions.FUNCTIONS.Train_Zealot_quick("now")
            b = random.choice(Gateways)
            return actions.FUNCTIONS.select_point("sellect_all_type", (b.x, b.y))

        b_assimilator = self.build_assimilator(obs)
        if b_assimilator:
            return b_assimilator

        # Recolectors
        Recolectors = self.get_units_by_type(obs, units.Protoss.Probe)
        if len(Recolectors) > 0:
            probe = random.choice(Recolectors)
            return actions.FUNCTIONS.select_point("select_all_type", (probe.x, probe.y))

        g_assimilator = self.gather_vespene_gas(obs)
        if g_assimilator:
            return g_assimilator

        return actions.FUNCTIONS.no_op()
        
def main(unused_argv):
    agent = ProtossAgent()
    try:
        while True:
            with sc2_env.SC2Env(
                map_name="Simple64",
                players=[sc2_env.Agent(sc2_env.Race.protoss),
                         sc2_env.Bot(sc2_env.Race.random, sc2_env.Difficulty.very_easy)],
                agent_interface_format= features.AgentInterfaceFormat(
                    feature_dimensions= features.Dimensions(screen=84, minimap=64),
                    use_feature_units= True
                ),
                step_mul= 16,
                game_steps_per_episode= 0,
                visualize= True
            ) as env:

                agent.setup(env.observation_spec(), env.action_spec())
                timesteps= env.reset()
                agent.reset()

                while True:
                    step_actions=[agent.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps= env.step(step_actions)
    
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    app.run(main)