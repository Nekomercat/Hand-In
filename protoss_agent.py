from pysc2 import agents
from pysc2.agents import base_agent
from pysc2.env import sc2_env, run_loop
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
        minerals = obs.observation.player.minerals
        neutral_vespene_geysers = self.get_units_by_type(obs, units.Neutral.VespeneGeyser)
        assimilators = self.get_units_by_type(obs, units.Protoss.Assimilator)
        if len(assimilators) < 1 and len(neutral_vespene_geysers) > 0 and minerals >= 75:
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

            #Enemy Position
            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16) #X, Y

        minerals = obs.observation.player.minerals
        vespene = obs.observation.player.vespene

        #Attack - Zealots 
        Zealots = self.get_units_by_type(obs, units.Protoss.Zealot)
        if len(Zealots) >= 10:
            if self.unit_type_is_selected(obs, units.Protoss.Zealot):
                if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)

            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.FUNCTIONS.select_army("select")

        #Create Pylon in every oportunity (4 total)
        Pylons = self.get_units_by_type(obs, units.Protoss.Pylon)
        if len(Pylons) < 3 and minerals >= 100:
            if self.unit_type_is_selected(obs, units.Protoss.Probe):
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
        
        #Create Zealots
        if len(Gateways) >= 3:
            if self.unit_type_is_selected(obs, units.Protoss.Gateway):
                Zealots = self.get_units_by_type(obs, units.Protoss.Zealot)
                if len(Zealots) <= 15:
                    if self.can_do(obs, actions.FUNCTIONS.Train_Zealot_quick.id):
                        return actions.FUNCTIONS.Train_Zealot_quick("now")
            b = random.choice(Gateways)
            return actions.FUNCTIONS.select_point("select_all_type", (b.x, b.y))

        Probes = self.get_units_by_type(obs, units.Protoss.Probe)
        if len(Probes) < 9 and minerals >= 50:
            if self.unit_type_is_selected(obs, units.Protoss.Nexus):
                if self.cand_do(obs, actions.FUNCTIONS.Train_Probe.quick.id):
                    return actions.FUNCTIONS.Train_Probe_quick("now")

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

class TerranAgent(base_agent.BaseAgent):

    def init(self):
        super(TerranAgent, self).init()
        self.attack_coordinates = None

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

    def build_refinery(self, obs):
        neutral_vespene_geysers = self.get_units_by_type(obs, units.Neutral.VespeneGeyser)
        refineries = self.get_units_by_type(obs, units.Terran.Refinery)

        if len(refineries) < 1 and len(neutral_vespene_geysers) > 0:
            if self.unit_type_is_selected(obs, units.Terran.SCV):
                if self.can_do(obs, actions.FUNCTIONS.Build_Refinery_screen.id):
                    geyser = random.choice(neutral_vespene_geysers)
                    return actions.FUNCTIONS.Build_Refinery_screen("now", (geyser.x, geyser.y))

            scvs = self.get_units_by_type(obs, units.Terran.SCV)

            if len(scvs) > 0:
                scv = random.choice(scvs)
                return actions.FUNCTIONS.select_point("select_all_type", (scv.x, scv.y))

    def gather_vespene_gas(self,obs):
        refinery = self.get_units_by_type(obs, units.Terran.Refinery)
        if len(refinery) > 0:
            refinery = random.choice(refinery)
            if refinery['assigned_harvesters'] < 3:
                if self.unit_type_is_selected(obs, units.Terran.SCV):
                    if len(obs.observation.single_select) < 2 and len(obs.observation.multi_select) < 2 :
                        if self.can_do(obs,actions.FUNCTIONS.Harvest_Gather_screen.id):
                            return actions.FUNCTIONS.Harvest_Gather_screen("now",(refinery.x, refinery.y))


                scvs = self.get_units_by_type(obs, units.Terran.SCV)
                if len(scvs) > 0 :
                    scv = random.choice(scvs)
                    return actions.FUNCTIONS.select_point("select",(scv.x,scv.y))


    def step(self, obs):
        super(TerranAgent, self).step(obs)

        if obs.first():
            # CHECK SELF POSITION
            player_y, player_x = (obs.observation.feature_minimap.player_relative == features.PlayerRelative.SELF).nonzero()
            xmean = player_x.mean()
            ymean = player_y.mean()

            # CHECK ENEMY POSITION
            if xmean <= 31 and ymean <= 31:
                self.attack_coordinates = (49, 49)
            else:
                self.attack_coordinates = (12, 16)


        minerals = obs.observation.player.minerals

        # CREATE SUPPLY DEPOTS IN EVERY OPPORTUNITY (TO HAVE 3 IN TOTAL)
        SupplyDepot = self.get_units_by_type(obs, units.Terran.SupplyDepot)
        if len(SupplyDepot) < 3 and minerals >= 100:
            if self.unit_type_is_selected(obs, units.Terran.SCV):
                if self.can_do(obs, actions.FUNCTIONS.Build_SupplyDepot_screen.id):
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)
                    return actions.FUNCTIONS.Build_SupplyDepot_screen("now", (x, y))

        # CREATE BARRACKS IN EVERY OPPORTUNITY (TO HAVE 3 IN TOTAL)
        Barracks = self.get_units_by_type(obs, units.Terran.Barracks)
        if len(Barracks) < 3 and minerals >= 150:
            if self.unit_type_is_selected(obs, units.Terran.SCV):
                if self.can_do(obs, actions.FUNCTIONS.Build_Barracks_screen.id):
                    x = random.randint(0, 83)
                    y = random.randint(0, 83)
                    return actions.FUNCTIONS.Build_Barracks_screen("now", (x, y))

        # ATTACK - MARINES (15 GROUP)
        Marines = self.get_units_by_type(obs, units.Terran.Marine)
        if len(Marines) >= 10:
            if self.unit_type_is_selected(obs, units.Terran.Marine):
                if self.can_do(obs, actions.FUNCTIONS.Attack_minimap.id):
                    return actions.FUNCTIONS.Attack_minimap("now", self.attack_coordinates)
            if self.can_do(obs, actions.FUNCTIONS.select_army.id):
                return actions.FUNCTIONS.select_army("select")


        # CREATE MARINES
        if len(Barracks) >= 3:
            if self.unit_type_is_selected(obs, units.Terran.Barracks):
                Marines = self.get_units_by_type(obs, units.Terran.Marine)
                if len(Marines) <= 15:
                    if self.can_do(obs, actions.FUNCTIONS.Train_Marine_quick.id):
                        return actions.FUNCTIONS.Train_Marine_quick("now")
            b = random.choice(Barracks)
            return actions.FUNCTIONS.select_point("select_all_type", (b.x, b.y))

        b_refinery = self.build_refinery(obs)
        if b_refinery:
            return b_refinery

        # RECOLECTORS
        Recolectors = self.get_units_by_type(obs, units.Terran.SCV)
        if len(Recolectors) > 0:
            scv = random.choice(Recolectors)
            return actions.FUNCTIONS.select_point("select_all_type", (scv.x, scv.y))

        g_refinery = self.gather_vespene_gas(obs)
        if g_refinery:
            return g_refinery

        return actions.FUNCTIONS.no_op()
        
def main(unused_argv):
    agentProtoss = ProtossAgent()
    agentTerran = TerranAgent()
    try:
        while True:
            with sc2_env.SC2Env(
                map_name="Simple64",
                players=[sc2_env.Agent(sc2_env.Race.protoss),
                         sc2_env.Agent(sc2_env.Race.terran)],
                agent_interface_format= features.AgentInterfaceFormat(
                    feature_dimensions= features.Dimensions(screen=84, minimap=64),
                    use_feature_units= True
                ),
                step_mul= 16,
                game_steps_per_episode= 0,
                visualize= True
            ) as env:
                run_loop.run_loop([agentProtoss,agentTerran], env)
                """
                agentProtoss.setup(env.observation_spec(), env.action_spec())
                timesteps= env.reset()
                agentProtoss.reset()

                agentTerran.setup(env.observation_spec(), env.action_spec())
                timesteps= env.reset()
                agentTerran.reset()

                while True:
                    step_actions=[agentProtoss.step(timesteps[0]), agentTerran.step(timesteps[0])]
                    if timesteps[0].last():
                        break
                    timesteps= env.step(step_actions)    
                """
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    app.run(main)