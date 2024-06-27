import numpy as np
from bot.debug import Debug, DebugTopic
from bot.wall_manager import WallManager
from sc2.bot_ai import BotAI, Race
from sc2.data import Result


from bot.economy_manager import EconomyManager  
from bot.military_manager import   MilitaryManager
from bot.opponent_predictor import OpponentPredictor
from bot.build_order import Builds

from bot.enums.game_focus import Focus
from bot.game_plan import GamePlan
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units


debug: Debug
class SiliConscriptBot(BotAI):
    NAME: str = "SiliConscript"
    """This bot's name"""

    RACE: Race = Race.Terran
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.
        Race.Random
    """

    def __init__(self) -> None:
        super().__init__()
        self.WORKER_MAX = 80
        self.test_marine: Unit = None
        self.test_depot: Unit = None


    async def on_before_start(self):

        """
        Override this in your bot class. This function is called before "on_start"
        and before "prepare_first_step" that calculates expansion locations.
        Not all data is available yet.
        This function is useful in realtime=True mode to split your workers or start producing the first worker.
        """
        global debug
        debug = Debug(self)
        Builds.set_bot_ai(self)
        Builds.set_bot_ai(self)
        self.test_marine: Unit = None
        self.test_depot: Unit = None

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

        self.opponent_predictor = OpponentPredictor(self)

        self.wall_manager = WallManager(self)
        self.wall_manager.add_wall(None, None, self.main_base_ramp)
        self.game_plan = GamePlan(Focus.BALANCED)
        self.economy_manager = EconomyManager(self, self.game_plan, self.wall_manager)
        self.military_manager = MilitaryManager(self)

        # debug.enable_topic(DebugTopic.UNIT_PERSISTANCE_TEST)
        debug.enable_topic(DebugTopic.BALANCE)

        


    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """

        if (self.opponent_predictor.appraise_army()):
            pass
        await self.economy_manager.operate()
        await self.military_manager.operate()

        self.wall_manager.perform_border_patrol()

        # Draw ramp points
        # self.draw_ramp_points()

        self.draw_unit_hightlights(self.economy_manager.wall_manager.structures)

        # Draw all detected expansions on the map
        # self.draw_expansions()

        # # Draw pathing grid
        # self.draw_pathing_grid()

        # Draw placement  grid
        # self.draw_placement_grid()

        # Draw vision blockers
        # self.draw_vision_blockers()

        # Draw visibility pixelmap for debugging purposes
        # self.draw_visibility_pixelmap()

        # Draw some example boxes around units, lines towards command center, text on the screen and barracks
        self.draw_example()

        debug.draw_text()

        self.test_code()

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")


    async def on_unit_destroyed(self, unit_tag: int):
        """
        Override this in your bot class.
        Note that this function uses unit tags and not the unit objects
        because the unit does not exist any more.
        This will event will be called when a unit (or structure, friendly or enemy) dies.
        For enemy units, this only works if the enemy unit was in vision on death.

        :param unit_tag:
        """
        self.wall_manager.handle_structure_detroyed(unit_tag)

    async def on_unit_created(self, unit: Unit):
        """Override this in your bot class. This function is called when a unit is created.

        :param unit:"""

    async def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        """Override this in your bot class. This function is called when a unit type has changed. To get the current UnitTypeId of the unit, use 'unit.type_id'

        This may happen when a larva morphed to an egg, siege tank sieged, a zerg unit burrowed, a hatchery morphed to lair,
        a corruptor morphed to broodlordcocoon, etc..

        Examples::

            print(f"My unit changed type: {unit} from {previous_type} to {unit.type_id}")

        :param unit:
        :param previous_type:
        """

    async def on_building_construction_started(self, unit: Unit):
        """
        Override this in your bot class.
        This function is called when a building construction has started.

        :param unit:
        """
        print(f"building started: {unit}")
        
        self.economy_manager.notify_construction_started(unit)

    async def on_building_construction_complete(self, unit: Unit):
        """
        Override this in your bot class. This function is called when a building
        construction is completed.

        :param unit:
        """
        print(f"building complete: {unit}")
        # Assign CCs to economy manager
         

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        """
        Override this in your bot class. This function is called with the upgrade id of an upgrade that was not finished last step and is now.

        :param upgrade:
        """

    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float):
        """
        Override this in your bot class. This function is called when your own unit (unit or structure) took damage.
        It will not be called if the unit died this frame.

        This may be called frequently for terran structures that are burning down, or zerg buildings that are off creep,
        or terran bio units that just used stimpack ability.
        TODO: If there is a demand for it, then I can add a similar event for when enemy units took damage

        Examples::

            print(f"My unit took damage: {unit} took {amount_damage_taken} damage")

        :param unit:
        """

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        """
        Override this in your bot class. This function is called when an enemy unit (unit or structure) entered vision (which was not visible last frame).

        :param unit:
        """

    async def on_enemy_unit_left_vision(self, unit_tag: int):
        """
        Override this in your bot class. This function is called when an enemy unit (unit or structure) left vision (which was visible last frame).
        Same as the self.on_unit_destroyed event, this function is called with the unit's tag because the unit is no longer visible anymore.
        If you want to store a snapshot of the unit, use self._enemy_units_previous_map[unit_tag] for units or self._enemy_structures_previous_map[unit_tag] for structures.

        Examples::

            last_known_unit = self._enemy_units_previous_map.get(unit_tag, None) or self._enemy_structures_previous_map[unit_tag]
            print(f"Enemy unit left vision, last known location: {last_known_unit.position}")

        :param unit_tag:
        """

        
    def draw_ramp_points(self):
        for ramp in self.game_info.map_ramps:
            for p in ramp.points:
                h2 = self.get_terrain_z_height(p)
                pos = Point3((p.x, p.y, h2))
                color = Point3((185, 66, 218))
                if p in ramp.upper:
                    color = Point3((60, 112, 214))
                if p in ramp.upper2_for_ramp_wall:
                    color = Point3((0, 0, 255))
                if p in ramp.lower:
                    color = Point3((93, 226, 231))
                self.client.debug_box2_out(pos + Point2((0.5, 0.5)), half_vertex_length=0.25, color=color)
                # Identical to above:
                # p0 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z + 0.25))
                # p1 = Point3((pos.x + 0.75, pos.y + 0.75, pos.z - 0.25))
                # logger.info(f"Drawing {p0} to {p1}")
                # self.client.debug_box_out(p0, p1, color=color)

    def draw_expansions(self):
        green = Point3((0, 255, 0))
        for expansion_pos in self.expansion_locations_list:
            height = self.get_terrain_z_height(expansion_pos)
            expansion_pos3 = Point3((*expansion_pos, height))
            self.client.debug_box2_out(expansion_pos3, half_vertex_length=2.5, color=green)

    def draw_pathing_grid(self):
        map_area = self.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.game_info.pathing_grid.data_numpy):
            if value == 0:
                continue
            # Skip values outside of playable map area
            if not map_area.x <= a < map_area.x + map_area.width:
                continue
            if not map_area.y <= b < map_area.y + map_area.height:
                continue
            p = Point2((a, b))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.15, pos.y - 0.15, pos.z + 0.15)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.15, pos.y + 0.15, pos.z - 0.15)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((0, 0, 200))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_placement_grid(self):
        map_area = self.game_info.playable_area
        for (b, a), value in np.ndenumerate(self.game_info.placement_grid.data_numpy):
            if value == 0:
                continue
            # Skip values outside of playable map area
            if not map_area.x <= a < map_area.x + map_area.width:
                continue
            if not map_area.y <= b < map_area.y + map_area.height:
                continue
            p = Point2((a, b))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((0, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_vision_blockers(self):
        for p in self.game_info.vision_blockers:
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # logger.info(f"Drawing {p0} to {p1}")
            color = Point3((255, 0, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_visibility_pixelmap(self):
        for (y, x), value in np.ndenumerate(self.state.visibility.data_numpy):
            p = Point2((x, y))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            p0 = Point3((pos.x - 0.25, pos.y - 0.25, pos.z + 0.25)) + Point2((0.5, 0.5))
            p1 = Point3((pos.x + 0.25, pos.y + 0.25, pos.z - 0.25)) + Point2((0.5, 0.5))
            # Red
            color = Point3((255, 0, 0))
            # If value == 2: show green (= we have vision on that point)
            if value == 2:
                color = Point3((0, 255, 0))
            self.client.debug_box_out(p0, p1, color=color)

    def draw_example(self):
        # Draw green boxes around SCVs if they are gathering, yellow if they are returning cargo, red the rest
        scv: Unit
        for scv in self.workers:
            pos = scv.position3d
            # Red
            color = Point3((255, 0, 0))
            if scv.is_gathering:
                color = Point3((0, 255, 0))
            elif scv.is_returning:
                color = Point3((255, 255, 0))
            self.client.debug_sphere_out(pos, 0.5, color=color)

        # Draw lines from structures to command center
        if self.townhalls:
            cc: Unit = self.economy_manager.expansion_townhalls[0]
            p0: Point3 = cc.position3d
            if not self.structures:
                return
            structure: Unit
            for structure in self.structures:
                # if structure == cc:
                #     continue
                # p1 = structure.position3d
                # # Red
                # color = Point3((255, 0, 0))
                # self.client.debug_line_out(p0, p1, color=color)

                # Draw text on barracks
                if structure.type_id == UnitTypeId.BARRACKS:
                    # Blue
                    color = Point3((0, 0, 255))
                    pos = structure.position3d + Point3((0, 0, 0.5))
                    self.client.debug_text_world(text="MY RAX", pos=pos, color=color, size=16)

        # Draw text in top left of screen
        self.client.debug_text_screen(text="Hello world!", pos=Point2((0, 0.4)), color=None, size=16)
        self.client.debug_text_simple(text="Hello world2!")
    
    def draw_unit_hightlights(self, units: Units):
        for unit in units:
            size = 0.5
            if unit.is_structure:
                size = 1.5
            pos = unit.position3d + Point3((0,0,size/2))
            #  Medium Violet Red
            color = Point3((136, 14, 79))
            self.client.debug_sphere_out(pos, size, color=color)

    def test_code(self):
        if self.test_marine == None:
            marines = self.units.of_type(UnitTypeId.MARINE)
            if marines.amount > 0:
                self.test_marine = marines.first
                debug.log_cond(f"Test Marine Created!\nTag Id: {self.test_marine.tag} Unit: {self.test_marine}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)
        else:
            pos = self.test_marine.position3d
            # teal
            color = Point3((77, 208, 225))
            self.client.debug_sphere_out(pos, 0.5, color=color)
            debug.log_cond(f"Test Marine Tag Id: {self.test_marine.tag} Unit: {self.test_marine}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)
            
            marine = self.units.find_by_tag(self.test_marine.tag)

            if marine != None:
                pos = marine.position3d
                # lime
                color = Point3((129, 199, 132))
                self.client.debug_sphere_out(pos, 0.5, color=color)
                debug.log_cond(f"Bot derived Marine Tag Id: {marine.tag} Unit: {marine}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)

        if self.test_depot == None:
            depots = self.structures.of_type(UnitTypeId.SUPPLYDEPOT)
            if depots.amount > 0:
                self.test_depot = depots.first
                debug.log_cond(f"Test Depot Created!\nTag Id: {self.test_depot.tag} Unit: {self.test_depot}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)
        else:
            pos = self.test_depot.position3d
            # teal
            color = Point3((77, 208, 225))
            self.client.debug_sphere_out(pos, 0.5, color=color)
            debug.log_cond(f"Test Depot Tag Id: {self.test_depot.tag} Unit: {self.test_depot}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)
            
            depot = self.structures.find_by_tag(self.test_depot.tag)

            if depot != None:
                pos = depot.position3d
                # lime
                color = Point3((129, 199, 132))
                self.client.debug_sphere_out(pos, 1.5, color=color)
                debug.log_cond(f"Bot derived Depot Tag Id: {depot.tag} Unit: {depot}", topic=DebugTopic.UNIT_PERSISTANCE_TEST)